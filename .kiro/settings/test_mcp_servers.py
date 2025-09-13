#!/usr/bin/env python3
"""
Test script for MCP server connectivity and basic functionality.

This script verifies that the configured MCP servers can be reached
and provides basic functionality testing.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any


def load_mcp_config() -> Dict[str, Any]:
    """Load the MCP configuration from mcp.json."""
    config_path = Path(__file__).parent / "mcp.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"MCP config not found at {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)


def check_uvx_installation() -> bool:
    """Check if uvx is installed and available."""
    try:
        result = subprocess.run(
            ["uvx", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        if result.returncode == 0:
            print(f"✓ uvx is installed: {result.stdout.strip()}")
            return True
        else:
            print(f"✗ uvx check failed: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"✗ uvx not found or not responding: {e}")
        return False


def test_server_availability(server_name: str, server_config: Dict[str, Any]) -> bool:
    """Test if an MCP server can be reached."""
    if server_config.get("disabled", False):
        print(f"⚠ {server_name} is disabled in configuration")
        return False
    
    command = server_config["command"]
    args = server_config["args"]
    env = dict(os.environ)
    env.update(server_config.get("env", {}))
    
    # Replace environment variable placeholders
    for key, value in env.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            env[key] = os.getenv(env_var, "")
    
    try:
        # Test with --help flag to avoid hanging
        full_command = [command] + args + ["--help"]
        result = subprocess.run(
            full_command,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✓ {server_name} server is accessible")
            return True
        else:
            print(f"✗ {server_name} server test failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"✗ {server_name} server test timed out")
        return False
    except Exception as e:
        print(f"✗ {server_name} server test error: {e}")
        return False


def check_github_token() -> bool:
    """Check if GitHub token is configured."""
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        print("⚠ GITHUB_PERSONAL_ACCESS_TOKEN not set")
        print("  Set it with: export GITHUB_PERSONAL_ACCESS_TOKEN=your_token")
        return False
    
    if len(token) < 20:  # GitHub tokens are typically longer
        print("⚠ GITHUB_PERSONAL_ACCESS_TOKEN seems too short")
        return False
    
    print("✓ GitHub token is configured")
    return True


def test_auto_approval_config(server_config: Dict[str, Any]) -> bool:
    """Verify auto-approval configuration is present."""
    auto_approve = server_config.get("autoApprove", [])
    if not auto_approve:
        print("⚠ No auto-approval settings configured")
        return False
    
    print(f"✓ {len(auto_approve)} operations configured for auto-approval")
    return True


def main():
    """Run all MCP server tests."""
    print("🔧 Testing MCP Server Configuration")
    print("=" * 50)
    
    # Check uvx installation
    if not check_uvx_installation():
        print("\n❌ uvx is not installed. Please install uv first:")
        print("   pip install uv")
        print("   # or follow instructions in MCP_SETUP.md")
        return 1
    
    # Load configuration
    try:
        config = load_mcp_config()
        servers = config.get("mcpServers", {})
        print(f"\n📋 Found {len(servers)} configured servers")
    except Exception as e:
        print(f"\n❌ Failed to load MCP config: {e}")
        return 1
    
    # Test each server
    all_passed = True
    for server_name, server_config in servers.items():
        print(f"\n🧪 Testing {server_name} server:")
        
        # Check auto-approval config
        test_auto_approval_config(server_config)
        
        # Special checks for GitHub
        if server_name == "github":
            if not check_github_token():
                all_passed = False
                continue
        
        # Test server availability
        if not test_server_availability(server_name, server_config):
            all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All MCP servers are configured and accessible!")
        print("\nNext steps:")
        print("1. Start Kiro to connect to MCP servers")
        print("2. Check MCP Server view for connection status")
        print("3. Test MCP tools in Kiro interface")
    else:
        print("❌ Some MCP servers failed tests")
        print("Check the errors above and refer to MCP_SETUP.md")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())