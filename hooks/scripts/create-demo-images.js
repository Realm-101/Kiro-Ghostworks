#!/usr/bin/env node

/**
 * Create demo images for testing Asset Gardener
 */

const fs = require('fs').promises;
const path = require('path');
const sharp = require('sharp');

async function createDemoImages() {
  console.log('Creating demo images...');
  
  // Ensure directories exist
  await fs.mkdir('apps/web/public/images', { recursive: true });
  await fs.mkdir('apps/web/src/assets', { recursive: true });
  
  // Create a hero image
  await sharp({
    create: {
      width: 1920,
      height: 1080,
      channels: 3,
      background: { r: 59, g: 130, b: 246 } // Blue gradient
    }
  })
  .jpeg({ quality: 90 })
  .toFile('apps/web/public/images/hero-banner.jpg');
  
  // Create a logo placeholder
  await sharp({
    create: {
      width: 400,
      height: 400,
      channels: 4,
      background: { r: 16, g: 185, b: 129, alpha: 1 } // Green
    }
  })
  .png()
  .toFile('apps/web/public/images/logo.png');
  
  // Create a product image
  await sharp({
    create: {
      width: 800,
      height: 600,
      channels: 3,
      background: { r: 239, g: 68, b: 68 } // Red
    }
  })
  .jpeg({ quality: 85 })
  .toFile('apps/web/src/assets/product-showcase.jpg');
  
  // Create an SVG icon
  const svgContent = `
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100" rx="20" fill="#8B5CF6"/>
  <text x="50" y="60" text-anchor="middle" fill="white" font-size="24" font-family="Arial">👻</text>
</svg>`.trim();
  
  await fs.writeFile('apps/web/public/images/ghost-icon.svg', svgContent);
  
  console.log('✅ Demo images created successfully!');
  console.log('Files created:');
  console.log('- apps/web/public/images/hero-banner.jpg');
  console.log('- apps/web/public/images/logo.png');
  console.log('- apps/web/src/assets/product-showcase.jpg');
  console.log('- apps/web/public/images/ghost-icon.svg');
}

createDemoImages().catch(console.error);