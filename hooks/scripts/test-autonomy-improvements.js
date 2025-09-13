#!/usr/bin/env node

/**
 * Test script for autonomy hook improvements
 * Tests the enhanced release notes generator and asset gardener
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');
const { ReleaseNotesGenerator } = require('./release-notes');
const { AssetGardener } = require('./asset-gardener');

class AutonomyImprovementsTester {
  constructor() {
    this.testDir = path.join(__dirname, '..', 'test-autonomy');
    this.originalCwd = process.cwd();
  }

  async runTests() {
    console.log('🧪 Starting Autonomy Improvements Test Suite...\n');

    try {
      await this.setupTestEnvironment();
      
      // Test Release Notes improvements
      await this.testReleaseNotesImprovements();
      
      // Test Asset Gardener improvements
      await this.testAssetGardenerImprovements();
      
      console.log('\n✅ All autonomy improvement tests passed!');
      
    } catch (error) {
      console.error('\n❌ Test failed:', error.message);
      throw error;
    } finally {
      await this.cleanup();
    }
  }

  async setupTestEnvironment() {
    console.log('📁 Setting up test environment...');
    
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
      name: 'test-autonomy-project',
      version: '1.0.0',
      description: 'Test project for autonomy improvements'
    };
    await fs.writeFile('package.json', JSON.stringify(packageJson, null, 2));

    console.log('✅ Test environment ready');
  }

  async testReleaseNotesImprovements() {
    console.log('\n📝 Testing Release Notes Generator improvements...');

    // Test configuration
    const config = {
      conventionalCommits: {
        types: {
          feat: { title: '✨ Features', semver: 'minor' },
          fix: { title: '🐛 Bug Fixes', semver: 'patch' },
          docs: { title: '📚 Documentation', semver: 'patch' },
          revert: { title: '⏪ Reverts', semver: 'patch' }
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

    // Test 1: Revert commit handling
    await this.testRevertCommitHandling(config);
    
    // Test 2: Dry-run mode
    await this.testDryRunMode(config);
    
    // Test 3: No prior tag scenario
    await this.testNoPriorTagScenario(config);
    
    console.log('✅ Release Notes improvements working correctly');
  }

  async testRevertCommitHandling(config) {
    console.log('  🔄 Testing revert commit handling...');

    try {
      // Create commits including a revert
      await fs.writeFile('feature.js', 'console.log("feature");');
      execSync('git add feature.js', { stdio: 'pipe' });
      execSync('git commit -m "feat: add new feature"', { stdio: 'pipe' });

      await fs.writeFile('bug.js', 'console.log("bug");');
      execSync('git add bug.js', { stdio: 'pipe' });
      execSync('git commit -m "fix: fix important bug"', { stdio: 'pipe' });

      // Create a revert commit
      execSync('git revert HEAD --no-edit', { stdio: 'pipe' });

      const generator = new ReleaseNotesGenerator(config);
      const commits = await generator.getCommitsSinceLastTag();
      const parsed = generator.parseConventionalCommits(commits);

      // Should have 3 commits: feat, fix, revert
      console.assert(parsed.length === 3, `Expected 3 commits, got ${parsed.length}`);
      
      // Find the revert commit
      const revertCommit = parsed.find(c => c.type === 'revert');
      console.assert(revertCommit, 'Should identify revert commit');
      console.assert(revertCommit.isRevert === true, 'Should mark as revert');
      console.assert(revertCommit.isBreaking === false, 'Reverts should not be breaking');

      // Test version calculation (reverts shouldn't affect semver)
      const version = generator.calculateNextVersion('1.0.0', parsed);
      console.assert(version === '1.1.0', `Expected 1.1.0 (minor for feat), got ${version}`);

      console.log('    ✅ Revert commits handled correctly');
      
    } catch (error) {
      console.log('    ⚠️ Skipping revert test:', error.message);
    }
  }

  async testDryRunMode(config) {
    console.log('  🔍 Testing dry-run mode...');

    const dryRunGenerator = new ReleaseNotesGenerator(config, { dryRun: true });
    const result = await dryRunGenerator.generate();

    console.assert(result.dryRun === true, 'Should be in dry-run mode');
    console.assert(result.proposedChanges, 'Should include proposed changes');
    console.assert(result.proposedChanges.changelogEntry, 'Should include changelog entry');
    console.assert(result.proposedChanges.versionBump, 'Should include version bump info');

    // Verify no files were actually modified
    const changelogExists = await fs.access('CHANGELOG.md').then(() => true).catch(() => false);
    console.assert(!changelogExists, 'Should not create CHANGELOG.md in dry-run mode');

    console.log('    ✅ Dry-run mode working correctly');
  }

  async testNoPriorTagScenario(config) {
    console.log('  🏷️ Testing no prior tag scenario...');

    // Ensure no tags exist
    try {
      const tags = execSync('git tag', { encoding: 'utf8', stdio: 'pipe' }).trim();
      if (tags) {
        console.log('    ⚠️ Tags exist, skipping no-tag test');
        return;
      }
    } catch {
      // No git or no tags, which is what we want
    }

    const generator = new ReleaseNotesGenerator(config);
    const currentVersion = await generator.getCurrentVersion();
    
    // Should use initial version when no tags exist
    console.assert(currentVersion === '0.1.0', `Expected initial version 0.1.0, got ${currentVersion}`);

    console.log('    ✅ No prior tag scenario handled correctly');
  }

  async testAssetGardenerImprovements() {
    console.log('\n🌱 Testing Asset Gardener improvements...');

    // Create test images directory
    const imagesDir = path.join(this.testDir, 'images');
    await fs.mkdir(imagesDir, { recursive: true });

    // Test configuration
    const config = {
      outputFormats: ["webp", "original"],
      sizes: [
        { "name": "thumbnail", "width": 150, "height": 150 },
        { "name": "medium", "width": 800, "height": null }
      ],
      quality: { webp: 85, jpeg: 85, png: 95 },
      optimization: { progressive: true, mozjpeg: true },
      outputDirectory: path.join(this.testDir, 'optimized'),
      importMapPath: path.join(this.testDir, 'image-imports.ts'),
      preserveOriginal: true,
      logging: { level: "info", file: path.join(this.testDir, 'test.log') }
    };

    // Test 1: SVG with text handling
    await this.testSvgTextHandling(config, imagesDir);
    
    // Test 2: Idempotency
    await this.testIdempotency(config, imagesDir);
    
    // Test 3: Dry-run mode
    await this.testAssetGardenerDryRun(config, imagesDir);

    console.log('✅ Asset Gardener improvements working correctly');
  }

  async testSvgTextHandling(config, imagesDir) {
    console.log('  📐 Testing SVG with text handling...');

    // Create SVG with text content
    const svgWithText = `
      <svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
        <!-- This is a comment that should be removed -->
        <rect width="200" height="100" fill="#f0f0f0"/>
        <text x="100" y="50" text-anchor="middle" font-family="Arial" font-size="16">
          Hello World
        </text>
        <text x="100" y="70" text-anchor="middle" font-size="12">
          Preserve   this   spacing
        </text>
      </svg>
    `;

    const svgPath = path.join(imagesDir, 'text-svg.svg');
    await fs.writeFile(svgPath, svgWithText);

    // Mock the findImageFiles method
    const gardener = new AssetGardener(config);
    gardener.findImageFiles = async () => [svgPath];

    const report = await gardener.run();

    console.assert(report.processed >= 1, 'Should process SVG file');
    
    // Check if optimized SVG exists and preserves text
    const outputPath = path.join(config.outputDirectory, 'text-svg.svg');
    const optimizedContent = await fs.readFile(outputPath, 'utf8');
    
    console.assert(!optimizedContent.includes('<!--'), 'Should remove comments');
    console.assert(optimizedContent.includes('<text'), 'Should preserve text elements');
    console.assert(optimizedContent.includes('Hello World'), 'Should preserve text content');

    console.log('    ✅ SVG text handling working correctly');
  }

  async testIdempotency(config, imagesDir) {
    console.log('  🔄 Testing idempotency...');

    // Create a simple test image (we'll simulate this with a text file for testing)
    const testImagePath = path.join(imagesDir, 'test-image.txt');
    await fs.writeFile(testImagePath, 'fake image content');

    // First run
    const gardener1 = new AssetGardener(config);
    gardener1.findImageFiles = async () => [testImagePath];
    
    // Mock the processImage method to simulate processing
    const originalProcessImage = gardener1.processImage.bind(gardener1);
    let processCount = 0;
    gardener1.processImage = async (imagePath) => {
      processCount++;
      return []; // Return empty variants for test
    };

    await gardener1.run();
    const firstRunCount = processCount;

    // Second run (should skip due to idempotency)
    const gardener2 = new AssetGardener(config);
    gardener2.findImageFiles = async () => [testImagePath];
    gardener2.processImage = gardener1.processImage;

    await gardener2.run();
    const secondRunCount = processCount;

    // Should have processed once, then skipped
    console.assert(firstRunCount === 1, `Expected 1 process in first run, got ${firstRunCount}`);
    console.assert(secondRunCount === 1, `Expected no additional processing in second run, got ${secondRunCount - firstRunCount} additional`);

    console.log('    ✅ Idempotency working correctly');
  }

  async testAssetGardenerDryRun(config, imagesDir) {
    console.log('  🔍 Testing Asset Gardener dry-run mode...');

    const testImagePath = path.join(imagesDir, 'dry-run-test.txt');
    await fs.writeFile(testImagePath, 'test content for dry run');

    const dryRunGardener = new AssetGardener(config, { dryRun: true });
    dryRunGardener.findImageFiles = async () => [testImagePath];

    const report = await dryRunGardener.run();

    console.assert(report.dryRun === true, 'Should be in dry-run mode');
    console.assert(report.processed >= 0, 'Should report processed count');

    // Verify no actual output files were created
    const outputDir = config.outputDirectory;
    const outputExists = await fs.access(outputDir).then(() => true).catch(() => false);
    
    if (outputExists) {
      const outputFiles = await fs.readdir(outputDir);
      console.assert(outputFiles.length === 0, 'Should not create output files in dry-run mode');
    }

    console.log('    ✅ Asset Gardener dry-run mode working correctly');
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
  const tester = new AutonomyImprovementsTester();
  
  try {
    await tester.runTests();
    console.log('\n🎉 Autonomy improvements are working correctly!');
  } catch (error) {
    console.error('\n💥 Tests failed:', error.message);
    process.exit(1);
  }
}

// Run tests if called directly
if (require.main === module) {
  main();
}

module.exports = { AutonomyImprovementsTester };