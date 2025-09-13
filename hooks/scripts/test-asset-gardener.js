#!/usr/bin/env node

/**
 * Test script for Asset Gardener
 * Creates sample images and tests the optimization pipeline
 */

const fs = require('fs').promises;
const path = require('path');
const sharp = require('sharp');
const { AssetGardener } = require('./asset-gardener');

class AssetGardenerTester {
  constructor() {
    this.testDir = path.join(__dirname, '..', 'test-images');
    this.outputDir = path.join(__dirname, '..', 'test-output');
  }

  async run() {
    console.log('🧪 Starting Asset Gardener test suite...');
    
    try {
      // Setup test environment
      await this.setupTestEnvironment();
      
      // Create sample images
      await this.createSampleImages();
      
      // Test the Asset Gardener
      await this.testAssetGardener();
      
      // Verify results
      await this.verifyResults();
      
      console.log('✅ All tests passed!');
      
    } catch (error) {
      console.error('❌ Test failed:', error.message);
      throw error;
    } finally {
      // Cleanup
      await this.cleanup();
    }
  }

  async setupTestEnvironment() {
    console.log('Setting up test environment...');
    
    // Create test directories
    await fs.mkdir(this.testDir, { recursive: true });
    await fs.mkdir(this.outputDir, { recursive: true });
    
    // Create test config
    const testConfig = {
      outputFormats: ["webp", "original"],
      sizes: [
        { "name": "thumbnail", "width": 150, "height": 150 },
        { "name": "medium", "width": 800, "height": null }
      ],
      quality: {
        webp: 85,
        jpeg: 85,
        png: 95
      },
      optimization: {
        progressive: true,
        mozjpeg: true,
        pngquant: true
      },
      outputDirectory: this.outputDir,
      importMapPath: path.join(this.outputDir, 'test-imports.ts'),
      preserveOriginal: true,
      logging: {
        level: "info",
        file: path.join(this.outputDir, 'test.log')
      }
    };
    
    this.config = testConfig;
  }

  async createSampleImages() {
    console.log('Creating sample images...');
    
    // Create a test JPEG
    await sharp({
      create: {
        width: 1200,
        height: 800,
        channels: 3,
        background: { r: 100, g: 150, b: 200 }
      }
    })
    .jpeg()
    .toFile(path.join(this.testDir, 'sample-photo.jpg'));
    
    // Create a test PNG with transparency
    await sharp({
      create: {
        width: 600,
        height: 400,
        channels: 4,
        background: { r: 255, g: 100, b: 100, alpha: 0.8 }
      }
    })
    .png()
    .toFile(path.join(this.testDir, 'sample-graphic.png'));
    
    // Create a simple SVG
    const svgContent = `
      <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="80" fill="#4CAF50"/>
        <text x="100" y="110" text-anchor="middle" fill="white" font-size="20">Test</text>
      </svg>
    `;
    
    await fs.writeFile(path.join(this.testDir, 'sample-icon.svg'), svgContent.trim());
    
    console.log('✅ Sample images created');
  }

  async testAssetGardener() {
    console.log('Testing Asset Gardener...');
    
    // Override the findImageFiles method to use our test images
    const gardener = new AssetGardener(this.config);
    
    // Mock the findImageFiles method
    gardener.findImageFiles = async () => {
      const files = await fs.readdir(this.testDir);
      return files.map(file => path.join(this.testDir, file));
    };
    
    // Run the optimization
    const report = await gardener.run();
    
    console.log('Optimization report:', report);
    this.report = report;
  }

  async verifyResults() {
    console.log('Verifying results...');
    
    // Check if output directory has optimized images
    const outputFiles = await fs.readdir(this.outputDir, { recursive: true });
    console.log('Output files:', outputFiles);
    
    // Verify we have WebP variants
    const webpFiles = outputFiles.filter(file => file.endsWith('.webp'));
    if (webpFiles.length === 0) {
      throw new Error('No WebP files generated');
    }
    
    // Verify import map was created
    const importMapPath = path.join(this.outputDir, 'test-imports.ts');
    try {
      await fs.access(importMapPath);
      console.log('✅ Import map created');
    } catch {
      throw new Error('Import map not created');
    }
    
    // Verify log file
    const logPath = path.join(this.outputDir, 'test.log');
    try {
      const logContent = await fs.readFile(logPath, 'utf8');
      if (logContent.length === 0) {
        throw new Error('Log file is empty');
      }
      console.log('✅ Log file created with content');
    } catch {
      throw new Error('Log file not created');
    }
    
    console.log('✅ All verifications passed');
  }

  async cleanup() {
    console.log('Cleaning up test files...');
    
    try {
      await fs.rm(this.testDir, { recursive: true, force: true });
      await fs.rm(this.outputDir, { recursive: true, force: true });
      console.log('✅ Cleanup completed');
    } catch (error) {
      console.warn('⚠️ Cleanup failed:', error.message);
    }
  }
}

// Run test if called directly
if (require.main === module) {
  const tester = new AssetGardenerTester();
  tester.run()
    .then(() => {
      console.log('🎉 Asset Gardener test completed successfully!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('💥 Asset Gardener test failed:', error);
      process.exit(1);
    });
}

module.exports = { AssetGardenerTester };