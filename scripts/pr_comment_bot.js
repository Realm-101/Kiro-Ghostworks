/**
 * GitHub Actions PR Comment Bot
 * 
 * This script generates comprehensive PR comments with test results,
 * coverage metrics, performance data, and security scan results.
 */

const fs = require('fs');
const path = require('path');

class PRCommentBot {
    constructor(github, context) {
        this.github = github;
        this.context = context;
    }

    /**
     * Load Kiro score data from artifacts
     */
    loadScoreData() {
        try {
            const scoreFile = path.join(process.cwd(), 'kiro_score.json');
            if (!fs.existsSync(scoreFile)) {
                throw new Error('kiro_score.json not found');
            }
            
            const scoreData = JSON.parse(fs.readFileSync(scoreFile, 'utf8'));
            return scoreData;
        } catch (error) {
            console.error('Error loading score data:', error);
            return null;
        }
    }

    /**
     * Generate grade emoji based on score
     */
    getGradeEmoji(grade) {
        const gradeEmojis = {
            'A+': '🏆',
            'A': '🟢',
            'A-': '🟢',
            'B+': '🔵',
            'B': '🔵',
            'B-': '🔵',
            'C+': '🟡',
            'C': '🟡',
            'C-': '🟡',
            'D': '🟠',
            'F': '🔴'
        };
        return gradeEmojis[grade] || '⚪';
    }

    /**
     * Generate test results table
     */
    generateTestTable(tests) {
        const testTypes = ['unit', 'integration', 'e2e'];
        let table = '| Test Type | Passed | Total | Pass Rate | Duration |\n';
        table += '|-----------|--------|-------|-----------|----------|\n';
        
        testTypes.forEach(type => {
            const test = tests[type];
            const passRate = test.total > 0 ? ((test.passed / test.total) * 100).toFixed(1) : '0';
            const duration = test.duration ? `${test.duration.toFixed(2)}s` : 'N/A';
            
            table += `| ${type.charAt(0).toUpperCase() + type.slice(1)} | ${test.passed} | ${test.total} | ${passRate}% | ${duration} |\n`;
        });
        
        return table;
    }

    /**
     * Generate coverage breakdown
     */
    generateCoverageSection(coverage) {
        let section = '### 📊 Coverage Report\n\n';
        
        const coverageBar = (percentage) => {
            const filled = Math.round(percentage / 5);
            const empty = 20 - filled;
            return '█'.repeat(filled) + '░'.repeat(empty);
        };
        
        section += `**Backend Coverage**: ${coverage.backend.toFixed(1)}%\n`;
        section += `\`${coverageBar(coverage.backend)}\` ${coverage.backend.toFixed(1)}%\n\n`;
        
        section += `**Frontend Coverage**: ${coverage.frontend.toFixed(1)}%\n`;
        section += `\`${coverageBar(coverage.frontend)}\` ${coverage.frontend.toFixed(1)}%\n\n`;
        
        section += `**Overall Coverage**: ${coverage.overall.toFixed(1)}%\n`;
        section += `\`${coverageBar(coverage.overall)}\` ${coverage.overall.toFixed(1)}%\n\n`;
        
        // Coverage targets
        const backendTarget = 70;
        const frontendTarget = 60;
        
        if (coverage.backend < backendTarget) {
            section += `⚠️ Backend coverage below target (${backendTarget}%)\n`;
        }
        if (coverage.frontend < frontendTarget) {
            section += `⚠️ Frontend coverage below target (${frontendTarget}%)\n`;
        }
        
        return section;
    }

    /**
     * Generate performance metrics section
     */
    generatePerformanceSection(performance) {
        let section = '### ⚡ Performance Metrics\n\n';
        
        section += '| Metric | Value | Target | Status |\n';
        section += '|--------|-------|--------|--------|\n';
        
        const p95Target = 200;
        const p95Status = performance.p95_response_time <= p95Target ? '✅' : '❌';
        section += `| P95 Response Time | ${performance.p95_response_time.toFixed(1)}ms | ${p95Target}ms | ${p95Status} |\n`;
        
        const errorRateTarget = 1;
        const errorStatus = performance.error_rate <= errorRateTarget ? '✅' : '❌';
        section += `| Error Rate | ${performance.error_rate.toFixed(2)}% | <${errorRateTarget}% | ${errorStatus} |\n`;
        
        section += `| Requests/sec | ${performance.requests_per_second.toFixed(1)} | - | ℹ️ |\n`;
        section += `| Avg Response Time | ${performance.avg_response_time.toFixed(1)}ms | - | ℹ️ |\n`;
        
        return section;
    }

    /**
     * Generate security section
     */
    generateSecuritySection(security) {
        let section = '### 🔒 Security Scan Results\n\n';
        
        if (security.scan_passed) {
            section += '✅ **Security scan passed**\n\n';
        } else {
            section += '❌ **Security scan failed**\n\n';
        }
        
        if (security.vulnerabilities_found > 0) {
            section += '**Vulnerabilities Found:**\n';
            section += `- 🔴 High: ${security.high_severity}\n`;
            section += `- 🟡 Medium: ${security.medium_severity}\n`;
            section += `- 🔵 Low: ${security.low_severity}\n\n`;
        }
        
        if (security.dependency_vulnerabilities > 0) {
            section += `⚠️ **Dependency vulnerabilities**: ${security.dependency_vulnerabilities}\n\n`;
        }
        
        return section;
    }

    /**
     * Generate recommendations section
     */
    generateRecommendationsSection(recommendations) {
        if (!recommendations || recommendations.length === 0) {
            return '';
        }
        
        let section = '### 🎯 Recommendations\n\n';
        recommendations.forEach(rec => {
            section += `- ${rec}\n`;
        });
        section += '\n';
        
        return section;
    }

    /**
     * Generate score trend (if previous scores available)
     */
    generateScoreTrend(currentScore) {
        // This would require storing previous scores
        // For now, just show current score
        return `**Current Score**: ${currentScore.toFixed(1)}/100\n\n`;
    }

    /**
     * Generate the complete PR comment
     */
    generateComment(scoreData) {
        const emoji = this.getGradeEmoji(scoreData.grade);
        const timestamp = new Date(scoreData.timestamp).toLocaleString();
        const commitSha = scoreData.commit_sha.substring(0, 7);
        
        let comment = `## 🎯 Kiro Quality Report\n\n`;
        
        // Header with score
        comment += `**Overall Score: ${scoreData.overall_score.toFixed(1)}/100 ${emoji} Grade ${scoreData.grade}**\n\n`;
        
        // Quick summary
        const totalTests = Object.values(scoreData.tests).reduce((sum, test) => sum + test.total, 0);
        const passedTests = Object.values(scoreData.tests).reduce((sum, test) => sum + test.passed, 0);
        const overallPassRate = totalTests > 0 ? ((passedTests / totalTests) * 100).toFixed(1) : '0';
        
        comment += `📈 **Quick Summary**: ${passedTests}/${totalTests} tests passed (${overallPassRate}%), `;
        comment += `${scoreData.coverage.overall.toFixed(1)}% coverage, `;
        comment += `${scoreData.performance.p95_response_time.toFixed(1)}ms P95 latency\n\n`;
        
        // Test results table
        comment += '### 📋 Test Results\n\n';
        comment += this.generateTestTable(scoreData.tests);
        comment += '\n';
        
        // Coverage section
        comment += this.generateCoverageSection(scoreData.coverage);
        
        // Performance section
        comment += this.generatePerformanceSection(scoreData.performance);
        comment += '\n';
        
        // Security section
        comment += this.generateSecuritySection(scoreData.security);
        
        // Recommendations
        comment += this.generateRecommendationsSection(scoreData.recommendations);
        
        // Score breakdown
        if (scoreData.score_breakdown) {
            comment += '### 📊 Score Breakdown\n\n';
            Object.entries(scoreData.score_breakdown).forEach(([key, value]) => {
                const icon = {
                    'tests': '🧪',
                    'coverage': '📊',
                    'performance': '⚡',
                    'security': '🔒'
                }[key] || '📋';
                comment += `${icon} **${key.charAt(0).toUpperCase() + key.slice(1)}**: ${value}\n`;
            });
            comment += '\n';
        }
        
        // Footer
        comment += '---\n';
        comment += `*Generated at ${timestamp} for commit ${commitSha}*\n`;
        comment += `*Workflow: [${scoreData.workflow_run_id}](${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${scoreData.workflow_run_id})*`;
        
        return comment;
    }

    /**
     * Find existing Kiro comment to update
     */
    async findExistingComment() {
        try {
            const comments = await this.github.rest.issues.listComments({
                owner: this.context.repo.owner,
                repo: this.context.repo.repo,
                issue_number: this.context.issue.number,
            });
            
            return comments.data.find(comment => 
                comment.body.includes('🎯 Kiro Quality Report') &&
                comment.user.type === 'Bot'
            );
        } catch (error) {
            console.error('Error finding existing comment:', error);
            return null;
        }
    }

    /**
     * Post or update PR comment
     */
    async postComment() {
        const scoreData = this.loadScoreData();
        if (!scoreData) {
            console.error('Could not load score data, skipping PR comment');
            return;
        }
        
        const comment = this.generateComment(scoreData);
        const existingComment = await this.findExistingComment();
        
        try {
            if (existingComment) {
                // Update existing comment
                await this.github.rest.issues.updateComment({
                    owner: this.context.repo.owner,
                    repo: this.context.repo.repo,
                    comment_id: existingComment.id,
                    body: comment
                });
                console.log('Updated existing PR comment');
            } else {
                // Create new comment
                await this.github.rest.issues.createComment({
                    owner: this.context.repo.owner,
                    repo: this.context.repo.repo,
                    issue_number: this.context.issue.number,
                    body: comment
                });
                console.log('Created new PR comment');
            }
        } catch (error) {
            console.error('Error posting PR comment:', error);
            throw error;
        }
    }
}

module.exports = { PRCommentBot };