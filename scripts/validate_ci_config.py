#!/usr/bin/env python3
"""
CI/CD Configuration Validator

This script validates the GitHub Actions workflow configuration
and ensures all required files and dependencies are in place.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any


class CIConfigValidator:
    """Validates CI/CD configuration files and dependencies."""
    
    def __init__(self, repo_root: str = "."):
        self.repo_root = Path(repo_root)
        self.errors = []
        self.warnings = []
    
    def validate_workflow_file(self) -> bool:
        """Validate the main CI workflow file."""
        workflow_file = self.repo_root / ".github" / "workflows" / "ci.yml"
        
        if not workflow_file.exists():
            self.errors.append("CI workflow file not found: .github/workflows/ci.yml")
            return False
        
        try:
            with open(workflow_file, 'r', encoding='utf-8') as f:
                workflow = yaml.safe_load(f)
            
            if workflow is None:
                self.errors.append("Workflow file is empty or invalid YAML")
                return False
            
            # Check required jobs
            required_jobs = [
                'lint', 'test-unit', 'test-integration', 'test-e2e',
                'security-scan', 'test-performance', 'build',
                'generate-score', 'pr-comment'
            ]
            
            jobs = workflow.get('jobs', {})
            if not jobs:
                self.errors.append("No jobs found in workflow file")
                return False
                
            for job in required_jobs:
                if job not in jobs:
                    self.errors.append(f"Required job '{job}' not found in workflow")
            
            # Check environment variables
            required_env_vars = ['NODE_VERSION', 'PYTHON_VERSION']
            env = workflow.get('env', {})
            for var in required_env_vars:
                if var not in env:
                    self.warnings.append(f"Environment variable '{var}' not defined")
            
            return len(self.errors) == 0
            
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in workflow file: {e}")
            return False
    
    def validate_zap_config(self) -> bool:
        """Validate ZAP security scanning configuration."""
        zap_rules = self.repo_root / ".zap" / "rules.tsv"
        
        if not zap_rules.exists():
            self.errors.append("ZAP rules file not found: .zap/rules.tsv")
            return False
        
        try:
            with open(zap_rules, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check for basic rules
            rule_count = sum(1 for line in lines if line.strip() and not line.startswith('#'))
            if rule_count < 5:
                self.warnings.append("ZAP rules file seems incomplete (less than 5 rules)")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error reading ZAP rules file: {e}")
            return False
    
    def validate_scoring_script(self) -> bool:
        """Validate the Kiro scoring script."""
        score_script = self.repo_root / "scripts" / "generate_kiro_score.py"
        
        if not score_script.exists():
            self.errors.append("Kiro scoring script not found: scripts/generate_kiro_score.py")
            return False
        
        # Check if script is executable
        if not os.access(score_script, os.X_OK):
            self.warnings.append("Scoring script is not executable")
        
        # Basic syntax check
        try:
            with open(score_script, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, str(score_script), 'exec')
            return True
            
        except SyntaxError as e:
            self.errors.append(f"Syntax error in scoring script: {e}")
            return False
    
    def validate_pr_bot_script(self) -> bool:
        """Validate the PR comment bot script."""
        bot_script = self.repo_root / "scripts" / "pr_comment_bot.js"
        
        if not bot_script.exists():
            self.errors.append("PR bot script not found: scripts/pr_comment_bot.js")
            return False
        
        try:
            with open(bot_script, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for required exports
            if 'PRCommentBot' not in content:
                self.errors.append("PR bot script missing PRCommentBot class")
            
            if 'module.exports' not in content:
                self.errors.append("PR bot script missing module.exports")
            
            return len(self.errors) == 0
            
        except Exception as e:
            self.errors.append(f"Error reading PR bot script: {e}")
            return False
    
    def validate_test_configs(self) -> bool:
        """Validate test configuration files."""
        configs_to_check = [
            ("pytest.ini", "Pytest configuration"),
            ("apps/web/playwright.config.ts", "Playwright configuration"),
            ("apps/web/vitest.config.ts", "Vitest configuration"),
        ]
        
        all_valid = True
        for config_path, description in configs_to_check:
            config_file = self.repo_root / config_path
            if not config_file.exists():
                self.warnings.append(f"{description} not found: {config_path}")
                all_valid = False
        
        return all_valid
    
    def validate_package_configs(self) -> bool:
        """Validate package.json files for test scripts."""
        package_files = [
            "package.json",
            "apps/web/package.json",
        ]
        
        all_valid = True
        for package_path in package_files:
            package_file = self.repo_root / package_path
            if not package_file.exists():
                self.warnings.append(f"Package file not found: {package_path}")
                continue
            
            try:
                with open(package_file, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get('scripts', {})
                
                # Check for required scripts based on file
                if package_path == "package.json":
                    required_scripts = ['test', 'test:unit', 'test:integration', 'lint']
                else:  # apps/web/package.json
                    required_scripts = ['test', 'test:e2e', 'build', 'lint']
                
                for script in required_scripts:
                    if script not in scripts:
                        self.warnings.append(f"Missing script '{script}' in {package_path}")
                
            except (json.JSONDecodeError, Exception) as e:
                self.errors.append(f"Error reading {package_path}: {e}")
                all_valid = False
        
        return all_valid
    
    def validate_docker_configs(self) -> bool:
        """Validate Docker configuration files."""
        docker_files = [
            "docker-compose.yml",
            "apps/web/Dockerfile",
        ]
        
        all_valid = True
        for docker_path in docker_files:
            docker_file = self.repo_root / docker_path
            if not docker_file.exists():
                self.warnings.append(f"Docker file not found: {docker_path}")
                all_valid = False
        
        return all_valid
    
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating CI/CD configuration...")
        
        checks = [
            ("Workflow file", self.validate_workflow_file),
            ("ZAP configuration", self.validate_zap_config),
            ("Scoring script", self.validate_scoring_script),
            ("PR bot script", self.validate_pr_bot_script),
            ("Test configurations", self.validate_test_configs),
            ("Package configurations", self.validate_package_configs),
            ("Docker configurations", self.validate_docker_configs),
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                status = "✅" if result else "❌"
                print(f"{status} {check_name}")
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ {check_name} (error: {e})")
                self.errors.append(f"Validation error in {check_name}: {e}")
                all_passed = False
        
        # Print summary
        print("\n📊 Validation Summary:")
        print(f"Errors: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print("\n⚠️ Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if all_passed and not self.errors:
            print("\n🎉 All validations passed!")
        elif not self.errors:
            print("\n✅ Validation passed with warnings")
        else:
            print("\n💥 Validation failed with errors")
        
        return all_passed and len(self.errors) == 0


def main():
    """Main entry point."""
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    validator = CIConfigValidator(repo_root)
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()