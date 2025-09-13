#!/usr/bin/env python3
"""
Demo Asset Validation Script

Validates that all required screenshots and assets are present for the demo script.
This ensures presenters don't hunt for missing images during demonstrations.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Required screenshots for demo script sections
CRITICAL_SCREENSHOTS = {
    "Authentication Flow (Section 1.1)": [
        "auth-login-form.png",
        "auth-workspace-selector.png", 
        "auth-workspace-switching.png"
    ],
    "Artifact Management (Section 1.2)": [
        "artifacts-list-view.png",
        "artifacts-search-filter.png",
        "artifacts-create-modal.png",
        "artifacts-edit-modal.png"
    ],
    "Live Metrics Dashboard (Section 2.1)": [
        "tour-landing-page.png",
        "tour-metrics-dashboard.png",
        "tour-telemetry-demo.png"
    ],
    "Grafana Dashboards (Section 2.2)": [
        "grafana-api-golden-signals.png",
        "grafana-business-metrics.png",
        "grafana-system-overview.png"
    ],
    "AI-Native Features (Section 3)": [
        "tour-asset-gardener.png",
        "mcp-configuration.png",
        "agent-hooks-interface.png"
    ],
    "API Documentation (Section 4.1)": [
        "api-docs-swagger-ui.png",
        "api-docs-authentication.png"
    ]
}

# Minimum requirements for screenshots
MIN_WIDTH = 1200
MIN_HEIGHT = 600
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class DemoAssetValidator:
    """Validates demo assets and provides actionable feedback."""
    
    def __init__(self, screenshots_dir: str = "docs/screenshots"):
        self.screenshots_dir = Path(screenshots_dir)
        self.missing_screenshots = []
        self.invalid_screenshots = []
        self.warnings = []
        
    def validate_all(self) -> bool:
        """Validate all demo assets and return True if ready for demo."""
        print("🎯 Validating Demo Assets for Ghostworks Presentation")
        print("=" * 60)
        
        # Check if screenshots directory exists
        if not self.screenshots_dir.exists():
            print(f"❌ Screenshots directory not found: {self.screenshots_dir}")
            print(f"   Create the directory: mkdir -p {self.screenshots_dir}")
            return False
        
        # Validate critical screenshots
        all_valid = True
        for section, screenshots in CRITICAL_SCREENSHOTS.items():
            section_valid = self.validate_section(section, screenshots)
            all_valid = all_valid and section_valid
        
        # Show summary
        self.print_summary()
        
        return all_valid and len(self.missing_screenshots) == 0
    
    def validate_section(self, section_name: str, screenshots: List[str]) -> bool:
        """Validate screenshots for a specific demo section."""
        print(f"\n📋 {section_name}")
        section_valid = True
        
        for screenshot in screenshots:
            screenshot_path = self.screenshots_dir / screenshot
            
            if not screenshot_path.exists():
                print(f"   ❌ MISSING: {screenshot}")
                self.missing_screenshots.append((section_name, screenshot))
                section_valid = False
            else:
                # Validate screenshot properties
                validation_result = self.validate_screenshot_properties(screenshot_path)
                if validation_result[0]:
                    print(f"   ✅ {screenshot}")
                else:
                    print(f"   ⚠️  {screenshot} - {validation_result[1]}")
                    self.warnings.append((screenshot, validation_result[1]))
        
        return section_valid
    
    def validate_screenshot_properties(self, screenshot_path: Path) -> Tuple[bool, str]:
        """Validate individual screenshot properties."""
        try:
            # Check file size
            file_size = screenshot_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                return False, f"File too large: {file_size / 1024 / 1024:.1f}MB (max: {MAX_FILE_SIZE / 1024 / 1024}MB)"
            
            if file_size < 10 * 1024:  # Less than 10KB is suspicious
                return False, f"File too small: {file_size / 1024:.1f}KB (might be corrupted)"
            
            # For now, we can't easily check image dimensions without PIL
            # But we can check file extension
            if not screenshot_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                return False, f"Invalid format: {screenshot_path.suffix} (use PNG or JPG)"
            
            return True, "Valid"
            
        except Exception as e:
            return False, f"Error validating: {str(e)}"
    
    def print_summary(self):
        """Print validation summary and next steps."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_required = sum(len(screenshots) for screenshots in CRITICAL_SCREENSHOTS.values())
        missing_count = len(self.missing_screenshots)
        present_count = total_required - missing_count
        
        print(f"Screenshots: {present_count}/{total_required} present")
        print(f"Missing: {missing_count}")
        print(f"Warnings: {len(self.warnings)}")
        
        if missing_count == 0:
            print("\n✅ DEMO READY!")
            print("   All critical screenshots are present.")
            print("   You can proceed with the demo presentation.")
        else:
            print(f"\n❌ DEMO NOT READY")
            print(f"   {missing_count} critical screenshots are missing.")
            print("   Demo sections will fail without these images.")
        
        # Show missing screenshots grouped by section
        if self.missing_screenshots:
            print(f"\n🚨 MISSING SCREENSHOTS:")
            current_section = None
            for section, screenshot in self.missing_screenshots:
                if section != current_section:
                    print(f"\n   {section}:")
                    current_section = section
                print(f"     - {screenshot}")
        
        # Show warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for screenshot, warning in self.warnings:
                print(f"   - {screenshot}: {warning}")
        
        # Provide next steps
        if missing_count > 0:
            print(f"\n📋 NEXT STEPS:")
            print("   1. Start the platform: make dev-up")
            print("   2. Navigate through the UI and capture missing screenshots")
            print("   3. Save screenshots to docs/screenshots/ with exact names above")
            print("   4. Run this validation again: make validate-demo-assets")
            print("   5. See docs/screenshots/README.md for capture guidelines")
    
    def generate_capture_script(self):
        """Generate a script to help capture missing screenshots."""
        if not self.missing_screenshots:
            return
        
        script_path = Path("scripts/capture_missing_screenshots.md")
        
        with open(script_path, 'w') as f:
            f.write("# Missing Screenshots Capture Guide\n\n")
            f.write("This guide helps you capture the missing screenshots for the demo.\n\n")
            
            f.write("## Prerequisites\n")
            f.write("```bash\n")
            f.write("# Start the platform\n")
            f.write("make dev-up\n")
            f.write("```\n\n")
            
            current_section = None
            for section, screenshot in self.missing_screenshots:
                if section != current_section:
                    f.write(f"## {section}\n\n")
                    current_section = section
                
                # Provide specific instructions based on screenshot name
                f.write(f"### {screenshot}\n")
                f.write(self.get_capture_instructions(screenshot))
                f.write(f"\n**Save as**: `docs/screenshots/{screenshot}`\n\n")
        
        print(f"\n📝 Generated capture guide: {script_path}")
    
    def get_capture_instructions(self, screenshot: str) -> str:
        """Get specific capture instructions for a screenshot."""
        instructions = {
            "auth-login-form.png": "1. Go to http://localhost:3000\n2. Capture the login form\n3. Ensure demo credentials are visible\n",
            "auth-workspace-selector.png": "1. Login as owner@acme.com\n2. Click workspace dropdown\n3. Capture showing both workspaces\n",
            "artifacts-list-view.png": "1. Navigate to main artifacts page\n2. Ensure demo data is loaded\n3. Capture full listing with pagination\n",
            "tour-landing-page.png": "1. Go to http://localhost:3000/tour\n2. Capture the landing page\n3. Show interactive elements\n",
            "grafana-api-golden-signals.png": "1. Go to http://localhost:3001\n2. Login as admin/admin\n3. Open API Golden Signals dashboard\n4. Capture with realistic metrics\n",
            "api-docs-swagger-ui.png": "1. Go to http://localhost:8000/docs\n2. Capture the OpenAPI interface\n3. Show available endpoints\n"
        }
        
        return instructions.get(screenshot, "1. Navigate to the appropriate page\n2. Capture the relevant interface\n3. Ensure high quality and proper framing\n")


def main():
    """Main entry point."""
    validator = DemoAssetValidator()
    
    # Run validation
    is_ready = validator.validate_all()
    
    # Generate capture guide if needed
    if not is_ready:
        validator.generate_capture_script()
    
    # Exit with appropriate code
    sys.exit(0 if is_ready else 1)


if __name__ == "__main__":
    main()