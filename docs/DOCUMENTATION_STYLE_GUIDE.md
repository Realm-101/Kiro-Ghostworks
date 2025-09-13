# Documentation Style Guide

This guide ensures consistency across all Ghostworks documentation.

## 📝 Writing Style

### Language
- **Dialect**: US English (prioritize, optimize, realize, utilize)
- **Tone**: Professional but approachable
- **Voice**: Active voice preferred
- **Tense**: Present tense for current features, future tense for roadmap

### Formatting
- **Headers**: Use sentence case (not title case)
- **Code**: Always use code blocks with language specification
- **Links**: Use descriptive link text, not "click here"
- **Lists**: Use parallel structure and consistent punctuation

## 🎨 Visual Consistency

### Emoji Usage (Standardized)

#### Section Headers
- 🚀 **Quick Start / Getting Started**
- 🏗️ **Architecture / System Design**
- 🎯 **Key Features / Core Functionality**
- 🛠️ **Development / Tools**
- 📊 **Monitoring / Metrics / Dashboards**
- 🚢 **Deployment / Operations**
- 📚 **Documentation / Resources**
- 🎪 **Demo / Tour / Presentation**
- 🤝 **Contributing / Community**
- 🆘 **Support / Help**

#### Content Types
- ⚡ **Performance / Speed**
- 🔒 **Security / Authentication**
- 🧪 **Testing / Quality**
- 🔄 **CI/CD / Automation**
- 🌱 **AI / Automation / Hooks**
- 📦 **Packages / Artifacts**
- ⚙️ **Configuration / Settings**
- 🔧 **Troubleshooting / Fixes**
- ✅ **Success / Validation**
- ❌ **Errors / Failures**
- ⚠️ **Warnings / Cautions**
- ℹ️ **Information / Notes**

#### Status Indicators
- ✅ **Complete / Working / Passed**
- ❌ **Failed / Broken / Missing**
- ⚠️ **Warning / Attention Needed**
- 🔄 **In Progress / Processing**
- ⏭️ **Skipped / Optional**
- 🎯 **Target / Goal / Objective**

### Header Hierarchy

```markdown
# Document Title (H1)
## Major Section (H2) 🚀
### Subsection (H3)
#### Detail Section (H4)
```

**Rules**:
- H1: Document title only (no emoji)
- H2: Major sections with emoji
- H3: Subsections (no emoji unless special emphasis)
- H4: Detail sections (no emoji)

## 📋 Content Structure

### README Files

#### Root README.md
- **Purpose**: User-facing entry point
- **Audience**: New users, evaluators, general audience
- **Content**: Overview, quick start, key features, navigation
- **Length**: Keep under 200 lines
- **Details**: Link to comprehensive docs, don't include

#### Service README.md
- **Purpose**: Service-specific documentation
- **Audience**: Developers working on that service
- **Content**: Setup, development, testing, deployment
- **Length**: Comprehensive but focused

#### .github/README.md
- **Purpose**: CI/CD quick reference
- **Audience**: Contributors, maintainers
- **Content**: Pipeline overview, quality gates, troubleshooting
- **Length**: Quick reference only, link to detailed docs

### Documentation Structure

```
README.md                    # User-facing overview
├── docs/
│   ├── getting-started.md   # Comprehensive setup
│   ├── ci-cd-pipeline.md    # Complete CI/CD docs
│   ├── security/            # Security documentation
│   ├── runbooks/            # Operational procedures
│   └── adr/                 # Architecture decisions
├── .github/README.md        # CI/CD quick reference
└── services/*/README.md     # Service-specific docs
```

## 🔗 Link Standards

### Internal Links
```markdown
# Good
[Getting Started Guide](docs/getting-started.md)
[API Documentation](http://localhost:8000/docs)

# Bad
[Click here for setup](docs/getting-started.md)
[API docs](http://localhost:8000/docs)
```

### External Links
```markdown
# Good
[Docker Desktop](https://www.docker.com/products/docker-desktop/)
[PostgreSQL Documentation](https://www.postgresql.org/docs/)

# Bad
[Docker](https://docker.com)
[Postgres docs](https://postgresql.org/docs)
```

## 📊 Code Examples

### Command Blocks
```markdown
# Always specify the shell/language
```bash
make dev-up
```

```python
# Python code example
def example_function():
    return "Hello, World!"
```

```typescript
// TypeScript code example
const example: string = "Hello, World!";
```
```

### File Paths
- Use relative paths from repository root
- Use forward slashes even on Windows
- Use code formatting for paths: `services/api/main.py`

## ⚠️ Security and Warnings

### Warning Blocks
```markdown
> **⚠️ SECURITY WARNING: DEMO CREDENTIALS ONLY**
> 
> **These credentials are ONLY available in local/development environments.**
> **They are automatically DISABLED in staging and production deployments.**
```

### Collapsible Sections
Use for content that's important but not always needed:

```markdown
<details>
<summary>🔑 Demo Accounts (Development Only)</summary>

[Content that can be hidden by default]

</details>
```

## 📚 Documentation Types

### User Guides
- **Focus**: How to accomplish tasks
- **Structure**: Step-by-step instructions
- **Examples**: Concrete, copy-paste ready
- **Audience**: End users, new developers

### Technical References
- **Focus**: Complete information about systems
- **Structure**: Comprehensive coverage
- **Examples**: Multiple scenarios and edge cases
- **Audience**: Experienced developers, maintainers

### Quick References
- **Focus**: Essential information only
- **Structure**: Tables, lists, key points
- **Examples**: Common commands and patterns
- **Audience**: Contributors who need quick lookup

## ✅ Quality Checklist

Before publishing documentation:

- [ ] Spelling and grammar checked (US English)
- [ ] Emojis follow standardized usage
- [ ] Headers use consistent hierarchy
- [ ] Code blocks specify language
- [ ] Links are descriptive and working
- [ ] Examples are copy-paste ready
- [ ] Security warnings are prominent
- [ ] Content is in appropriate location
- [ ] Cross-references are accurate
- [ ] Mobile-friendly formatting

## 🔄 Maintenance

### Regular Reviews
- **Monthly**: Check for broken links
- **Quarterly**: Update screenshots and examples
- **Per Release**: Update version-specific information
- **As Needed**: Fix reported issues

### Content Updates
1. **New Features**: Update relevant documentation
2. **API Changes**: Update examples and references
3. **Process Changes**: Update guides and procedures
4. **Security Updates**: Review and update warnings

This style guide ensures all Ghostworks documentation maintains a consistent, professional appearance while being maximally useful to users.