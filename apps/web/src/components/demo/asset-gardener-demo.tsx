'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { getImageVariant, getResponsiveSrcSet, optimizedImages } from '@/lib/image-imports';

export const AssetGardenerDemo: React.FC = () => {
  const [selectedImage, setSelectedImage] = useState<string>('logo');
  const [selectedSize, setSelectedSize] = useState<'thumbnail' | 'small' | 'medium' | 'large' | 'xlarge'>('medium');
  const [selectedFormat, setSelectedFormat] = useState<'webp' | 'avif' | 'original'>('webp');

  const imageKeys = Object.keys(optimizedImages);
  const sizes = ['thumbnail', 'small', 'medium', 'large', 'xlarge'] as const;
  const formats = ['webp', 'avif', 'original'] as const;

  const currentImageUrl = getImageVariant(selectedImage, selectedSize, selectedFormat);
  const responsiveSrcSet = getResponsiveSrcSet(selectedImage, selectedFormat);

  const triggerAssetGardener = async () => {
    try {
      // In a real implementation, this would trigger the hook via the Kiro API
      alert('🌱 Asset Gardener would be triggered here!\n\nThis would:\n- Scan for new/modified images\n- Generate responsive variants\n- Update the import map\n- Optimize for web delivery');
    } catch (error) {
      console.error('Failed to trigger Asset Gardener:', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          🌱 Asset Gardener Demo
        </h2>
        <p className="text-lg text-gray-600 mb-6">
          Autonomous image optimization with responsive variants
        </p>
        
        <button
          onClick={triggerAssetGardener}
          className="bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg shadow-md transition-colors duration-200 flex items-center gap-2 mx-auto"
        >
          <span>🌱</span>
          Trigger Asset Gardener
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Controls */}
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Image
            </label>
            <select
              value={selectedImage}
              onChange={(e) => setSelectedImage(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              {imageKeys.map((key) => (
                <option key={key} value={key}>
                  {key} ({optimizedImages[key].metadata.baseName})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Size Variant
            </label>
            <select
              value={selectedSize}
              onChange={(e) => setSelectedSize(e.target.value as typeof selectedSize)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              {sizes.map((size) => (
                <option key={size} value={size}>
                  {size.charAt(0).toUpperCase() + size.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Format
            </label>
            <select
              value={selectedFormat}
              onChange={(e) => setSelectedFormat(e.target.value as typeof selectedFormat)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-transparent"
            >
              {formats.map((format) => (
                <option key={format} value={format}>
                  {format.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Image Info */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Image Info</h3>
            <div className="space-y-1 text-sm text-gray-600">
              <p><strong>Original:</strong> {optimizedImages[selectedImage]?.metadata.relativePath}</p>
              <p><strong>Optimized URL:</strong> {currentImageUrl || 'Not available'}</p>
              <p><strong>Responsive SrcSet:</strong></p>
              <code className="block bg-white p-2 rounded text-xs break-all">
                {responsiveSrcSet || 'Not available'}
              </code>
            </div>
          </div>
        </div>

        {/* Image Preview */}
        <div className="space-y-6">
          <div className="bg-gray-100 rounded-lg p-6 text-center">
            <h3 className="font-semibold text-gray-900 mb-4">Preview</h3>
            {currentImageUrl ? (
              <div className="space-y-4">
                <Image
                  src={currentImageUrl}
                  alt={`${selectedImage} - ${selectedSize} - ${selectedFormat}`}
                  className="max-w-full h-auto mx-auto rounded-lg shadow-md"
                  style={{ maxHeight: '300px' }}
                  width={300}
                  height={300}
                />
                <p className="text-sm text-gray-600">
                  {selectedSize} variant in {selectedFormat.toUpperCase()} format
                </p>
              </div>
            ) : (
              <div className="text-gray-500 py-12">
                <p>Image variant not available</p>
                <p className="text-sm mt-2">
                  Try a different format or size
                </p>
              </div>
            )}
          </div>

          {/* Available Variants */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold text-gray-900 mb-2">Available Variants</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {sizes.map((size) => (
                <div key={size} className="space-y-1">
                  <p className="font-medium text-gray-700">{size}:</p>
                  {formats.map((format) => {
                    const url = getImageVariant(selectedImage, size, format);
                    return (
                      <p key={format} className={url ? 'text-green-600' : 'text-gray-400'}>
                        {format}: {url ? '✓' : '✗'}
                      </p>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">
          Asset Gardener Features
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">🖼️ Format Optimization</h4>
            <p className="text-sm text-gray-600">
              Automatically generates WebP and AVIF variants for better compression
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">📱 Responsive Variants</h4>
            <p className="text-sm text-gray-600">
              Creates multiple sizes (thumbnail, small, medium, large, xlarge)
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">🗺️ TypeScript Integration</h4>
            <p className="text-sm text-gray-600">
              Generates typed import maps for easy developer experience
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">⚡ Automatic Triggers</h4>
            <p className="text-sm text-gray-600">
              Watches for file changes and optimizes images automatically
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">🔧 Manual Control</h4>
            <p className="text-sm text-gray-600">
              Provides manual trigger buttons for on-demand optimization
            </p>
          </div>
          <div className="space-y-2">
            <h4 className="font-medium text-gray-900">📊 Performance Metrics</h4>
            <p className="text-sm text-gray-600">
              Reports compression ratios and optimization statistics
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};