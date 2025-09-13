# MCP Server Setup Guide

This document provides instructions for setting up and configuring MCP (Model Context Protocol) servers for the Ghostworks SaaS platform.

## Prerequisites

### Install uv and uvx

The MCP servers are configured to use `uvx` for execution. You need to install `uv` first:

#### Windows (PowerShell)
```powershell
# Using pip
pip install uv

# Or using winget
winget install astral-sh.uv

# Or using chocolatey
choco install uv
```

#### macOS/Linux
```bash
# Using curl
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv

# Or using homebrew (macOS)
brew install uv
```

After installing `uv`, `uvx` should be available automatically.

## Configured MCP Servers

### 1. GitHub MCP Server

**Purpose**: Provides read access to GitHub repositories, issues, pull requests, and code search.

**Configuration**:
- **Command**: `uvx mcp-server-github`
- **Environment Variables Required**:
  - `GITHUB_PERSONAL_ACCESS_TOKEN`: GitHub personal access token with repo read permissions

**Auto-approved Operations** (read-only):
- Repository search and information retrieval
- File content reading
- Issue and pull request listing
- Code search across repositories
- Commit and branch information

**Setup Steps**:
1. Create a GitHub Personal Access Token:
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Generate a new token with `repo` scope for private repos or `public_repo` for public only
   - Copy the token

2. Set the environment variable:
   ```powershell
   # Windows
   $env:GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
   
   # Or add to your .env file
   echo "GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here" >> .env
   ```

### 2. AWS Documentation MCP Server

**Purpose**: Provides access to AWS service documentation, best practices, and architectural guidance.

**Configuration**:
- **Command**: `uvx awslabs.aws-documentation-mcp-server@latest`
- **No authentication required** (public documentation)

**Auto-approved Operations** (read-only):
- AWS service documentation search
- Best practices retrieval
- Architecture pattern lookup
- FAQ searches
- Pricing information access

## Testing MCP Server Connectivity

### Verify uvx Installation
```powershell
uvx --version
```

### Test GitHub MCP Server
```powershell
# Set your GitHub token
$env:GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"

# Test the server (this will download and run it)
uvx mcp-server-github --help
```

### Test AWS Documentation MCP Server
```powershell
# Test the server (this will download and run it)
uvx awslabs.aws-documentation-mcp-server@latest --help
```

## Configuration Details

### Auto-Approval Settings

The MCP configuration includes auto-approval for read-only operations to streamline development workflows:

- **GitHub**: Repository browsing, code reading, issue tracking
- **AWS Docs**: Documentation lookup, best practices, architecture patterns

### Security Considerations

- Only read-only operations are auto-approved
- Write operations (creating issues, PRs, etc.) require explicit approval
- GitHub token should have minimal required permissions
- Environment variables are used for sensitive configuration

## Troubleshooting

### Common Issues

1. **uvx not found**:
   - Ensure `uv` is installed and in your PATH
   - Restart your terminal after installation

2. **GitHub authentication fails**:
   - Verify your personal access token is correct
   - Check token permissions include required scopes
   - Ensure environment variable is set correctly

3. **Server download fails**:
   - Check internet connectivity
   - Verify uvx can access PyPI
   - Try running with verbose logging: `FASTMCP_LOG_LEVEL=DEBUG`

### Verification Commands

```powershell
# Check if uv is installed
uv --version

# Check if uvx is available
uvx --version

# List available MCP servers
uvx --help

# Test GitHub server with debug logging
$env:FASTMCP_LOG_LEVEL="DEBUG"
$env:GITHUB_PERSONAL_ACCESS_TOKEN="your_token"
uvx mcp-server-github
```

## Integration with Kiro

Once the MCP servers are configured and tested:

1. The servers will automatically connect when Kiro starts
2. Use the MCP Server view in Kiro to monitor connection status
3. Servers can be reconnected from the Kiro interface without restart
4. Check the command palette for MCP-related commands

## Next Steps

After successful MCP setup:
1. Configure agent hooks for automated workflows
2. Test MCP tool functionality within Kiro
3. Set up additional MCP servers as needed for your workflow