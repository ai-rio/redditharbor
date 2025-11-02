# RedditHarbor Documentation Naming Conventions

<div style="text-align: center; margin: 20px 0;">
  <h2 style="color: #FF6B35;">File Naming Standards</h2>
  <p style="color: #004E89;">Consistent naming conventions for organized documentation</p>
</div>

## 📝 Overview

This document establishes the naming conventions used throughout RedditHarbor documentation to ensure consistency, readability, and easy navigation.

---

## 🎯 Core Principles

1. **Consistency** - Use the same pattern throughout all documentation
2. **Readability** - Names should be clear and descriptive
3. **Searchability** - Easy to find specific documents
4. **Scalability** - Conventions should work as documentation grows
5. **Clarity** - Purpose of document should be clear from filename

---

## 📂 File Naming Rules

### Primary Rule: Kebab-Case

All documentation files must follow **kebab-case** naming (lowercase with hyphens):

```bash
✅ Correct Examples:
user-authentication.md
api-reference-guide.md
react-component-patterns.md
database-setup-tutorial.md
troubleshooting-common-issues.md

❌ Incorrect Examples:
UserAuthentication.md
API_Reference_Guide.md
React Component Patterns.md
databaseSetupTutorial.md
troubleshootingCommonIssues.md
```

### Special Cases

#### Uppercase Standard Files

```bash
# Always uppercase
README.md
CHANGELOG.md
LICENSE
CONTRIBUTING.md
```

#### Acronyms in Kebab-Case

```bash
# Keep acronyms lowercase
api-docs.md (not API-docs.md)
sql-setup.md (not SQL-setup.md)
html-guide.md (not HTML-guide.md)
url-configuration.md (not URL-configuration.md)
```

#### Version-Specific Files

```bash
# Include version in kebab-case
migration-guide-v2.md
api-changes-v1-5.md
legacy-support-v0-9.md
```

---

## 📁 Folder Naming Conventions

### Standard Folder Structure

```bash
docs/
├── api/                    # API documentation
├── components/             # Component documentation
├── guides/                 # User guides and tutorials
├── architecture/           # Architecture and design
├── contributing/           # Contributing guidelines
└── assets/                 # Images, diagrams, examples
    ├── images/             # Static images
    ├── diagrams/           # Architecture diagrams
    └── examples/           # Code examples
```

### Folder Names

All folders use **lowercase** with **kebab-case** for multi-word names:

```bash
✅ Correct:
user-guides/
api-documentation/
database-integration/
privacy-settings/

❌ Incorrect:
UserGuides/
API_Documentation/
DatabaseIntegration/
privacySettings/
```

---

## 📋 Document Type Naming Patterns

### 1. API Documentation

```bash
Pattern: [component]-api.md or [feature]-reference.md

Examples:
reddit-collector-api.md
privacy-processor-reference.md
database-operations-api.md
export-formats-reference.md
```

### 2. User Guides

```bash
Pattern: [topic]-guide.md or [action]-tutorial.md

Examples:
quick-start-guide.md
installation-tutorial.md
data-collection-guide.md
database-setup-tutorial.md
```

### 3. How-To Guides

```bash
Pattern: how-to-[action].md

Examples:
how-to-collect-posts.md
how-to-setup-database.md
how-to-export-data.md
how-to-configure-privacy.md
```

### 4. Troubleshooting

```bash
Pattern: troubleshooting-[issue].md

Examples:
troubleshooting-api-errors.md
troubleshooting-database-connection.md
troubleshooting-rate-limits.md
troubleshooting-authentication.md
```

### 5. Configuration

```bash
Pattern: [component]-configuration.md

Examples:
reddit-collector-configuration.md
database-configuration.md
privacy-settings-configuration.md
rate-limit-configuration.md
```

### 6. Examples

```bash
Pattern: [language]-[purpose]-example.md or [topic]-examples.md

Examples:
python-basic-collection-example.md
javascript-web-integration-example.md
data-analysis-examples.md
research-project-examples.md
```

---

## 🏷️ Tagging and Categorization

### Front Matter Tags

Each document should include relevant tags in its front matter:

```yaml
---
title: "User Authentication Guide"
description: "Complete guide to Reddit API authentication"
tags: ["authentication", "api", "setup", "beginner"]
category: "guides"
difficulty: "beginner"
estimated_time: "10 minutes"
related: ["api-setup.md", "troubleshooting-auth.md"]
---
```

### Tag Naming Conventions

```bash
# Use lowercase kebab-case
authentication
api-setup
data-collection
privacy-settings
rate-limiting
database-integration
performance-optimization
error-handling
```

---

## 📊 Content Organization Standards

### Document Structure

```markdown
# Document Title

<div style="text-align: center; margin: 20px 0;">
  <h2 style="color: #FF6B35;">Subtitle</h2>
  <p style="color: #004E89;">Description</p>
</div>

## Overview
Brief description of what the document covers

## Prerequisites
What users need before starting

## Steps/Sections
Main content with clear headings

## Examples
Practical code examples

## Troubleshooting
Common issues and solutions

## Related Documents
Links to related documentation
```

### Heading Conventions

```markdown
# Main Title (H1) - Document title only
## Section Title (H2) - Major sections
### Subsection Title (H3) - Sub-sections
#### Detailed Topic (H4) - Specific topics
##### Specific Point (H5) - Fine details
```

---

## 🔗 Internal Linking Conventions

### Link Format

```markdown
# Relative links to other documents
[Link Text](../path/to/document.md)

# Links to sections within documents
[Link Text](document.md#section-name)

# Links to API documentation
[Function Name](../api/reddit-collector.md#function-name)
```

### Cross-Reference Standards

```markdown
# API References
Use `function_name()` format in text
Link to full API documentation for details

# Code References
Use `ClassName.method_name()` format
Include file path for clarity: `redditharbor/collector.py:123`

# Configuration References
Use `config.option_name` format
Link to configuration documentation
```

---

## 🖼️ Image and Media Naming

### Image File Naming

```bash
# Use descriptive kebab-case names
reddit-data-flow-diagram.png
api-request-response-cycle.svg
database-schema-structure.png
rate-limiting-behavior-graph.png
error-handling-workflow.svg
```

### Screenshot Naming

```bash
# Include context and purpose
reddit-collector-setup-wizard.png
database-connection-settings-dialog.png
privacy-configuration-interface.png
export-data-selection-screen.png
```

### Diagram Naming

```bash
# Include type and subject
architecture-overview-diagram.svg
data-pipeline-flow-diagram.svg
component-interaction-diagram.svg
deployment-architecture-diagram.svg
```

---

## 📝 Version Control and History

### File Versioning

```bash
# For major version changes
authentication-guide-v2.md
api-reference-v2.md
migration-guide-v1-to-v2.md

# For version-specific content
python-3-8-compatibility.md
postgres-13-setup.md
sqlite-vs-postgresql-comparison.md
```

### Archive Naming

```bash
# For deprecated documentation
deprecated/old-authentication-methods.md
archive/legacy-api-v1-reference.md
old-versions/python-2-7-setup.md
```

---

## ✅ Quality Checklist

### Before Creating a Document

- [ ] **Name follows kebab-case convention**
- [ ] **Name is descriptive and clear**
- [ ] **Check for existing similar documents**
- [ ] **Determine correct folder location**
- [ ] **Plan document structure**

### Before Finalizing a Document

- [ ] **All internal links work correctly**
- [ ] **Images follow naming conventions**
- [ ] **Headings follow hierarchy rules**
- [ ] **Front matter is complete**
- [ ] **Related documents are linked**
- [ ] **Tags are appropriate**

### Regular Maintenance

- [ ] **Review document relevance**
- [ ] **Check for broken links**
- [ ] **Update outdated information**
- [ ] **Verify naming conventions**
- [ ] **Archive deprecated content**

---

## 🔄 Migration Guidelines

### Renaming Existing Files

When renaming files that already exist:

1. **Create redirect** from old name to new name
2. **Update all internal links** pointing to old name
3. **Update table of contents** and indexes
4. **Add note in changelog** about renamed files
5. **Consider 301 redirects** for web documentation

### Example Migration Process

```bash
# Old file: UserAuthentication.md
# New file: user-authentication-guide.md

1. Create new file with proper content
2. Add redirect in old file:
   # This file has moved
   This content has been moved to [user-authentication-guide.md](./user-authentication-guide.md)

3. Update all links:
   - README.md
   - API documentation
   - Guides and tutorials
   - Related documents

4. Update table of contents
5. Add to CHANGELOG.md
```

---

## 📚 Templates and Examples

### Document Template

```markdown
# Document Title

<div style="text-align: center; margin: 20px 0;">
  <h2 style="color: #FF6B35;">Subtitle</h2>
  <p style="color: #004E89;">Brief description</p>
</div>

## Overview
[What this document covers]

## Prerequisites
[What users need]

## Main Content
[Detailed content with proper headings]

## Examples
[Practical examples]

## Troubleshooting
[Common issues]

## Related Documents
[Links to related docs]
```

### Folder Structure Template

```bash
docs/
├── README.md                  # Main documentation index
├── CHANGELOG.md               # Version history
├── api/                       # API reference docs
│   ├── README.md
│   ├── reddit-collector.md
│   └── privacy-processor.md
├── guides/                    # User guides
│   ├── README.md
│   ├── quick-start.md
│   ├── installation.md
│   └── troubleshooting/
├── architecture/              # System architecture
│   ├── README.md
│   ├── overview.md
│   └── design-decisions.md
├── contributing/              # Contributing guide
│   └── README.md
└── assets/                    # Media assets
    ├── images/
    ├── diagrams/
    └── examples/
```

---

## 🎯 Quick Reference

### Naming Do's and Don'ts

| ✅ Do | ❌ Don't |
|------|---------|
| Use `kebab-case` | Use `camelCase` or `snake_case` |
| Be descriptive | Use vague names |
| Keep names concise | Use overly long names |
| Use lowercase for folders | Use uppercase folders |
| Include version when needed | Forget version specificity |
| Follow consistent patterns | Mix different patterns |

### Common Patterns

```bash
# Guides
quick-start.md
installation-guide.md
how-to-[action].md
troubleshooting-[issue].md

# API Documentation
[component]-api.md
[feature]-reference.md
[method]-documentation.md

# Configuration
[component]-configuration.md
[service]-setup.md
[feature]-settings.md

# Examples
[language]-[purpose]-example.md
[topic]-examples.md
[use-case]-tutorial.md
```

---

<div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #F5F5F5;">
  <p style="color: #666; font-size: 0.9em;">
    Following these conventions ensures consistent, maintainable documentation across RedditHarbor 🎯
  </p>
</div>