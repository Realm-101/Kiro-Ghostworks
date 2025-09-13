#!/usr/bin/env node

/**
 * Release Notes Generator
 * 
 * Automatically generates release notes and CHANGELOG.md from conventional commits
 * with semantic versioning support.
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

class ReleaseNotesGenerator {
  constructor(config, options = {}) {
    this.config = config;
    this.options = {
      dryRun: false,
      verbose: false,
      ...options
    };
    this.workspaceRoot = process.cwd();
    this.changelogPath = path.join(this.workspaceRoot, config.changelog.path);
    this.packageJsonPath = path.join(this.workspaceRoot, 'package.json');
  }

  /**
   * Main execution method
   */
  async generate() {
    try {
      console.log('🚀 Starting Release Notes Generation...');

      // Get commits since last tag
      const commits = await this.getCommitsSinceLastTag();

      if (commits.length === 0) {
        console.log('ℹ️ No new commits found since last release');
        return;
      }

      console.log(`📝 Found ${commits.length} commits to process`);

      // Parse conventional commits
      const parsedCommits = this.parseConventionalCommits(commits);

      // Determine next version
      const currentVersion = await this.getCurrentVersion();
      const nextVersion = this.calculateNextVersion(currentVersion, parsedCommits);

      console.log(`📈 Version bump: ${currentVersion} → ${nextVersion}`);

      // Generate changelog entry
      const changelogEntry = this.generateChangelogEntry(nextVersion, parsedCommits);

      if (this.options.dryRun) {
        console.log('\n🔍 DRY RUN MODE - No files will be modified');
        console.log('📋 Proposed changes:');
        console.log(`   Version: ${currentVersion} → ${nextVersion}`);
        console.log(`   Commits processed: ${commits.length}`);
        console.log(`   Changelog entry:\n${changelogEntry}`);

        return {
          version: nextVersion,
          commitCount: commits.length,
          changelogPath: this.changelogPath,
          dryRun: true,
          proposedChanges: {
            changelogEntry,
            versionBump: `${currentVersion} → ${nextVersion}`
          }
        };
      }

      // Update CHANGELOG.md
      await this.updateChangelog(changelogEntry);

      // Update package.json version
      await this.updatePackageVersion(nextVersion);

      console.log(`✅ Release notes generated successfully for version ${nextVersion}`);

      return {
        version: nextVersion,
        commitCount: commits.length,
        changelogPath: this.changelogPath,
        dryRun: false
      };

    } catch (error) {
      console.error('❌ Error generating release notes:', error.message);
      throw error;
    }
  }

  /**
   * Get commits since the last git tag
   */
  async getCommitsSinceLastTag() {
    try {
      // Get the latest tag
      let lastTag;
      try {
        lastTag = execSync('git describe --tags --abbrev=0', { encoding: 'utf8' }).trim();
      } catch (error) {
        // No tags found, get all commits
        lastTag = null;
        console.log('ℹ️ No previous tags found - processing all commits from repository start');
      }

      // Get commits since last tag (or all commits if no tags)
      // Exclude merge commits and revert commits from semver calculation
      const gitCommand = lastTag
        ? `git log ${lastTag}..HEAD --oneline --no-merges`
        : 'git log --oneline --no-merges';

      const output = execSync(gitCommand, { encoding: 'utf8' }).trim();

      if (!output) {
        return [];
      }

      const commits = output.split('\n').map(line => {
        const [hash, ...messageParts] = line.split(' ');
        const message = messageParts.join(' ');
        return {
          hash: hash,
          message: message,
          fullMessage: this.getFullCommitMessage(hash),
          isRevert: this.isRevertCommit(message),
          isMerge: this.isMergeCommit(hash)
        };
      });

      // Filter out merge commits and mark reverts separately
      return commits.filter(commit => !commit.isMerge);

    } catch (error) {
      console.error('Error getting commits:', error.message);
      return [];
    }
  }

  /**
   * Get full commit message including body and footer
   */
  getFullCommitMessage(hash) {
    try {
      return execSync(`git log -1 --pretty=format:"%B" ${hash}`, { encoding: 'utf8' }).trim();
    } catch (error) {
      return '';
    }
  }

  /**
   * Parse commits according to conventional commit format
   */
  parseConventionalCommits(commits) {
    const conventionalPattern = /^(\w+)(\(.+\))?: (.+)$/;
    const revertPattern = /^revert:\s*(.+)$/i;
    const parsed = [];

    for (const commit of commits) {
      let parsedCommit;

      // Handle revert commits specially
      if (commit.isRevert || revertPattern.test(commit.message)) {
        const revertMatch = commit.message.match(revertPattern);
        const revertedMessage = revertMatch ? revertMatch[1] : commit.message.replace(/^revert:\s*/i, '');

        parsedCommit = {
          hash: commit.hash,
          type: 'revert',
          scope: null,
          description: `revert "${revertedMessage}"`,
          fullMessage: commit.fullMessage,
          isBreaking: false, // Reverts don't count as breaking for semver
          isRevert: true,
          author: this.getCommitAuthor(commit.hash),
          date: this.getCommitDate(commit.hash),
          original: commit.message
        };
      } else {
        // Parse conventional commits
        const match = commit.message.match(conventionalPattern);

        if (match) {
          const [, type, scope, description] = match;
          const scopeClean = scope ? scope.slice(1, -1) : null; // Remove parentheses

          // Check for breaking changes
          const isBreaking = this.hasBreakingChange(commit.fullMessage);

          parsedCommit = {
            hash: commit.hash,
            type: type.toLowerCase(),
            scope: scopeClean,
            description,
            fullMessage: commit.fullMessage,
            isBreaking,
            isRevert: false,
            author: this.getCommitAuthor(commit.hash),
            date: this.getCommitDate(commit.hash),
            original: commit.message
          };
        } else {
          // Non-conventional commit - treat as chore
          parsedCommit = {
            hash: commit.hash,
            type: 'chore',
            scope: null,
            description: commit.message,
            fullMessage: commit.fullMessage,
            isBreaking: false,
            isRevert: false,
            author: this.getCommitAuthor(commit.hash),
            date: this.getCommitDate(commit.hash),
            original: commit.message
          };
        }
      }

      parsed.push(parsedCommit);
    }

    return parsed;
  }

  /**
   * Check if commit contains breaking changes
   */
  hasBreakingChange(fullMessage) {
    const breakingKeywords = this.config.conventionalCommits.breakingChangeKeywords;

    // Check for breaking change keywords in message
    const hasKeyword = breakingKeywords.some(keyword =>
      fullMessage.toLowerCase().includes(keyword.toLowerCase())
    );

    // Check for ! in commit type (e.g., feat!)
    const hasExclamation = /^\w+!(\(.+\))?: /.test(fullMessage);

    return hasKeyword || hasExclamation;
  }

  /**
   * Get commit author
   */
  getCommitAuthor(hash) {
    try {
      return execSync(`git log -1 --pretty=format:"%an" ${hash}`, { encoding: 'utf8' }).trim();
    } catch (error) {
      return 'Unknown';
    }
  }

  /**
   * Get commit date
   */
  getCommitDate(hash) {
    try {
      return execSync(`git log -1 --pretty=format:"%ci" ${hash}`, { encoding: 'utf8' }).trim();
    } catch (error) {
      return new Date().toISOString();
    }
  }

  /**
   * Check if commit is a revert commit
   */
  isRevertCommit(message) {
    return /^revert:/i.test(message) || message.toLowerCase().includes('revert');
  }

  /**
   * Check if commit is a merge commit
   */
  isMergeCommit(hash) {
    try {
      const parents = execSync(`git log -1 --pretty=format:"%P" ${hash}`, { encoding: 'utf8' }).trim();
      return parents.split(' ').length > 1; // Merge commits have multiple parents
    } catch (error) {
      return false;
    }
  }

  /**
   * Get current version from package.json or git tags
   */
  async getCurrentVersion() {
    try {
      // Try to get version from package.json first
      const packageJson = JSON.parse(await fs.readFile(this.packageJsonPath, 'utf8'));
      if (packageJson.version) {
        return packageJson.version;
      }
    } catch (error) {
      // Package.json not found or no version field
    }

    try {
      // Try to get latest git tag
      const latestTag = execSync('git describe --tags --abbrev=0', { encoding: 'utf8' }).trim();
      return latestTag.replace(/^v/, ''); // Remove 'v' prefix if present
    } catch (error) {
      // No tags found
    }

    // Return initial version
    return this.config.versioning.initialVersion;
  }

  /**
   * Calculate next version based on conventional commits
   */
  calculateNextVersion(currentVersion, commits) {
    const [major, minor, patch] = currentVersion.split('.').map(Number);

    // Filter out reverts and noise commits for semver calculation
    const semverCommits = commits.filter(commit =>
      !commit.isRevert &&
      commit.type !== 'chore' &&
      commit.type !== 'docs' &&
      commit.type !== 'style' &&
      commit.type !== 'test'
    );

    let bumpType = 'patch'; // Default to patch

    // Check for breaking changes (major bump)
    // Only count breaking changes from non-revert commits
    if (semverCommits.some(commit => commit.isBreaking)) {
      bumpType = 'major';
    }
    // Check for features (minor bump)
    else if (semverCommits.some(commit =>
      this.config.conventionalCommits.types[commit.type]?.semver === 'minor'
    )) {
      bumpType = 'minor';
    }
    // Check for fixes and other patch-level changes
    else if (semverCommits.some(commit =>
      this.config.conventionalCommits.types[commit.type]?.semver === 'patch'
    )) {
      bumpType = 'patch';
    }
    // If only noise commits (docs, style, test, chore), don't bump version
    else if (semverCommits.length === 0) {
      console.log('ℹ️ Only maintenance commits found - no version bump needed');
      return currentVersion; // No version bump
    }

    switch (bumpType) {
      case 'major':
        return `${major + 1}.0.0`;
      case 'minor':
        return `${major}.${minor + 1}.0`;
      case 'patch':
      default:
        return `${major}.${minor}.${patch + 1}`;
    }
  }

  /**
   * Generate changelog entry for the new version
   */
  generateChangelogEntry(version, commits) {
    const date = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
    const config = this.config.changelog;

    let entry = `## [${version}] - ${date}\n\n`;

    // Group commits by type
    const groupedCommits = this.groupCommitsByType(commits);

    // Add breaking changes first if any
    const breakingChanges = commits.filter(commit => commit.isBreaking);
    if (breakingChanges.length > 0) {
      entry += `### 💥 BREAKING CHANGES\n\n`;
      for (const commit of breakingChanges) {
        entry += this.formatCommitEntry(commit, config);
      }
      entry += '\n';
    }

    // Add other commit types
    for (const [type, typeCommits] of Object.entries(groupedCommits)) {
      if (type === 'breaking') continue; // Already handled above

      const typeConfig = this.config.conventionalCommits.types[type];
      if (!typeConfig || typeCommits.length === 0) continue;

      entry += `### ${typeConfig.title}\n\n`;

      for (const commit of typeCommits) {
        entry += this.formatCommitEntry(commit, config);
      }
      entry += '\n';
    }

    return entry;
  }

  /**
   * Group commits by their type
   */
  groupCommitsByType(commits) {
    const grouped = {};

    for (const commit of commits) {
      if (commit.isBreaking) {
        if (!grouped.breaking) grouped.breaking = [];
        grouped.breaking.push(commit);
      } else {
        if (!grouped[commit.type]) grouped[commit.type] = [];
        grouped[commit.type].push(commit);
      }
    }

    return grouped;
  }

  /**
   * Format individual commit entry
   */
  formatCommitEntry(commit, config) {
    let entry = `- `;

    // Add scope if present and configured
    if (commit.scope && config.sections.includeScope) {
      entry += `**${commit.scope}**: `;
    }

    // Add description
    entry += commit.description;

    // Add commit link if configured
    if (config.includeCommitLinks && config.repositoryUrl) {
      entry += ` ([${commit.hash.substring(0, 7)}](${config.repositoryUrl}/commit/${commit.hash}))`;
    }

    // Add author if configured
    if (config.sections.includeAuthors) {
      entry += ` by ${commit.author}`;
    }

    entry += '\n';

    return entry;
  }

  /**
   * Update CHANGELOG.md file
   */
  async updateChangelog(newEntry) {
    if (this.options.dryRun) {
      console.log('🔍 DRY RUN: Would update CHANGELOG.md');
      return;
    }

    let existingContent = '';

    try {
      existingContent = await fs.readFile(this.changelogPath, 'utf8');
    } catch (error) {
      // File doesn't exist, create header
      existingContent = `# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),\nand this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n`;
    }

    // Find where to insert the new entry
    const lines = existingContent.split('\n');
    const insertIndex = this.findInsertionPoint(lines);

    // Insert new entry
    const newLines = [
      ...lines.slice(0, insertIndex),
      newEntry,
      ...lines.slice(insertIndex)
    ];

    const updatedContent = newLines.join('\n');
    await fs.writeFile(this.changelogPath, updatedContent, 'utf8');

    console.log(`📝 Updated ${this.changelogPath}`);
  }

  /**
   * Find the correct insertion point in the changelog
   */
  findInsertionPoint(lines) {
    // Look for the first ## heading after the main title
    let foundTitle = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      if (line.startsWith('# ')) {
        foundTitle = true;
        continue;
      }

      if (foundTitle && line.startsWith('## ')) {
        return i;
      }
    }

    // If no existing entries, add after the header
    return lines.length;
  }

  /**
   * Update package.json version
   */
  async updatePackageVersion(newVersion) {
    if (this.options.dryRun) {
      console.log('🔍 DRY RUN: Would update package.json version to', newVersion);
      return;
    }

    try {
      const packageJson = JSON.parse(await fs.readFile(this.packageJsonPath, 'utf8'));
      packageJson.version = newVersion;

      await fs.writeFile(
        this.packageJsonPath,
        JSON.stringify(packageJson, null, 2) + '\n',
        'utf8'
      );

      console.log(`📦 Updated package.json version to ${newVersion}`);
    } catch (error) {
      console.warn('⚠️ Could not update package.json version:', error.message);
    }
  }
}

/**
 * Main execution
 */
async function main() {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    const options = {
      dryRun: args.includes('--dry-run') || args.includes('-d'),
      verbose: args.includes('--verbose') || args.includes('-v'),
      help: args.includes('--help') || args.includes('-h')
    };

    if (options.help) {
      console.log(`
Release Notes Generator

Usage: node release-notes.js [options]

Options:
  --dry-run, -d    Show proposed changes without modifying files
  --verbose, -v    Enable verbose output
  --help, -h       Show this help message

Examples:
  node release-notes.js                    # Generate release notes
  node release-notes.js --dry-run          # Preview changes without writing
  node release-notes.js --dry-run --verbose # Preview with detailed output
      `);
      return;
    }

    // Load configuration
    const configPath = path.join(__dirname, '..', 'release-notes.json');
    const config = JSON.parse(await fs.readFile(configPath, 'utf8'));

    // Create generator instance with options
    const generator = new ReleaseNotesGenerator(config.configuration, options);

    // Generate release notes
    const result = await generator.generate();

    // Output result for hook system
    if (result) {
      const output = {
        success: true,
        version: result.version,
        commitCount: result.commitCount,
        changelogPath: result.changelogPath,
        dryRun: result.dryRun || false
      };

      if (result.dryRun) {
        output.proposedChanges = result.proposedChanges;
      }

      console.log(JSON.stringify(output, null, options.verbose ? 2 : 0));
    }

  } catch (error) {
    console.error('❌ Release Notes Generation Failed:', error.message);
    if (options && options.verbose) {
      console.error(error.stack);
    }
    console.log(JSON.stringify({
      success: false,
      error: error.message
    }));
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { ReleaseNotesGenerator };