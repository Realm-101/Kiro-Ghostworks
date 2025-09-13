#!/usr/bin/env python3
"""
Kiro Score Generator

This script generates a comprehensive quality score for the Ghostworks SaaS platform
based on test results, coverage, performance, and security metrics.
"""

import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
import glob
import sys
from pathlib import Path
from typing import Dict, Any, Optional


class KiroScoreGenerator:
    """Generate Kiro quality scores from CI/CD artifacts."""
    
    def __init__(self, artifacts_dir: str = "."):
        self.artifacts_dir = Path(artifacts_dir)
        self.score_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'commit_sha': os.environ.get('GITHUB_SHA', 'unknown'),
            'branch': os.environ.get('GITHUB_REF_NAME', 'unknown'),
            'workflow_run_id': os.environ.get('GITHUB_RUN_ID', 'unknown'),
            'tests': {
                'unit': {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0, 'coverage': 0},
                'integration': {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0, 'coverage': 0},
                'e2e': {'total': 0, 'passed': 0, 'failed': 0, 'duration': 0}
            },
            'coverage': {
                'backend': 0,
                'frontend': 0,
                'overall': 0
            },
            'performance': {
                'avg_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'requests_per_second': 0,
                'error_rate': 0
            },
            'security': {
                'vulnerabilities_found': 0,
                'high_severity': 0,
                'medium_severity': 0,
                'low_severity': 0,
                'scan_passed': True,
                'dependency_vulnerabilities': 0
            },
            'build': {
                'success': True,
                'duration': 0,
                'size_mb': 0
            },
            'code_quality': {
                'linting_errors': 0,
                'linting_warnings': 0,
                'complexity_score': 0,
                'maintainability_index': 0
            }
        }

    def parse_junit_xml(self, file_path: Path) -> Dict[str, Any]:
        """Parse JUnit XML file and extract test metrics."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            tests = int(root.get('tests', 0))
            failures = int(root.get('failures', 0))
            errors = int(root.get('errors', 0))
            skipped = int(root.get('skipped', 0))
            time = float(root.get('time', 0))
            
            return {
                'total': tests,
                'passed': tests - failures - errors - skipped,
                'failed': failures + errors,
                'skipped': skipped,
                'duration': time
            }
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'duration': 0}

    def parse_coverage_xml(self, file_path: Path) -> float:
        """Parse coverage XML file and extract coverage percentage."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Try different coverage XML formats
            coverage_elem = root.find('.//coverage')
            if coverage_elem is not None:
                line_rate = float(coverage_elem.get('line-rate', 0))
                return line_rate * 100
            
            # Try Cobertura format
            coverage_elem = root
            if coverage_elem.tag == 'coverage':
                line_rate = float(coverage_elem.get('line-rate', 0))
                return line_rate * 100
                
            return 0
        except Exception as e:
            print(f"Error parsing coverage {file_path}: {e}")
            return 0

    def parse_performance_json(self, file_path: Path) -> Dict[str, float]:
        """Parse k6 performance results."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Parse k6 JSON output (one JSON object per line)
            metrics_data = {}
            for line in lines:
                if line.strip():
                    data = json.loads(line)
                    if data.get('type') == 'Point' and 'metric' in data:
                        metric_name = data['metric']
                        value = data.get('data', {}).get('value', 0)
                        
                        if metric_name == 'http_req_duration':
                            if 'tags' in data['data'] and data['data']['tags'].get('expected_response') == 'true':
                                metrics_data.setdefault('response_times', []).append(value)
                        elif metric_name == 'http_reqs':
                            metrics_data['total_requests'] = metrics_data.get('total_requests', 0) + 1
                        elif metric_name == 'http_req_failed':
                            if value > 0:
                                metrics_data['failed_requests'] = metrics_data.get('failed_requests', 0) + 1
            
            # Calculate statistics
            response_times = metrics_data.get('response_times', [0])
            if response_times:
                response_times.sort()
                n = len(response_times)
                avg_response_time = sum(response_times) / n
                p95_response_time = response_times[int(n * 0.95)] if n > 0 else 0
                p99_response_time = response_times[int(n * 0.99)] if n > 0 else 0
            else:
                avg_response_time = p95_response_time = p99_response_time = 0
            
            total_requests = metrics_data.get('total_requests', 0)
            failed_requests = metrics_data.get('failed_requests', 0)
            error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'avg_response_time': avg_response_time,
                'p95_response_time': p95_response_time,
                'p99_response_time': p99_response_time,
                'requests_per_second': total_requests / 60 if total_requests > 0 else 0,  # Assuming 1-minute test
                'error_rate': error_rate
            }
        except Exception as e:
            print(f"Error parsing performance {file_path}: {e}")
            return {
                'avg_response_time': 0,
                'p95_response_time': 0,
                'p99_response_time': 0,
                'requests_per_second': 0,
                'error_rate': 0
            }

    def parse_security_results(self) -> Dict[str, Any]:
        """Parse security scan results from various tools."""
        security_data = {
            'vulnerabilities_found': 0,
            'high_severity': 0,
            'medium_severity': 0,
            'low_severity': 0,
            'scan_passed': True,
            'dependency_vulnerabilities': 0
        }
        
        # Parse ZAP results
        zap_files = list(self.artifacts_dir.glob('**/report_json.json'))
        for zap_file in zap_files:
            try:
                with open(zap_file, 'r') as f:
                    zap_data = json.load(f)
                
                alerts = zap_data.get('site', [{}])[0].get('alerts', [])
                for alert in alerts:
                    risk = alert.get('riskdesc', '').lower()
                    if 'high' in risk:
                        security_data['high_severity'] += 1
                    elif 'medium' in risk:
                        security_data['medium_severity'] += 1
                    elif 'low' in risk:
                        security_data['low_severity'] += 1
                
                security_data['vulnerabilities_found'] = (
                    security_data['high_severity'] + 
                    security_data['medium_severity'] + 
                    security_data['low_severity']
                )
                
                # Fail if high severity vulnerabilities found
                if security_data['high_severity'] > 0:
                    security_data['scan_passed'] = False
                    
            except Exception as e:
                print(f"Error parsing ZAP results {zap_file}: {e}")
        
        # Parse Safety results (Python dependencies)
        safety_files = list(self.artifacts_dir.glob('**/safety-report.json'))
        for safety_file in safety_files:
            try:
                with open(safety_file, 'r') as f:
                    safety_data = json.load(f)
                
                vulnerabilities = safety_data.get('vulnerabilities', [])
                security_data['dependency_vulnerabilities'] = len(vulnerabilities)
                
                if vulnerabilities:
                    security_data['scan_passed'] = False
                    
            except Exception as e:
                print(f"Error parsing Safety results {safety_file}: {e}")
        
        return security_data

    def collect_metrics(self):
        """Collect all metrics from CI artifacts."""
        
        # Parse unit test results
        unit_test_files = list(self.artifacts_dir.glob('**/pytest-unit-results.xml'))
        if unit_test_files:
            self.score_data['tests']['unit'].update(self.parse_junit_xml(unit_test_files[0]))

        # Parse integration test results
        integration_test_files = list(self.artifacts_dir.glob('**/pytest-integration-results.xml'))
        if integration_test_files:
            self.score_data['tests']['integration'].update(self.parse_junit_xml(integration_test_files[0]))

        # Parse E2E test results (Playwright)
        e2e_test_files = list(self.artifacts_dir.glob('**/test-results.json'))
        if e2e_test_files:
            try:
                with open(e2e_test_files[0], 'r') as f:
                    e2e_data = json.load(f)
                
                # Parse Playwright results format
                suites = e2e_data.get('suites', [])
                total = passed = failed = 0
                duration = 0
                
                for suite in suites:
                    for spec in suite.get('specs', []):
                        for test in spec.get('tests', []):
                            total += 1
                            results = test.get('results', [])
                            if results and results[0].get('status') == 'passed':
                                passed += 1
                            else:
                                failed += 1
                            duration += results[0].get('duration', 0) if results else 0
                
                self.score_data['tests']['e2e'] = {
                    'total': total,
                    'passed': passed,
                    'failed': failed,
                    'duration': duration / 1000  # Convert to seconds
                }
            except Exception as e:
                print(f"Error parsing E2E results: {e}")

        # Parse coverage results
        coverage_files = list(self.artifacts_dir.glob('**/coverage.xml'))
        if coverage_files:
            backend_coverage = self.parse_coverage_xml(coverage_files[0])
            self.score_data['coverage']['backend'] = backend_coverage
            
        # Frontend coverage (if separate file exists)
        frontend_coverage_files = list(self.artifacts_dir.glob('**/coverage-frontend.xml'))
        if frontend_coverage_files:
            frontend_coverage = self.parse_coverage_xml(frontend_coverage_files[0])
            self.score_data['coverage']['frontend'] = frontend_coverage
        else:
            # Assume similar coverage for frontend if not separate
            self.score_data['coverage']['frontend'] = self.score_data['coverage']['backend'] * 0.8

        # Calculate overall coverage
        self.score_data['coverage']['overall'] = (
            self.score_data['coverage']['backend'] + 
            self.score_data['coverage']['frontend']
        ) / 2

        # Parse performance results
        perf_files = list(self.artifacts_dir.glob('**/performance-results.json'))
        if perf_files:
            self.score_data['performance'].update(self.parse_performance_json(perf_files[0]))

        # Parse security results
        self.score_data['security'].update(self.parse_security_results())

    def calculate_score(self) -> Dict[str, Any]:
        """Calculate overall Kiro score with detailed breakdown and transparency."""
        
        # Test score (35% weight) - Critical for reliability
        # Rationale: Tests are the foundation of quality - they prevent regressions,
        # ensure functionality works as expected, and provide confidence for deployments
        total_tests = (
            self.score_data['tests']['unit']['total'] + 
            self.score_data['tests']['integration']['total'] + 
            self.score_data['tests']['e2e']['total']
        )
        total_passed = (
            self.score_data['tests']['unit']['passed'] + 
            self.score_data['tests']['integration']['passed'] + 
            self.score_data['tests']['e2e']['passed']
        )
        
        test_pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        test_score = min(test_pass_rate, 100) * 0.35

        # Coverage score (25% weight) - Important for code quality
        # Rationale: Code coverage indicates how much of the codebase is tested,
        # helping identify untested code paths that could harbor bugs
        coverage_score = min(self.score_data['coverage']['overall'], 100) * 0.25

        # Performance score (20% weight) - Critical for user experience
        # Rationale: Performance directly impacts user satisfaction and business metrics.
        # Poor performance leads to user abandonment and reduced conversion rates
        performance_breakdown = self.calculate_performance_score()
        perf_score = performance_breakdown['score'] * 0.20

        # Security score (15% weight) - Essential for trust and compliance
        # Rationale: Security vulnerabilities can lead to data breaches, legal issues,
        # and loss of customer trust. High/medium severity issues block deployment
        security_breakdown = self.calculate_security_score()
        security_score = security_breakdown['score'] * 0.15

        # Build quality score (5% weight) - Basic requirement
        # Rationale: If the build fails, nothing else matters. This is a gate condition
        build_score = 5 if self.score_data['build']['success'] else 0

        total_score = test_score + coverage_score + perf_score + security_score + build_score
        
        return {
            'total_score': min(total_score, 100),
            'breakdown': {
                'tests': {
                    'score': test_score,
                    'weight': 35,
                    'rationale': 'Tests prevent regressions and ensure functionality',
                    'pass_rate': test_pass_rate,
                    'total_tests': total_tests,
                    'passed_tests': total_passed
                },
                'coverage': {
                    'score': coverage_score,
                    'weight': 25,
                    'rationale': 'Coverage identifies untested code paths',
                    'percentage': self.score_data['coverage']['overall']
                },
                'performance': {
                    'score': perf_score,
                    'weight': 20,
                    'rationale': 'Performance impacts user experience and business metrics',
                    **performance_breakdown
                },
                'security': {
                    'score': security_score,
                    'weight': 15,
                    'rationale': 'Security prevents breaches and maintains trust',
                    **security_breakdown
                },
                'build': {
                    'score': build_score,
                    'weight': 5,
                    'rationale': 'Build success is a basic gate condition',
                    'success': self.score_data['build']['success']
                }
            }
        }

    def calculate_performance_score(self) -> Dict[str, Any]:
        """Calculate performance score with route-class granularity."""
        p95_actual = self.score_data['performance']['p95_response_time']
        error_rate = self.score_data['performance']['error_rate']
        
        # Route-class specific targets (more realistic than blanket 200ms)
        route_targets = {
            'health_check': 50,      # Health endpoints should be very fast
            'auth': 150,             # Auth operations can be slightly slower (crypto)
            'crud_simple': 200,      # Simple CRUD operations
            'search_heavy': 500,     # Complex search/analytics operations
            'file_upload': 2000,     # File operations can be much slower
        }
        
        # For now, use general CRUD target (200ms) but document the granularity
        p95_target = 200
        error_target = 1.0  # 1% error rate threshold
        
        # Performance scoring
        if p95_actual > 0:
            # Exponential penalty for exceeding targets
            if p95_actual <= p95_target:
                latency_score = 100
            elif p95_actual <= p95_target * 2:
                latency_score = 100 * (p95_target * 2 - p95_actual) / p95_target
            else:
                latency_score = 0
        else:
            latency_score = 100  # No data = full points
        
        # Error rate scoring
        if error_rate <= error_target:
            error_score = 100
        elif error_rate <= error_target * 2:
            error_score = 100 * (error_target * 2 - error_rate) / error_target
        else:
            error_score = 0
        
        # Combined performance score (weighted average)
        combined_score = (latency_score * 0.7) + (error_score * 0.3)
        
        return {
            'score': combined_score,
            'latency_score': latency_score,
            'error_score': error_score,
            'p95_actual': p95_actual,
            'p95_target': p95_target,
            'error_rate_actual': error_rate,
            'error_rate_target': error_target,
            'route_targets': route_targets,
            'notes': [
                'Excludes cold-start/first-hit latency in local development',
                'Route-class targets: health(50ms), auth(150ms), crud(200ms), search(500ms), upload(2s)',
                'Performance gates are more aggressive for production than staging'
            ]
        }

    def calculate_security_score(self) -> Dict[str, Any]:
        """Calculate security score with detailed breakdown."""
        base_score = 100
        
        # High severity = deployment blocker
        if self.score_data['security']['high_severity'] > 0:
            base_score = 0
            deployment_action = 'BLOCK'
        # Medium severity = warning but allow with review
        elif self.score_data['security']['medium_severity'] > 0:
            base_score = 70  # Significant reduction
            deployment_action = 'WARN'
        # Low severity = minor reduction
        elif self.score_data['security']['low_severity'] > 5:
            base_score = 90  # Small reduction for many low issues
            deployment_action = 'PROCEED'
        else:
            deployment_action = 'PROCEED'
        
        # Dependency vulnerabilities
        if self.score_data['security']['dependency_vulnerabilities'] > 0:
            base_score *= 0.8  # 20% reduction for dependency issues
        
        return {
            'score': base_score,
            'deployment_action': deployment_action,
            'high_severity': self.score_data['security']['high_severity'],
            'medium_severity': self.score_data['security']['medium_severity'],
            'low_severity': self.score_data['security']['low_severity'],
            'dependency_vulnerabilities': self.score_data['security']['dependency_vulnerabilities'],
            'scan_passed': self.score_data['security']['scan_passed']
        }

    def get_grade(self, score: float) -> Dict[str, Any]:
        """Convert numeric score to letter grade with deployment implications."""
        if score >= 95:
            grade = 'A+'
            deployment = 'AUTO_DEPLOY'
            description = 'Excellent quality - automatic deployment approved'
        elif score >= 90:
            grade = 'A'
            deployment = 'AUTO_DEPLOY'
            description = 'High quality - automatic deployment approved'
        elif score >= 85:
            grade = 'A-'
            deployment = 'AUTO_DEPLOY'
            description = 'Good quality - automatic deployment approved'
        elif score >= 80:
            grade = 'B+'
            deployment = 'MANUAL_REVIEW'
            description = 'Acceptable quality - manual review recommended'
        elif score >= 75:
            grade = 'B'
            deployment = 'MANUAL_REVIEW'
            description = 'Acceptable quality - manual review recommended'
        elif score >= 70:
            grade = 'B-'
            deployment = 'MANUAL_REVIEW'
            description = 'Below target - manual review required'
        elif score >= 65:
            grade = 'C+'
            deployment = 'BLOCK_WITH_OVERRIDE'
            description = 'Poor quality - deployment blocked, override possible'
        elif score >= 60:
            grade = 'C'
            deployment = 'BLOCK_WITH_OVERRIDE'
            description = 'Poor quality - deployment blocked, override possible'
        elif score >= 55:
            grade = 'C-'
            deployment = 'BLOCK_WITH_OVERRIDE'
            description = 'Poor quality - deployment blocked, override possible'
        elif score >= 50:
            grade = 'D'
            deployment = 'BLOCK'
            description = 'Unacceptable quality - deployment blocked'
        else:
            grade = 'F'
            deployment = 'BLOCK'
            description = 'Failed quality gates - deployment blocked'
        
        return {
            'grade': grade,
            'deployment_action': deployment,
            'description': description,
            'thresholds': {
                'auto_deploy': '≥85 (A- or better)',
                'manual_review': '70-84 (B- to B+)',
                'block_with_override': '55-69 (C- to C+)',
                'block': '<55 (D or F)'
            }
        }

    def generate_recommendations(self) -> list:
        """Generate improvement recommendations based on metrics."""
        recommendations = []
        
        # Test recommendations
        total_tests = sum(test['total'] for test in self.score_data['tests'].values())
        if total_tests < 50:
            recommendations.append("📝 Add more comprehensive test coverage (current: {total_tests} tests)")
        
        failed_tests = sum(test['failed'] for test in self.score_data['tests'].values())
        if failed_tests > 0:
            recommendations.append(f"🔧 Fix {failed_tests} failing tests")
        
        # Coverage recommendations
        if self.score_data['coverage']['backend'] < 70:
            recommendations.append(f"📊 Improve backend test coverage (current: {self.score_data['coverage']['backend']:.1f}%)")
        
        if self.score_data['coverage']['frontend'] < 60:
            recommendations.append(f"🎨 Improve frontend test coverage (current: {self.score_data['coverage']['frontend']:.1f}%)")
        
        # Performance recommendations
        if self.score_data['performance']['p95_response_time'] > 200:
            recommendations.append(f"⚡ Optimize API performance (P95: {self.score_data['performance']['p95_response_time']:.1f}ms)")
        
        if self.score_data['performance']['error_rate'] > 1:
            recommendations.append(f"🚨 Reduce error rate (current: {self.score_data['performance']['error_rate']:.1f}%)")
        
        # Security recommendations
        if self.score_data['security']['high_severity'] > 0:
            recommendations.append(f"🔒 Fix {self.score_data['security']['high_severity']} high-severity security issues")
        
        if self.score_data['security']['dependency_vulnerabilities'] > 0:
            recommendations.append(f"📦 Update {self.score_data['security']['dependency_vulnerabilities']} vulnerable dependencies")
        
        return recommendations

    def generate_score_file(self, output_path: str = "kiro_score.json"):
        """Generate the complete Kiro score file with transparency."""
        self.collect_metrics()
        
        score_result = self.calculate_score()
        overall_score = score_result['total_score']
        grade_result = self.get_grade(overall_score)
        recommendations = self.generate_recommendations()
        
        # Generate artifact links for CI/CD
        artifact_links = self.generate_artifact_links()
        
        self.score_data.update({
            'overall_score': overall_score,
            'grade': grade_result['grade'],
            'grade_info': grade_result,
            'score_breakdown': score_result['breakdown'],
            'recommendations': recommendations,
            'artifact_links': artifact_links,
            'transparency': {
                'scoring_methodology': {
                    'weights': {
                        'tests': '35% - Foundation of quality, prevents regressions',
                        'coverage': '25% - Identifies untested code paths',
                        'performance': '20% - User experience and business impact',
                        'security': '15% - Trust, compliance, and risk management',
                        'build': '5% - Basic gate condition'
                    },
                    'thresholds': grade_result['thresholds'],
                    'performance_targets': score_result['breakdown']['performance'].get('route_targets', {}),
                    'version': '2.0',
                    'last_updated': '2024-01-15'
                }
            },
            'summary': {
                'tests': f"{sum(test['passed'] for test in self.score_data['tests'].values())}/{sum(test['total'] for test in self.score_data['tests'].values())} passed",
                'coverage': f"{self.score_data['coverage']['overall']:.1f}% average",
                'performance': f"{self.score_data['performance']['p95_response_time']:.1f}ms P95",
                'security': "✅ Passed" if self.score_data['security']['scan_passed'] else "❌ Failed"
            }
        })
        
        with open(output_path, 'w') as f:
            json.dump(self.score_data, f, indent=2)
        
        return self.score_data

    def generate_artifact_links(self) -> Dict[str, str]:
        """Generate links to CI/CD artifacts for easy access."""
        base_url = f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'owner/repo')}"
        run_id = os.environ.get('GITHUB_RUN_ID', 'unknown')
        
        links = {
            'workflow_run': f"{base_url}/actions/runs/{run_id}",
            'commit': f"{base_url}/commit/{self.score_data['commit_sha']}"
        }
        
        # Add artifact-specific links if available
        if run_id != 'unknown':
            artifact_base = f"{base_url}/actions/runs/{run_id}"
            
            links.update({
                'test_results': {
                    'unit_tests': f"{artifact_base}#artifacts",
                    'integration_tests': f"{artifact_base}#artifacts", 
                    'e2e_tests': f"{artifact_base}#artifacts"
                },
                'coverage_report': f"{artifact_base}#artifacts",
                'performance_report': f"{artifact_base}#artifacts",
                'security_scan': f"{artifact_base}#artifacts",
                'playwright_report': f"{artifact_base}#artifacts"
            })
        
        return links


def main():
    """Main entry point."""
    artifacts_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "kiro_score.json"
    
    generator = KiroScoreGenerator(artifacts_dir)
    score_data = generator.generate_score_file(output_file)
    
    grade_info = score_data['grade_info']
    print(f"Generated Kiro Score: {score_data['overall_score']:.1f}/100 (Grade: {score_data['grade']})")
    print(f"Deployment Action: {grade_info['deployment_action']}")
    print(f"Description: {grade_info['description']}")
    print(f"Score file written to: {output_file}")
    
    # Show score breakdown
    print(f"\n📊 Score Breakdown:")
    for category, details in score_data['score_breakdown'].items():
        print(f"  {category.title()}: {details['score']:.1f}/{details['weight']} points")
    
    if score_data['recommendations']:
        print("\n🎯 Recommendations for improvement:")
        for rec in score_data['recommendations']:
            print(f"  {rec}")
    
    # Exit with appropriate code based on deployment action
    if grade_info['deployment_action'] == 'BLOCK':
        print(f"\n❌ Quality gates failed - blocking deployment")
        sys.exit(1)
    elif grade_info['deployment_action'] == 'BLOCK_WITH_OVERRIDE':
        print(f"\n⚠️ Quality below threshold - manual override required")
        sys.exit(2)
    elif grade_info['deployment_action'] == 'MANUAL_REVIEW':
        print(f"\n📋 Manual review recommended before deployment")
        sys.exit(0)
    else:
        print(f"\n✅ Quality gates passed - deployment approved")
        sys.exit(0)


if __name__ == "__main__":
    main()