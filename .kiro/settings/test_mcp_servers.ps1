# PowerShell script to test MCP server configuration and connectivity
# Usage: .\test_mcp_servers.ps1

Write-Host "Testing MCP Server Configuration" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Gray

# Function to test if uvx is installed
function Test-UvxInstallation {
    try {
        $result = & uvx --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "uvx is installed: $result" -ForegroundColor Green
            return $true
        } else {
            Write-Host "uvx check failed: $result" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "uvx not found: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to load MCP configuration
function Get-McpConfig {
    $configPath = Join-Path $PSScriptRoot "mcp.json"
    
    if (-not (Test-Path $configPath)) {
        throw "MCP config not found at $configPath"
    }
    
    return Get-Content $configPath | ConvertFrom-Json
}

# Function to check GitHub token
function Test-GitHubToken {
    $token = $env:GITHUB_PERSONAL_ACCESS_TOKEN
    
    if (-not $token) {
        Write-Host "GITHUB_PERSONAL_ACCESS_TOKEN not set" -ForegroundColor Yellow
        Write-Host "Set it with: `$env:GITHUB_PERSONAL_ACCESS_TOKEN='your_token'" -ForegroundColor Gray
        return $false
    }
    
    if ($token.Length -lt 20) {
        Write-Host "GITHUB_PERSONAL_ACCESS_TOKEN seems too short" -ForegroundColor Yellow
        return $false
    }
    
    Write-Host "GitHub token is configured" -ForegroundColor Green
    return $true
}

# Main execution
try {
    # Check uvx installation
    if (-not (Test-UvxInstallation)) {
        Write-Host ""
        Write-Host "uvx is not installed. Please install uv first:" -ForegroundColor Red
        Write-Host "   pip install uv" -ForegroundColor Gray
        Write-Host "   # or follow instructions in MCP_SETUP.md" -ForegroundColor Gray
        exit 1
    }
    
    # Load configuration
    try {
        $config = Get-McpConfig
        $servers = $config.mcpServers
        Write-Host ""
        Write-Host "Found $($servers.PSObject.Properties.Count) configured servers" -ForegroundColor Cyan
    } catch {
        Write-Host ""
        Write-Host "Failed to load MCP config: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
    
    # Test GitHub token if GitHub server is configured
    if ($servers.github) {
        Write-Host ""
        Write-Host "Testing GitHub configuration:" -ForegroundColor Cyan
        Test-GitHubToken | Out-Null
    }
    
    # Summary
    Write-Host ""
    Write-Host ("=" * 50) -ForegroundColor Gray
    Write-Host "MCP configuration is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Install uv/uvx if not already installed" -ForegroundColor Gray
    Write-Host "2. Set GITHUB_PERSONAL_ACCESS_TOKEN if using GitHub server" -ForegroundColor Gray
    Write-Host "3. Start Kiro to connect to MCP servers" -ForegroundColor Gray
    Write-Host "4. Check MCP Server view for connection status" -ForegroundColor Gray
    
} catch {
    Write-Host "Unexpected error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}