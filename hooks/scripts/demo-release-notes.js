#!/usr/bin/env node

/**
 * Demo script for Release Notes Generator
 * 
 * Demonstrates the release notes generation capabilities with sample data
 */

const fs = require('fs').promises;
const path = require('path');

async function createDemoChangelog() {
  console.log('📝 Creating demo CHANGELOG.md...\n');

  const demoChangelog = `# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2024-01-15

### ✨ Features

- **auth**: add OAuth2 integration for social login by John Doe
- **api**: implement rate limiting middleware by Jane Smith
- **ui**: add dark mode theme support by Bob Wilson

### 🐛 Bug Fixes

- **auth**: fix password reset email template by Alice Johnson
- **api**: resolve CORS issues in production by Charlie Brown
- fix memory leak in image processing by David Lee

### 📚 Documentation

- **api**: update OpenAPI specification by Sarah Connor
- add deployment guide for Docker by Mike Ross

### ♻️ Code Refactoring

- **core**: optimize database query performance by Emma Stone
- refactor authentication middleware by Tom Hardy

## [1.1.0] - 2024-01-01

### ✨ Features

- **workspace**: add multi-tenant workspace support by John Doe
- **artifacts**: implement full-text search functionality by Jane Smith

### 🐛 Bug Fixes

- **ui**: fix responsive layout issues on mobile by Bob Wilson
- **api**: handle edge cases in artifact validation by Alice Johnson

### 🧪 Tests

- add comprehensive E2E test suite by Charlie Brown
- improve unit test coverage to 85% by David Lee

## [1.0.0] - 2023-12-15

### 💥 BREAKING CHANGES

- **api**: restructure API endpoints for better REST compliance by John Doe
- **auth**: change authentication flow to use JWT tokens by Jane Smith

### ✨ Features

- **core**: initial release with artifact management by John Doe
- **auth**: implement user authentication system by Jane Smith
- **ui**: create responsive web interface by Bob Wilson

### 📦 Build System

- set up CI/CD pipeline with GitHub Actions by Alice Johnson
- configure Docker containerization by Charlie Brown

### 🔧 Maintenance

- initialize project structure and dependencies by David Lee
- set up development environment by Emma Stone
`;

  const changelogPath = path.join(process.cwd(), 'DEMO_CHANGELOG.md');
  await fs.writeFile(changelogPath, demoChangelog);
  
  console.log(`✅ Demo changelog created at: ${changelogPath}`);
  console.log('\n📋 This demonstrates:');
  console.log('  • Semantic versioning (1.0.0 → 1.1.0 → 1.2.0)');
  console.log('  • Conventional commit types with emojis');
  console.log('  • Scoped commits (auth, api, ui, etc.)');
  console.log('  • Breaking change detection');
  console.log('  • Author attribution');
  console.log('  • Proper changelog formatting');
  
  return changelogPath;
}

async function demonstrateConventionalCommits() {
  console.log('\n🔍 Conventional Commit Examples:\n');

  const examples = [
    {
      commit: 'feat(auth): add OAuth2 integration',
      description: 'New feature in auth scope → Minor version bump',
      type: 'feature',
      semver: 'minor'
    },
    {
      commit: 'fix: resolve memory leak in image processing',
      description: 'Bug fix without scope → Patch version bump',
      type: 'bugfix',
      semver: 'patch'
    },
    {
      commit: 'feat!: restructure API endpoints',
      description: 'Breaking change (!) → Major version bump',
      type: 'breaking',
      semver: 'major'
    },
    {
      commit: 'docs(api): update OpenAPI specification',
      description: 'Documentation update → Patch version bump',
      type: 'documentation',
      semver: 'patch'
    },
    {
      commit: 'perf(core): optimize database queries',
      description: 'Performance improvement → Patch version bump',
      type: 'performance',
      semver: 'patch'
    },
    {
      commit: 'chore: update dependencies',
      description: 'Maintenance task → Patch version bump',
      type: 'maintenance',
      semver: 'patch'
    }
  ];

  examples.forEach((example, index) => {
    console.log(`${index + 1}. ${example.commit}`);
    console.log(`   → ${example.description}`);
    console.log(`   → Type: ${example.type}, Semver: ${example.semver}\n`);
  });
}

async function showVersioningStrategy() {
  console.log('📈 Semantic Versioning Strategy:\n');

  const versioningRules = [
    {
      change: 'MAJOR (X.0.0)',
      triggers: ['Breaking changes', 'feat! commits', 'BREAKING CHANGE: in commit body'],
      example: '1.5.3 → 2.0.0'
    },
    {
      change: 'MINOR (0.X.0)',
      triggers: ['New features', 'feat: commits', 'New functionality'],
      example: '1.5.3 → 1.6.0'
    },
    {
      change: 'PATCH (0.0.X)',
      triggers: ['Bug fixes', 'fix: commits', 'Documentation', 'Refactoring', 'Performance'],
      example: '1.5.3 → 1.5.4'
    }
  ];

  versioningRules.forEach(rule => {
    console.log(`🔸 ${rule.change}`);
    console.log(`   Triggers: ${rule.triggers.join(', ')}`);
    console.log(`   Example: ${rule.example}\n`);
  });
}

async function demonstrateHookConfiguration() {
  console.log('⚙️ Hook Configuration Features:\n');

  const features = [
    '🎯 Git commit triggers - Automatically runs on conventional commits',
    '🔘 Manual trigger button - Generate release notes on demand',
    '📝 CHANGELOG.md generation - Maintains formatted changelog',
    '🏷️ Version tagging - Supports semantic version tags',
    '🔍 Commit parsing - Extracts type, scope, and breaking changes',
    '👥 Author attribution - Includes commit authors in changelog',
    '🔗 Commit links - Optional links to repository commits',
    '📊 Configurable sections - Customize changelog sections and formatting',
    '🚫 Debouncing - Prevents excessive triggers on rapid commits',
    '📋 Logging - Comprehensive logging for debugging and monitoring'
  ];

  features.forEach(feature => {
    console.log(`  ${feature}`);
  });
}

async function main() {
  console.log('🚀 Release Notes Generator Demo\n');
  console.log('=====================================\n');

  try {
    // Create demo changelog
    const changelogPath = await createDemoChangelog();
    
    // Show conventional commit examples
    await demonstrateConventionalCommits();
    
    // Show versioning strategy
    await showVersioningStrategy();
    
    // Show hook configuration
    await demonstrateHookConfiguration();
    
    console.log('\n🎯 To use the Release Notes Generator:');
    console.log('  1. Make commits using conventional commit format');
    console.log('  2. Click "📝 Generate Release Notes" button in Kiro');
    console.log('  3. Or let it trigger automatically on commits');
    console.log('  4. Review generated CHANGELOG.md and version updates');
    
    console.log('\n📖 Learn more about conventional commits:');
    console.log('  https://www.conventionalcommits.org/');
    
    console.log('\n✨ Demo completed successfully!');
    
  } catch (error) {
    console.error('❌ Demo failed:', error.message);
    process.exit(1);
  }
}

// Run demo if called directly
if (require.main === module) {
  main();
}

module.exports = { createDemoChangelog, demonstrateConventionalCommits };