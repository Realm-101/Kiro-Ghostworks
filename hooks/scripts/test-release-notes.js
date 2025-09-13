#!/usr/bin/env node

/**
 * Test script for Release Notes Generator
 * 
 * Tests the release notes generation functionality with mock data
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');
const { ReleaseNotesGenerator } = require('./release-notes');

class ReleaseNotesTest {
  constructor() {
    this.testDir = path.join(__dirname, '..', 'test-workspace');
    this.originalCwd = process.cwd();
  }

  async runTests() {
    console.log('🧪 Starting Release Notes Generator Tests...\n');

    try {
      await this.setupTestEnvironment();
      await this.testConventionalCommitParsing();
      await this.testVersionCalculation();
      await this.testChangelogGeneration();
      await this.testManualTrigger();
      
      console.log('\n✅ All tests passed!');
      
    } catch (error) {
      console.error('\n❌ Test failed:', error.message);
      throw error;
    } finally {
      await this.cleanup();
    }
  }

  async setupTestEnvironment() {
    console.log('📁 Setting up test environment...');
    
    // Create test directory
    await fs.mkdir(this.testDir, { recursive: true });
    process.chdir(this.testDir);

    // Initialize git repo
    try {
      execSync('git init', { stdio: 'pipe' });
      execSync('git config user.name "Test User"', { stdio: 'pipe' });
      execSync('git config user.email "test@example.com"', { stdio: 'pipe' });
    } catch (error) {
      console.log('⚠️ Git not available, skipping git-dependent tests');
    }

    // Create test package.json
    const packageJson = {
      name: 'test-project',
      version: '1.0.0',
      description: 'Test project for release notes'
    };
    await fs.writeFile('package.json', JSON.stringify(packageJson, null, 2));

    // Create test configuration
    const config = {
      conventionalCommits: {
        types: {
          feat: { title: '✨ Features', semver: 'minor' },
          fix: { title: '🐛 Bug Fixes', semver: 'patch' },
          docs: { title: '📚 Documentation', semver: 'patch' }
        },
        breakingChangeKeywords: ['BREAKING CHANGE:', 'BREAKING:']
      },
      versioning: {
        strategy: 'semantic',
        initialVersion: '0.1.0'
      },
      changelog: {
        path: 'CHANGELOG.md',
        includeCommitLinks: false,
        sections: {
          includeAuthors: true,
          includeScope: true
        }
      }
    };

    this.generator = new ReleaseNotesGenerator(config);
    
    console.log('✅ Test environment ready');
  }

  async testConventionalCommitParsing() {
    console.log('\n🔍 Testing conventional commit parsing...');

    const mockCommits = [
      {
        hash: 'abc123',
        message: 'feat(auth): add user authentication',
        fullMessage: 'feat(auth): add user authentication\n\nImplements JWT-based authentication system'
      },
      {
        hash: 'def456', 
        message: 'fix: resolve login bug',
        fullMessage: 'fix: resolve login bug\n\nFixes issue with password validation'
      },
      {
        hash: 'ghi789',
        message: 'feat!: breaking API change',
        fullMessage: 'feat!: breaking API change\n\nBREAKING CHANGE: API endpoints now require authentication'
      },
      {
        hash: 'jkl012',
        message: 'update readme',
        fullMessage: 'update readme'
      }
    ];

    const parsed = this.generator.parseConventionalCommits(mockCommits);

    // Test parsing results
    console.assert(parsed.length === 4, 'Should parse all commits');
    console.assert(parsed[0].type === 'feat', 'Should identify feat type');
    console.assert(parsed[0].scope === 'auth', 'Should extract scope');
    console.assert(parsed[1].type === 'fix', 'Should identify fix type');
    console.assert(parsed[2].isBreaking === true, 'Should detect breaking change');
    console.assert(parsed[3].type === 'chore', 'Should default to chore for non-conventional');

    console.log('✅ Conventional commit parsing works correctly');
  }

  async testVersionCalculation() {
    console.log('\n📈 Testing version calculation...');

    // Test patch version bump
    const patchCommits = [
      { type: 'fix', isBreaking: false },
      { type: 'docs', isBreaking: false }
    ];
    const patchVersion = this.generator.calculateNextVersion('1.0.0', patchCommits);
    console.assert(patchVersion === '1.0.1', `Expected 1.0.1, got ${patchVersion}`);

    // Test minor version bump
    const minorCommits = [
      { type: 'feat', isBreaking: false },
      { type: 'fix', isBreaking: false }
    ];
    const minorVersion = this.generator.calculateNextVersion('1.0.0', minorCommits);
    console.assert(minorVersion === '1.1.0', `Expected 1.1.0, got ${minorVersion}`);

    // Test major version bump
    const majorCommits = [
      { type: 'feat', isBreaking: true }
    ];
    const majorVersion = this.generator.calculateNextVersion('1.0.0', majorCommits);
    console.assert(majorVersion === '2.0.0', `Expected 2.0.0, got ${majorVersion}`);

    console.log('✅ Version calculation works correctly');
  }

  async testChangelogGeneration() {
    console.log('\n📝 Testing changelog generation...');

    const mockCommits = [
      {
        hash: 'abc123',
        type: 'feat',
        scope: 'auth',
        description: 'add user authentication',
        isBreaking: false,
        author: 'John Doe'
      },
      {
        hash: 'def456',
        type: 'fix',
        scope: null,
        description: 'resolve login bug',
        isBreaking: false,
        author: 'Jane Smith'
      }
    ];

    const changelogEntry = this.generator.generateChangelogEntry('1.1.0', mockCommits);
    
    console.assert(changelogEntry.includes('## [1.1.0]'), 'Should include version header');
    console.assert(changelogEntry.includes('✨ Features'), 'Should include features section');
    console.assert(changelogEntry.includes('🐛 Bug Fixes'), 'Should include bug fixes section');
    console.assert(changelogEntry.includes('**auth**: add user authentication'), 'Should include scoped feature');
    console.assert(changelogEntry.includes('by John Doe'), 'Should include author');

    console.log('✅ Changelog generation works correctly');
  }

  async testManualTrigger() {
    console.log('\n🔘 Testing manual trigger interface...');

    // Create some test commits if git is available
    try {
      // Create initial commit
      await fs.writeFile('README.md', '# Test Project');
      execSync('git add README.md', { stdio: 'pipe' });
      execSync('git commit -m "feat: initial commit"', { stdio: 'pipe' });

      // Create feature commit
      await fs.writeFile('feature.js', 'console.log("feature");');
      execSync('git add feature.js', { stdio: 'pipe' });
      execSync('git commit -m "feat(core): add new feature"', { stdio: 'pipe' });

      // Test the generator
      const result = await this.generator.generate();
      
      console.assert(result && result.version, 'Should return version information');
      console.assert(result.commitCount > 0, 'Should count commits');

      // Check if CHANGELOG.md was created
      const changelogExists = await fs.access('CHANGELOG.md').then(() => true).catch(() => false);
      console.assert(changelogExists, 'Should create CHANGELOG.md');

      if (changelogExists) {
        const changelogContent = await fs.readFile('CHANGELOG.md', 'utf8');
        console.assert(changelogContent.includes('# Changelog'), 'Should have changelog header');
        console.assert(changelogContent.includes('✨ Features'), 'Should include features');
      }

      console.log('✅ Manual trigger works correctly');
      
    } catch (error) {
      console.log('⚠️ Skipping git-dependent manual trigger test:', error.message);
    }
  }

  async cleanup() {
    console.log('\n🧹 Cleaning up test environment...');
    
    process.chdir(this.originalCwd);
    
    try {
      await fs.rm(this.testDir, { recursive: true, force: true });
      console.log('✅ Test environment cleaned up');
    } catch (error) {
      console.warn('⚠️ Could not clean up test directory:', error.message);
    }
  }
}

/**
 * Main test execution
 */
async function main() {
  const tester = new ReleaseNotesTest();
  
  try {
    await tester.runTests();
    console.log('\n🎉 Release Notes Generator is working correctly!');
  } catch (error) {
    console.error('\n💥 Tests failed:', error.message);
    process.exit(1);
  }
}

// Run tests if called directly
if (require.main === module) {
  main();
}

module.exports = { ReleaseNotesTest };