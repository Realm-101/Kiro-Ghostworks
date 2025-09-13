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
  constructor(config) {
    this.config = config;
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
      
      // Update CHANGELOG.md
      await this.updateChangelog(changelogEntry);
      
      // Update package.json version
      await this.updatePackageVersion(nextVersion);
      
      console.log(`✅ Release notes generated successfully for version ${nextVersion}`);
      
      return {
        version: nextVersion,
        commitCount: commits.length,
        changelogPath: this.changelogPath
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
      }

      // Get commits since last tag (or all commits if no tags)
      const gitCommand = lastTag 
        ? `git log ${lastTag}..HEAD --oneline --no-merges`
        : 'git log --oneline --no-merges';
      
      const output = execSync(gitCommand, { encoding: 'utf8' }).trim();
      
      if (!output) {
        return [];
      }

      return output.split('\n').map(line => {
        const [hash, ...messageParts] = line.split(' ');
        return {
          hash: hash,
          message: messageParts.join(' '),
          fullMessage: this.getFullCommitMessage(hash)
        };
      });
      
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
    const parsed = [];

    for (const commit of commits) {
      const match = commit.message.match(conventionalPattern);
      
      if (match) {
        const [, type, scope, description] = match;
        const scopeClean = scope ? scope.slice(1, -1) : null; // Remove parentheses
        
        // Check for breaking changes
        const isBreaking = this.hasBreakingChange(commit.fullMessage);
        
        // Get commit author and date
        const author = this.getCommitAuthor(commit.hash);
        const date = this.getCommitDate(commit.hash);
        
        parsed.push({
          hash: commit.hash,
          type: type.toLowerCase(),
          scope: scopeClean,
          description,
          fullMessage: commit.fullMessage,
          isBreaking,
          author,
          date,
          original: commit.message
        });
      } else {
        // Non-conventional commit - treat as chore
        parsed.push({
          hash: commit.hash,
          type: 'chore',
          scope: null,
          description: commit.message,
          fullMessage: commit.fullMessage,
          isBreaking: false,
          author: this.getCommitAuthor(commit.hash),
          date: this.getCommitDate(commit.hash),
          original: commit.message
        });
      }
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
    
    let bumpType = 'patch'; // Default to patch
    
    // Check for breaking changes (major bump)
    if (commits.some(commit => commit.isBreaking)) {
      bumpType = 'major';
    }
    // Check for features (minor bump)
    else if (commits.some(commit => 
      this.config.conventionalCommits.types[commit.type]?.semver === 'minor'
    )) {
      bumpType = 'minor';
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
    // Load configuration
    const configPath = path.join(__dirname, '..', 'release-notes.json');
    const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
    
    // Create generator instance
    const generator = new ReleaseNotesGenerator(config.configuration);
    
    // Generate release notes
    const result = await generator.generate();
    
    // Output result for hook system
    if (result) {
      console.log(JSON.stringify({
        success: true,
        version: result.version,
        commitCount: result.commitCount,
        changelogPath: result.changelogPath
      }));
    }
    
  } catch (error) {
    console.error('❌ Release Notes Generation Failed:', error.message);
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