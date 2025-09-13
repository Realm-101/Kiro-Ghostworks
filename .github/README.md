# CI/CD Pipeline Overview

This document provides a quick reference for the Ghostworks CI/CD pipeline. For complete documentation, see [docs/ci-cd-pipeline.md](../docs/ci-cd-pipeline.md).

## Pipeline Status

[![CI/CD Pipeline](https://github.com/Realm-101/Kiro-Ghostworks/actions/workflows/ci.yml/badge.svg)](https://github.com/Realm-101/Kiro-Ghostworks/actions/workflows/ci.yml)

## Quick Reference

### Pipeline Jobs
1. **Lint** → **Unit Tests** → **Integration Tests** → **Security Scan**
2. **E2E Tests** → **Performance Tests** → **Build**
3. **Generate Kiro Score** → **PR Comment** → **Deploy**

### Quality Gates
- **Tests**: ≥95% pass rate
- **Coverage**: Backend ≥70%, Frontend ≥60%
- **Security**: No high-severity vulnerabilities
- **Performance**: Route-class specific thresholds
- **Kiro Score**: ≥70 (B- grade) for deployment

### Kiro Score Grades
- **A+ to A- (≥85)**: AUTO_DEPLOY
- **B+ to B- (70-84)**: MANUAL_REVIEW
- **C+ to C- (55-69)**: BLOCK_WITH_OVERRIDE
- **D to F (<55)**: BLOCK

### Key Artifacts
- Test results (JUnit XML)
- Coverage reports (HTML/XML)
- Security scans (JSON/HTML)
- Performance results (k6 JSON)
- Kiro score (comprehensive JSON)

## For Developers

### Running Tests Locally
```bash
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests
make test-security     # Security tests
```

### Quality Checks
```bash
make lint              # Code linting
make typecheck         # Type checking
make security-scan     # Security scanning
```

### Troubleshooting
1. Check GitHub Actions logs
2. Review PR comment for detailed feedback
3. See [complete documentation](../docs/ci-cd-pipeline.md) for detailed troubleshooting

## Configuration Files

- **Pipeline**: `.github/workflows/ci.yml`
- **Kiro Scoring**: `scripts/generate_kiro_score.py`
- **PR Comments**: `scripts/pr_comment_bot.js`
- **Security Rules**: `.zap/rules.tsv`

For complete pipeline documentation, architecture details, and troubleshooting guides, see [docs/ci-cd-pipeline.md](../docs/ci-cd-pipeline.md).