#!/usr/bin/env node

/**
 * Asset Gardener - Autonomous Image Optimization Hook
 * 
 * This script automatically optimizes images and generates responsive variants
 * when triggered by file changes or manual execution.
 */

const fs = require('fs').promises;
const path = require('path');
const sharp = require('sharp');
const { glob } = require('glob');

class AssetGardener {
  constructor(config) {
    this.config = config;
    this.stats = {
      processed: 0,
      optimized: 0,
      errors: 0,
      originalSize: 0,
      optimizedSize: 0,
      startTime: Date.now()
    };
    this.logger = new Logger(config.logging);
  }

  /**
   * Main execution method
   */
  async run() {
    try {
      this.logger.info('🌱 Asset Gardener starting image optimization...');
      
      // Ensure output directory exists
      await this.ensureDirectoryExists(this.config.outputDirectory);
      
      // Find all images to process
      const imageFiles = await this.findImageFiles();
      this.logger.info(`Found ${imageFiles.length} image files to process`);
      
      if (imageFiles.length === 0) {
        this.logger.info('No images found to optimize');
        return this.generateReport();
      }
      
      // Process images in batches to avoid memory issues
      const batchSize = 5;
      for (let i = 0; i < imageFiles.length; i += batchSize) {
        const batch = imageFiles.slice(i, i + batchSize);
        await Promise.all(batch.map(file => this.processImage(file)));
      }
      
      // Update import map
      await this.updateImportMap(imageFiles);
      
      // Generate and log report
      const report = this.generateReport();
      this.logger.info('✅ Asset Gardener completed successfully', report);
      
      return report;
      
    } catch (error) {
      this.logger.error('❌ Asset Gardener failed:', error);
      throw error;
    }
  }

  /**
   * Find all image files matching the configured patterns
   */
  async findImageFiles() {
    // Get the workspace root (parent of hooks directory)
    const workspaceRoot = path.resolve(__dirname, '..', '..');
    const patterns = [
      `${workspaceRoot}/apps/web/public/images/**/*.{jpg,jpeg,png,gif,webp,svg}`,
      `${workspaceRoot}/apps/web/src/assets/**/*.{jpg,jpeg,png,gif,webp,svg}`,
      `${workspaceRoot}/docs/images/**/*.{jpg,jpeg,png,gif,webp,svg}`
    ];
    
    const allFiles = [];
    for (const pattern of patterns) {
      try {
        const files = await glob(pattern, { nodir: true });
        allFiles.push(...files);
      } catch (error) {
        this.logger.warn(`Failed to glob pattern ${pattern}:`, error.message);
      }
    }
    
    // Remove duplicates and filter existing files
    const uniqueFiles = [...new Set(allFiles)];
    const existingFiles = [];
    
    for (const file of uniqueFiles) {
      try {
        await fs.access(file);
        existingFiles.push(file);
      } catch {
        // File doesn't exist, skip
      }
    }
    
    return existingFiles;
  }

  /**
   * Process a single image file
   */
  async processImage(imagePath) {
    try {
      this.stats.processed++;
      this.logger.debug(`Processing: ${imagePath}`);
      
      // Get original file stats
      const originalStats = await fs.stat(imagePath);
      this.stats.originalSize += originalStats.size;
      
      // Load image with sharp
      const image = sharp(imagePath);
      const metadata = await image.metadata();
      
      // Skip SVG files (handle them separately)
      if (metadata.format === 'svg') {
        return this.processSvg(imagePath);
      }
      
      // Generate optimized variants
      const variants = await this.generateVariants(image, imagePath, metadata);
      
      // Calculate total optimized size
      let totalOptimizedSize = 0;
      for (const variant of variants) {
        try {
          const stats = await fs.stat(variant.outputPath);
          totalOptimizedSize += stats.size;
        } catch {
          // File might not exist if optimization failed
        }
      }
      
      this.stats.optimizedSize += totalOptimizedSize;
      this.stats.optimized++;
      
      this.logger.debug(`✅ Optimized: ${imagePath} (${this.formatBytes(originalStats.size)} → ${this.formatBytes(totalOptimizedSize)})`);
      
      return variants;
      
    } catch (error) {
      this.stats.errors++;
      this.logger.error(`❌ Failed to process ${imagePath}:`, error.message);
      return [];
    }
  }

  /**
   * Generate responsive variants for an image
   */
  async generateVariants(image, originalPath, metadata) {
    const variants = [];
    const baseName = path.parse(originalPath).name;
    const relativePath = path.relative(process.cwd(), originalPath);
    
    // Generate size variants
    for (const size of this.config.sizes) {
      for (const format of this.config.outputFormats) {
        if (format === 'original') continue;
        
        try {
          const outputPath = this.getOutputPath(relativePath, baseName, size.name, format);
          await this.ensureDirectoryExists(path.dirname(outputPath));
          
          let pipeline = image.clone();
          
          // Resize if dimensions specified
          if (size.width || size.height) {
            pipeline = pipeline.resize(size.width, size.height, {
              fit: 'inside',
              withoutEnlargement: true
            });
          }
          
          // Apply format-specific optimizations
          pipeline = this.applyFormatOptimizations(pipeline, format);
          
          // Save the variant
          await pipeline.toFile(outputPath);
          
          variants.push({
            size: size.name,
            format,
            outputPath,
            width: size.width,
            height: size.height
          });
          
        } catch (error) {
          this.logger.warn(`Failed to generate ${size.name} ${format} variant for ${originalPath}:`, error.message);
        }
      }
    }
    
    // Preserve original if configured
    if (this.config.preserveOriginal) {
      const originalOutputPath = this.getOutputPath(relativePath, baseName, 'original', metadata.format);
      await this.ensureDirectoryExists(path.dirname(originalOutputPath));
      
      try {
        // Copy original with potential optimization
        let pipeline = image.clone();
        pipeline = this.applyFormatOptimizations(pipeline, metadata.format);
        await pipeline.toFile(originalOutputPath);
        
        variants.push({
          size: 'original',
          format: metadata.format,
          outputPath: originalOutputPath,
          width: metadata.width,
          height: metadata.height
        });
      } catch (error) {
        this.logger.warn(`Failed to preserve original for ${originalPath}:`, error.message);
      }
    }
    
    return variants;
  }

  /**
   * Apply format-specific optimizations
   */
  applyFormatOptimizations(pipeline, format) {
    const quality = this.config.quality;
    
    switch (format) {
      case 'webp':
        return pipeline.webp({ 
          quality: quality.webp,
          effort: 6
        });
        
      case 'avif':
        return pipeline.avif({ 
          quality: quality.avif,
          effort: 9
        });
        
      case 'jpeg':
      case 'jpg':
        return pipeline.jpeg({ 
          quality: quality.jpeg,
          progressive: this.config.optimization.progressive,
          mozjpeg: this.config.optimization.mozjpeg
        });
        
      case 'png':
        return pipeline.png({ 
          quality: quality.png,
          compressionLevel: 9,
          progressive: this.config.optimization.progressive
        });
        
      default:
        return pipeline;
    }
  }

  /**
   * Process SVG files (basic optimization)
   */
  async processSvg(svgPath) {
    try {
      const content = await fs.readFile(svgPath, 'utf8');
      const baseName = path.parse(svgPath).name;
      const relativePath = path.relative(process.cwd(), svgPath);
      const outputPath = this.getOutputPath(relativePath, baseName, 'original', 'svg');
      
      await this.ensureDirectoryExists(path.dirname(outputPath));
      
      // Basic SVG optimization (remove comments, extra whitespace)
      const optimized = content
        .replace(/<!--[\s\S]*?-->/g, '') // Remove comments
        .replace(/\s+/g, ' ') // Normalize whitespace
        .trim();
      
      await fs.writeFile(outputPath, optimized);
      
      return [{
        size: 'original',
        format: 'svg',
        outputPath,
        width: null,
        height: null
      }];
      
    } catch (error) {
      this.logger.error(`Failed to process SVG ${svgPath}:`, error.message);
      return [];
    }
  }

  /**
   * Generate output path for optimized image
   */
  getOutputPath(relativePath, baseName, sizeName, format) {
    // Get workspace root
    const workspaceRoot = path.resolve(__dirname, '..', '..');
    
    // Determine the subdirectory based on the original image location
    let subDir = '';
    if (relativePath.includes('public/images')) {
      subDir = 'images';
    } else if (relativePath.includes('src/assets')) {
      subDir = 'assets';
    } else if (relativePath.includes('docs/images')) {
      subDir = 'docs';
    }
    
    let filename;
    if (sizeName === 'original') {
      filename = `${baseName}.${format}`;
    } else {
      filename = `${baseName}-${sizeName}.${format}`;
    }
    
    // Make output directory relative to workspace root
    const outputDir = path.resolve(workspaceRoot, this.config.outputDirectory);
    return path.join(outputDir, subDir, filename);
  }

  /**
   * Update the import map with optimized image paths
   */
  async updateImportMap(imageFiles) {
    try {
      this.logger.info('Updating import map...');
      
      const imports = {};
      
      // Process each image file to generate import entries
      const workspaceRootPath = path.resolve(__dirname, '..', '..');
      for (const imagePath of imageFiles) {
        const baseName = path.parse(imagePath).name;
        const relativePath = path.relative(workspaceRootPath, imagePath);
        
        // Generate import key (convert path to camelCase identifier)
        const importKey = this.pathToImportKey(relativePath);
        
        // Find all variants for this image
        const variants = {};
        
        for (const size of this.config.sizes) {
          variants[size.name] = {};
          
          for (const format of this.config.outputFormats) {
            const outputPath = this.getOutputPath(relativePath, baseName, size.name, format);
            const workspaceRootForWeb = path.resolve(__dirname, '..', '..');
            const webPublicPath = path.join(workspaceRootForWeb, 'apps/web/public');
            const webPath = '/' + path.relative(webPublicPath, outputPath).replace(/\\/g, '/');
            
            try {
              await fs.access(outputPath);
              variants[size.name][format] = webPath;
            } catch {
              // Variant doesn't exist, skip
            }
          }
        }
        
        imports[importKey] = {
          original: relativePath,
          variants,
          metadata: {
            baseName,
            relativePath
          }
        };
      }
      
      // Generate TypeScript import map
      const importMapContent = this.generateImportMapContent(imports);
      
      // Ensure directory exists
      const workspaceRootForImport = path.resolve(__dirname, '..', '..');
      const importMapPath = path.resolve(workspaceRootForImport, this.config.importMapPath);
      await this.ensureDirectoryExists(path.dirname(importMapPath));
      
      // Write import map
      await fs.writeFile(importMapPath, importMapContent);
      
      this.logger.info(`✅ Updated import map with ${Object.keys(imports).length} images`);
      
    } catch (error) {
      this.logger.error('Failed to update import map:', error);
    }
  }

  /**
   * Convert file path to camelCase import key
   */
  pathToImportKey(filePath) {
    return path.parse(filePath).name
      .replace(/[^a-zA-Z0-9]/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '')
      .replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
  }

  /**
   * Generate TypeScript import map content
   */
  generateImportMapContent(imports) {
    const timestamp = new Date().toISOString();
    
    return `/**
 * Auto-generated image import map
 * Generated by Asset Gardener on ${timestamp}
 * 
 * This file provides optimized image variants for responsive loading.
 * Do not edit manually - it will be overwritten on next optimization.
 */

export interface ImageVariant {
  original?: string;
  webp?: string;
  avif?: string;
}

export interface ImageVariants {
  thumbnail: ImageVariant;
  small: ImageVariant;
  medium: ImageVariant;
  large: ImageVariant;
  xlarge: ImageVariant;
  original: ImageVariant;
}

export interface OptimizedImage {
  original: string;
  variants: ImageVariants;
  metadata: {
    baseName: string;
    relativePath: string;
  };
}

export const optimizedImages: Record<string, OptimizedImage> = ${JSON.stringify(imports, null, 2)};

/**
 * Get the best image variant for a given size and format preference
 */
export function getImageVariant(
  imageKey: string, 
  size: keyof ImageVariants = 'medium',
  preferredFormat: 'webp' | 'avif' | 'original' = 'webp'
): string | undefined {
  const image = optimizedImages[imageKey];
  if (!image) return undefined;
  
  const variant = image.variants[size];
  if (!variant) return undefined;
  
  // Try preferred format first, then fallback to available formats
  return variant[preferredFormat] || 
         variant.webp || 
         variant.avif || 
         variant.original;
}

/**
 * Get all available sizes for an image
 */
export function getImageSizes(imageKey: string): Array<keyof ImageVariants> {
  const image = optimizedImages[imageKey];
  if (!image) return [];
  
  return Object.keys(image.variants) as Array<keyof ImageVariants>;
}

/**
 * Get responsive srcset for an image
 */
export function getResponsiveSrcSet(
  imageKey: string,
  format: 'webp' | 'avif' | 'original' = 'webp'
): string {
  const image = optimizedImages[imageKey];
  if (!image) return '';
  
  const srcsetEntries: string[] = [];
  
  Object.entries(image.variants).forEach(([size, variant]) => {
    const url = variant[format] || variant.webp || variant.original;
    if (url && size !== 'original') {
      // Map size names to approximate widths for srcset
      const widthMap: Record<string, number> = {
        thumbnail: 150,
        small: 400,
        medium: 800,
        large: 1200,
        xlarge: 1920
      };
      
      const width = widthMap[size];
      if (width) {
        srcsetEntries.push(\`\${url} \${width}w\`);
      }
    }
  });
  
  return srcsetEntries.join(', ');
}
`;
  }

  /**
   * Ensure directory exists
   */
  async ensureDirectoryExists(dirPath) {
    try {
      await fs.mkdir(dirPath, { recursive: true });
    } catch (error) {
      if (error.code !== 'EEXIST') {
        throw error;
      }
    }
  }

  /**
   * Format bytes to human readable string
   */
  formatBytes(bytes) {
    if (bytes === 0 || isNaN(bytes)) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(Math.abs(bytes)) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Generate optimization report
   */
  generateReport() {
    const duration = Date.now() - this.stats.startTime;
    const savedBytes = this.stats.originalSize - this.stats.optimizedSize;
    const compressionRatio = this.stats.originalSize > 0 
      ? ((savedBytes / this.stats.originalSize) * 100).toFixed(1)
      : '0';
    
    return {
      processed: this.stats.processed,
      optimized: this.stats.optimized,
      errors: this.stats.errors,
      duration: `${(duration / 1000).toFixed(2)}s`,
      originalSize: this.formatBytes(this.stats.originalSize),
      optimizedSize: this.formatBytes(this.stats.optimizedSize),
      savedBytes: this.formatBytes(savedBytes),
      compressionRatio: `${compressionRatio}%`,
      note: savedBytes < 0 ? 'Size increased due to multiple format variants generated' : 'Size reduced through optimization'
    };
  }
}

/**
 * Simple logger class
 */
class Logger {
  constructor(config) {
    this.config = config;
    this.logFile = config.file;
  }

  async log(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      data
    };
    
    // Console output
    const consoleMessage = `[${timestamp}] ${level.toUpperCase()}: ${message}`;
    console.log(consoleMessage, data ? JSON.stringify(data, null, 2) : '');
    
    // File output
    if (this.logFile) {
      try {
        await fs.mkdir(path.dirname(this.logFile), { recursive: true });
        await fs.appendFile(this.logFile, JSON.stringify(logEntry) + '\n');
      } catch (error) {
        console.error('Failed to write to log file:', error.message);
      }
    }
  }

  info(message, data) { return this.log('info', message, data); }
  warn(message, data) { return this.log('warn', message, data); }
  error(message, data) { return this.log('error', message, data); }
  debug(message, data) { return this.log('debug', message, data); }
}

/**
 * Main execution
 */
async function main() {
  try {
    // Load configuration
    const configPath = path.join(__dirname, '..', 'asset-gardener.json');
    const configContent = await fs.readFile(configPath, 'utf8');
    const fullConfig = JSON.parse(configContent);
    const config = {
      ...fullConfig.configuration,
      logging: fullConfig.logging || {
        level: "info",
        file: "hooks/logs/asset-gardener.log"
      }
    };
    
    // Create and run Asset Gardener
    const gardener = new AssetGardener(config);
    const report = await gardener.run();
    
    // Output report for hook system
    console.log('\n🌱 ASSET GARDENER REPORT:');
    console.log(JSON.stringify(report, null, 2));
    
    process.exit(0);
    
  } catch (error) {
    console.error('❌ Asset Gardener failed:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { AssetGardener };