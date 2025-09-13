# Ghostworks Agent Hooks

This directory contains autonomous agent hooks that provide AI-powered automation for the Ghostworks SaaS platform.

## Available Hooks

- **Asset Gardener**: Automatic image optimization and responsive variant generation
- **Release Notes Generator**: Conventional commit parsing and CHANGELOG.md generation

## Asset Gardener Hook

The Asset Gardener is an autonomous image optimization hook that automatically:

- 🖼️ **Optimizes images** when they are added or modified
- 📱 **Generates responsive variants** in multiple formats (WebP, AVIF)
- 📏 **Creates multiple sizes** for different use cases
- 🗺️ **Updates import maps** for easy TypeScript integration
- 🔧 **Provides manual triggers** for on-demand optimization

### Features

#### Automatic Optimization
- Watches for image file changes in configured directories
- Supports JPEG, PNG, GIF, SVG, and WebP formats
- Generates modern formats (WebP, AVIF) for better performance
- Creates responsive variants (thumbnail, small, medium, large, xlarge)

#### Smart Configuration
- Configurable quality settings per format
- Customizable output sizes and formats
- Preserves original files when needed
- Debounced file watching to avoid excessive processing

#### Developer Experience
- TypeScript import map generation
- Utility functions for responsive images
- Comprehensive logging and error reporting
- Performance metrics and optimization reports

### Usage

#### Automatic Triggering
The hook automatically triggers when image files are modified in:
- `apps/web/public/images/**/*`
- `apps/web/src/assets/**/*`
- `docs/images/**/*`

#### Manual Triggering
Use the manual trigger button in the Kiro IDE or run:
```bash
cd hooks
npm run asset-gardener
```

#### Testing
Run the test suite to verify functionality:
```bash
cd hooks
npm run test-asset-gardener
```

### Configuration

The hook is configured via `asset-gardener.json`:

```json
{
  "configuration": {
    "outputFormats": ["webp", "avif", "original"],
    "sizes": [
      { "name": "thumbnail", "width": 150, "height": 150 },
      { "name": "small", "width": 400, "height": null },
      { "name": "medium", "width": 800, "height": null },
      { "name": "large", "width": 1200, "height": null },
      { "name": "xlarge", "width": 1920, "height": null }
    ],
    "quality": {
      "webp": 85,
      "avif": 80,
      "jpeg": 85,
      "png": 95
    }
  }
}
```

### Generated Import Map

The hook generates a TypeScript import map at `apps/web/src/lib/image-imports.ts`:

```typescript
import { getImageVariant, getResponsiveSrcSet } from '@/lib/image-imports';

// Get optimized image URL
const imageUrl = getImageVariant('myImage', 'medium', 'webp');

// Get responsive srcset
const srcSet = getResponsiveSrcSet('myImage', 'webp');
```

### Output Structure

Optimized images are saved to `apps/web/public/optimized/` with the following structure:

```
apps/web/public/optimized/
├── images/
│   ├── hero-thumbnail.webp
│   ├── hero-small.webp
│   ├── hero-medium.webp
│   ├── hero-large.webp
│   └── hero-xlarge.webp
└── icons/
    ├── logo-thumbnail.avif
    └── logo-medium.avif
```

### Performance Benefits

- **Reduced file sizes**: 30-70% smaller files with modern formats
- **Faster loading**: Responsive images load appropriate sizes
- **Better UX**: Progressive loading and format fallbacks
- **SEO friendly**: Optimized images improve page speed scores

### Requirements Satisfied

This implementation satisfies the following requirements:

- **8.2**: Asset Gardener hook optimizes images and generates responsive variants
- **8.5**: Manual trigger capabilities for demonstrating autonomy
- **9.4**: Interactive button to showcase autonomous optimization

### Dependencies

- **sharp**: High-performance image processing
- **glob**: File pattern matching
- **Node.js**: Runtime environment (>=18.0.0)

### Logging

All operations are logged to `hooks/logs/asset-gardener.log` with structured JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "message": "Optimized image",
  "data": {
    "file": "hero.jpg",
    "originalSize": "2.5MB",
    "optimizedSize": "850KB",
    "compression": "66%"
  }
}
```

### Error Handling

The hook includes comprehensive error handling:
- Individual image failures don't stop the batch
- Detailed error logging with stack traces
- Graceful degradation for unsupported formats
- Retry logic for transient failures

### Future Enhancements

Potential improvements for future versions:
- Progressive JPEG optimization
- AVIF format support expansion
- Custom watermarking capabilities
- Integration with CDN services
- Batch processing optimizations
## Rel
ease Notes Generator Hook

The Release Notes Generator is an autonomous hook that automatically:

- 📝 **Parses conventional commits** using standardized format
- 📈 **Calculates semantic versions** based on commit types
- 📋 **Generates CHANGELOG.md** with formatted release notes
- 🏷️ **Supports version tagging** with Git integration
- 🔧 **Provides manual triggers** for on-demand generation

### Features

#### Conventional Commit Parsing
- Supports standard conventional commit format (`type(scope): description`)
- Recognizes commit types: feat, fix, docs, style, refactor, perf, test, chore, build, ci
- Detects breaking changes from commit messages and footers
- Extracts scope information for better organization

#### Semantic Versioning
- **Major**: Breaking changes (BREAKING CHANGE:, feat!)
- **Minor**: New features (feat:)
- **Patch**: Bug fixes, docs, refactoring (fix:, docs:, etc.)
- Configurable versioning strategy and initial version

#### CHANGELOG Generation
- Maintains Keep a Changelog format
- Groups commits by type with emoji headers
- Includes commit authors and scopes
- Optional commit links to repository
- Configurable sections and formatting

#### Git Integration
- Reads commit history since last tag
- Supports version tagging automation
- Handles repositories without existing tags
- Updates package.json version field

### Usage

#### Automatic Triggering
The hook automatically triggers on commits matching conventional format:
- `feat:` - New features
- `fix:` - Bug fixes  
- `docs:` - Documentation changes
- `BREAKING CHANGE:` - Breaking changes

#### Manual Triggering
Use the manual trigger button in the Kiro IDE or run:
```bash
cd hooks
npm run release-notes
```

#### Testing
Run the test suite to verify functionality:
```bash
cd hooks
npm run test-release-notes
```

#### Demo
See examples and documentation:
```bash
cd hooks
npm run demo-release-notes
```

### Configuration

The hook is configured via `release-notes.json`:

```json
{
  "configuration": {
    "conventionalCommits": {
      "types": {
        "feat": { "title": "✨ Features", "semver": "minor" },
        "fix": { "title": "🐛 Bug Fixes", "semver": "patch" }
      }
    },
    "versioning": {
      "strategy": "semantic",
      "initialVersion": "0.1.0",
      "tagPrefix": "v"
    },
    "changelog": {
      "path": "CHANGELOG.md",
      "includeCommitLinks": true,
      "includeAuthors": true
    }
  }
}
```

### Conventional Commit Examples

```bash
# Feature (minor version bump)
git commit -m "feat(auth): add OAuth2 integration"

# Bug fix (patch version bump)  
git commit -m "fix: resolve memory leak in image processing"

# Breaking change (major version bump)
git commit -m "feat!: restructure API endpoints"

# With breaking change footer
git commit -m "feat(api): new authentication system

BREAKING CHANGE: All API endpoints now require authentication headers"

# Documentation (patch version bump)
git commit -m "docs(api): update OpenAPI specification"

# Scoped commits
git commit -m "perf(core): optimize database queries"
git commit -m "test(auth): add integration tests"
```

### Generated CHANGELOG Format

```markdown
# Changelog

## [1.2.0] - 2024-01-15

### ✨ Features

- **auth**: add OAuth2 integration ([abc123](https://github.com/repo/commit/abc123)) by John Doe
- **api**: implement rate limiting middleware ([def456](https://github.com/repo/commit/def456)) by Jane Smith

### 🐛 Bug Fixes

- **auth**: fix password reset email template ([ghi789](https://github.com/repo/commit/ghi789)) by Alice Johnson
- resolve CORS issues in production ([jkl012](https://github.com/repo/commit/jkl012)) by Charlie Brown

### 📚 Documentation

- **api**: update OpenAPI specification ([mno345](https://github.com/repo/commit/mno345)) by Sarah Connor
```

### Version Calculation Logic

| Commit Type | Breaking Change | Version Bump | Example |
|-------------|----------------|--------------|---------|
| `feat:` | No | Minor | 1.0.0 → 1.1.0 |
| `feat!:` | Yes | Major | 1.0.0 → 2.0.0 |
| `fix:` | No | Patch | 1.0.0 → 1.0.1 |
| `docs:` | No | Patch | 1.0.0 → 1.0.1 |
| Any type | `BREAKING CHANGE:` | Major | 1.0.0 → 2.0.0 |

### Git Integration

The hook integrates with Git to:
- Read commit history since last tag
- Parse commit messages and metadata
- Extract author information and dates
- Support repositories with or without existing tags
- Optional automatic tagging and pushing

### Requirements Satisfied

This implementation satisfies the following requirements:

- **8.3**: Release Notes hook compiles conventional commits into CHANGELOG.md
- **8.5**: Manual trigger capabilities for demonstrating autonomy
- **Requirements 8.3**: Conventional commit parsing with regex patterns
- **Requirements 8.3**: CHANGELOG.md generation logic from parsed commits
- **Requirements 8.3**: Version tagging automation based on semantic versioning

### Error Handling

The hook includes comprehensive error handling:
- Graceful handling of repositories without Git history
- Fallback for non-conventional commits
- Detailed error logging with context
- Validation of commit message format
- Safe file operations with backup

### Performance Considerations

- Efficient Git log parsing with limited history
- Debounced triggering to avoid excessive runs
- Incremental changelog updates
- Memory-efficient commit processing
- Configurable commit history limits

### Future Enhancements

Potential improvements for future versions:
- GitHub/GitLab release creation
- Custom commit type definitions
- Multi-repository changelog aggregation
- Release note templates
- Integration with project management tools
- Automated dependency update notes