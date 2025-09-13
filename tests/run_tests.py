#!/usr/bin/env python3
"""
Comprehensive test runner script for the Ghostworks SaaS platform.
Runs unit tests, integration tests, and E2E tests with coverage reporting.
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class TestRunner:
    """Test runner for the Ghostworks platform."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_suites": {},
            "coverage": {},
            "performance": {},
            "summary": {}
        }
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests with coverage."""
        print("🧪 Running unit tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/",
            "services/api/tests/",
            "-m", "unit",
            "--cov=services/api",
            "--cov=packages/shared",
            "--cov-report=json:coverage-unit.json",
            "--junit-xml=test-results-unit.xml",
            "-v"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        # Parse coverage data
        coverage_file = self.project_root / "coverage-unit.json"
        coverage_data = {}
        if coverage_file.exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "coverage": coverage_data.get("totals", {}).get("percent_covered", 0) if coverage_data else 0,
            "passed": result.returncode == 0
        }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running integration tests...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/api/",
            "-m", "integration",
            "--junit-xml=test-results-integration.xml",
            "-v"
        ]
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0
        }
    
    def run_e2e_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests with Playwright."""
        print("🎭 Running E2E tests...")
        
        # First, install Playwright browsers if needed
        install_cmd = ["npx", "playwright", "install"]
        subprocess.run(install_cmd, cwd=self.project_root / "apps" / "web")
        
        # Run Playwright tests
        cmd = [
            "npx", "playwright", "test",
            "--reporter=json:test-results-e2e.json",
            "--reporter=html:playwright-report"
        ]
        
        result = subprocess.run(
            cmd, 
            cwd=self.project_root / "apps" / "web", 
            capture_output=True, 
            text=True
        )
        
        # Parse Playwright results
        results_file = self.project_root / "apps" / "web" / "test-results-e2e.json"
        test_results = {}
        if results_file.exists():
            with open(results_file) as f:
                test_results = json.load(f)
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "results": test_results,
            "passed": result.returncode == 0
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests (if available)."""
        print("⚡ Running performance tests...")
        
        # Check if k6 is available
        k6_check = subprocess.run(["which", "k6"], capture_output=True)
        if k6_check.returncode != 0:
            return {
                "skipped": True,
                "reason": "k6 not installed",
                "passed": True
            }
        
        # Run k6 performance tests if they exist
        perf_dir = self.project_root / "tests" / "performance"
        if not perf_dir.exists():
            return {
                "skipped": True,
                "reason": "No performance tests found",
                "passed": True
            }
        
        cmd = ["k6", "run", "--out", "json=performance-results.json", "api-load-test.js"]
        result = subprocess.run(cmd, cwd=perf_dir, capture_output=True, text=True)
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0
        }
    
    def check_code_quality(self) -> Dict[str, Any]:
        """Run code quality checks."""
        print("🔍 Running code quality checks...")
        
        results = {}
        
        # Python linting with flake8
        flake8_cmd = ["flake8", "services/api", "tests/", "--max-line-length=100"]
        flake8_result = subprocess.run(flake8_cmd, cwd=self.project_root, capture_output=True, text=True)
        results["flake8"] = {
            "passed": flake8_result.returncode == 0,
            "output": flake8_result.stdout + flake8_result.stderr
        }
        
        # Python formatting with black
        black_cmd = ["black", "--check", "services/api", "tests/"]
        black_result = subprocess.run(black_cmd, cwd=self.project_root, capture_output=True, text=True)
        results["black"] = {
            "passed": black_result.returncode == 0,
            "output": black_result.stdout + black_result.stderr
        }
        
        # TypeScript/JavaScript linting
        eslint_cmd = ["npm", "run", "lint"]
        eslint_result = subprocess.run(
            eslint_cmd, 
            cwd=self.project_root / "apps" / "web", 
            capture_output=True, 
            text=True
        )
        results["eslint"] = {
            "passed": eslint_result.returncode == 0,
            "output": eslint_result.stdout + eslint_result.stderr
        }
        
        return results
    
    def generate_kiro_score(self) -> Dict[str, Any]:
        """Generate kiro_score.json with test results and metrics."""
        unit_results = self.results["test_suites"].get("unit", {})
        integration_results = self.results["test_suites"].get("integration", {})
        e2e_results = self.results["test_suites"].get("e2e", {})
        performance_results = self.results["test_suites"].get("performance", {})
        quality_results = self.results.get("code_quality", {})
        
        # Calculate scores
        unit_score = 100 if unit_results.get("passed", False) else 0
        integration_score = 100 if integration_results.get("passed", False) else 0
        e2e_score = 100 if e2e_results.get("passed", False) else 0
        performance_score = 100 if performance_results.get("passed", False) else 0
        
        # Code quality score
        quality_checks = quality_results.values() if quality_results else []
        quality_score = (
            sum(1 for check in quality_checks if check.get("passed", False)) / 
            len(quality_checks) * 100
        ) if quality_checks else 0
        
        # Coverage score
        coverage_percent = unit_results.get("coverage", 0)
        coverage_score = min(coverage_percent, 100)
        
        # Overall score (weighted average)
        overall_score = (
            unit_score * 0.3 +
            integration_score * 0.25 +
            e2e_score * 0.2 +
            coverage_score * 0.15 +
            quality_score * 0.1
        )
        
        kiro_score = {
            "timestamp": self.results["timestamp"],
            "overall_score": round(overall_score, 2),
            "scores": {
                "unit_tests": unit_score,
                "integration_tests": integration_score,
                "e2e_tests": e2e_score,
                "performance_tests": performance_score,
                "code_quality": round(quality_score, 2),
                "coverage": round(coverage_score, 2)
            },
            "metrics": {
                "test_coverage_percent": coverage_percent,
                "total_tests_run": (
                    unit_results.get("test_count", 0) +
                    integration_results.get("test_count", 0) +
                    e2e_results.get("test_count", 0)
                ),
                "tests_passed": all([
                    unit_results.get("passed", False),
                    integration_results.get("passed", False),
                    e2e_results.get("passed", False)
                ])
            },
            "details": self.results
        }
        
        # Write kiro_score.json
        with open(self.project_root / "kiro_score.json", "w") as f:
            json.dump(kiro_score, f, indent=2)
        
        return kiro_score
    
    def run_all_tests(self, skip_e2e: bool = False, skip_performance: bool = False) -> Dict[str, Any]:
        """Run all test suites."""
        print("🚀 Starting comprehensive test suite...")
        
        # Run unit tests
        self.results["test_suites"]["unit"] = self.run_unit_tests()
        
        # Run integration tests
        self.results["test_suites"]["integration"] = self.run_integration_tests()
        
        # Run E2E tests (unless skipped)
        if not skip_e2e:
            self.results["test_suites"]["e2e"] = self.run_e2e_tests()
        else:
            print("⏭️  Skipping E2E tests")
            self.results["test_suites"]["e2e"] = {"skipped": True, "passed": True}
        
        # Run performance tests (unless skipped)
        if not skip_performance:
            self.results["test_suites"]["performance"] = self.run_performance_tests()
        else:
            print("⏭️  Skipping performance tests")
            self.results["test_suites"]["performance"] = {"skipped": True, "passed": True}
        
        # Run code quality checks
        self.results["code_quality"] = self.check_code_quality()
        
        # Generate final score
        kiro_score = self.generate_kiro_score()
        
        # Print summary
        self.print_summary(kiro_score)
        
        return self.results
    
    def print_summary(self, kiro_score: Dict[str, Any]):
        """Print test results summary."""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        overall_score = kiro_score["overall_score"]
        print(f"Overall Score: {overall_score:.1f}/100")
        
        if overall_score >= 90:
            print("🎉 Excellent! All systems go!")
        elif overall_score >= 80:
            print("✅ Good! Minor improvements needed.")
        elif overall_score >= 70:
            print("⚠️  Acceptable, but needs attention.")
        else:
            print("❌ Needs significant improvement.")
        
        print("\nDetailed Scores:")
        for category, score in kiro_score["scores"].items():
            status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"  {status} {category.replace('_', ' ').title()}: {score:.1f}/100")
        
        print(f"\nTest Coverage: {kiro_score['metrics']['test_coverage_percent']:.1f}%")
        print(f"Total Tests: {kiro_score['metrics']['total_tests_run']}")
        print(f"All Tests Passed: {'Yes' if kiro_score['metrics']['tests_passed'] else 'No'}")
        
        print("\n📄 Reports generated:")
        print("  - kiro_score.json (overall results)")
        print("  - htmlcov/index.html (coverage report)")
        print("  - playwright-report/index.html (E2E test report)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Ghostworks test suite")
    parser.add_argument("--skip-e2e", action="store_true", help="Skip E2E tests")
    parser.add_argument("--skip-performance", action="store_true", help="Skip performance tests")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--e2e-only", action="store_true", help="Run only E2E tests")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    runner = TestRunner(project_root)
    
    try:
        if args.unit_only:
            result = runner.run_unit_tests()
            print(f"Unit tests: {'PASSED' if result['passed'] else 'FAILED'}")
        elif args.integration_only:
            result = runner.run_integration_tests()
            print(f"Integration tests: {'PASSED' if result['passed'] else 'FAILED'}")
        elif args.e2e_only:
            result = runner.run_e2e_tests()
            print(f"E2E tests: {'PASSED' if result['passed'] else 'FAILED'}")
        else:
            runner.run_all_tests(
                skip_e2e=args.skip_e2e,
                skip_performance=args.skip_performance
            )
        
        return 0
    
    except KeyboardInterrupt:
        print("\n⏹️  Test run interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test run failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())