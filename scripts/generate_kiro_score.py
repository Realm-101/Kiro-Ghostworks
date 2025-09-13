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

    def calculate_score(self) -> float:
        """Calculate overall Kiro score based on weighted metrics."""
        
        # Test score (35% weight)
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

        # Coverage score (25% weight)
        coverage_score = min(self.score_data['coverage']['overall'], 100) * 0.25

        # Performance score (20% weight)
        p95_target = 200  # ms
        p95_actual = self.score_data['performance']['p95_response_time']
        if p95_actual > 0:
            perf_score = max(0, (p95_target - p95_actual) / p95_target * 100) * 0.20
        else:
            perf_score = 20  # Full points if no performance data

        # Security score (15% weight)
        security_base = 15
        if not self.score_data['security']['scan_passed']:
            security_base = 0
        elif self.score_data['security']['medium_severity'] > 0:
            security_base *= 0.7  # Reduce for medium severity issues
        elif self.score_data['security']['low_severity'] > 5:
            security_base *= 0.9  # Slight reduction for many low severity issues
        
        security_score = security_base

        # Build quality score (5% weight)
        build_score = 5 if self.score_data['build']['success'] else 0

        total_score = test_score + coverage_score + perf_score + security_score + build_score
        return min(total_score, 100)

    def get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'A-'
        elif score >= 80:
            return 'B+'
        elif score >= 75:
            return 'B'
        elif score >= 70:
            return 'B-'
        elif score >= 65:
            return 'C+'
        elif score >= 60:
            return 'C'
        elif score >= 55:
            return 'C-'
        elif score >= 50:
            return 'D'
        else:
            return 'F'

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
        """Generate the complete Kiro score file."""
        self.collect_metrics()
        
        overall_score = self.calculate_score()
        grade = self.get_grade(overall_score)
        recommendations = self.generate_recommendations()
        
        self.score_data.update({
            'overall_score': overall_score,
            'grade': grade,
            'recommendations': recommendations,
            'score_breakdown': {
                'tests': f"{sum(test['passed'] for test in self.score_data['tests'].values())}/{sum(test['total'] for test in self.score_data['tests'].values())} passed",
                'coverage': f"{self.score_data['coverage']['overall']:.1f}% average",
                'performance': f"{self.score_data['performance']['p95_response_time']:.1f}ms P95",
                'security': "✅ Passed" if self.score_data['security']['scan_passed'] else "❌ Failed"
            }
        })
        
        with open(output_path, 'w') as f:
            json.dump(self.score_data, f, indent=2)
        
        return self.score_data


def main():
    """Main entry point."""
    artifacts_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "kiro_score.json"
    
    generator = KiroScoreGenerator(artifacts_dir)
    score_data = generator.generate_score_file(output_file)
    
    print(f"Generated Kiro Score: {score_data['overall_score']:.1f}/100 (Grade: {score_data['grade']})")
    print(f"Score file written to: {output_file}")
    
    if score_data['recommendations']:
        print("\n🎯 Recommendations for improvement:")
        for rec in score_data['recommendations']:
            print(f"  {rec}")


if __name__ == "__main__":
    main()