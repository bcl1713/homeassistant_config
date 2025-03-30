# Contributing Guide

Thank you for your interest in contributing to this Home Assistant configuration! This document provides guidelines and processes to follow when making changes.

## Getting Started

1. Read the [DEVELOPMENT.md](DEVELOPMENT.md) file for detailed workflow information
2. Check existing [GitHub issues](https://github.com/yourusername/home-assistant-config/issues) for current work
3. Fork the repository if you're not already a collaborator

## Contribution Process

### 1. Pick an Issue or Create One

- Browse existing issues or create a new one
- Comment on the issue you'd like to work on to avoid duplication of effort

### 2. Branch Management

Follow these branching conventions:
- Feature branches: `feature/descriptive-name`
- Bug fixes: `fix/descriptive-name`
- Documentation: `docs/descriptive-name`

Always start from the latest main branch:
```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

### 3. Development Standards

Please follow these standards:
- Use 2-space indentation in YAML files
- Follow existing naming conventions
- Group related configurations logically
- Add sufficient comments to explain complex automations
- Test all changes before submitting

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed standards.

### 4. Commit Messages

Use conventional commit format:
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Examples:
- `feat(security): add camera motion detection notifications`
- `fix(automation): correct good night routine condition check`
- `docs(README): update with new security camera instructions`

### 5. Pull Request Process

1. Push your branch to GitHub
2. Create a pull request to merge into main
3. Reference the issue number in the PR description
4. Wait for review and address any feedback

## Code of Conduct

- Be respectful and inclusive in all communications
- Provide constructive feedback
- Help maintain a welcoming environment for contributors of all skill levels

Thank you for helping to improve this Home Assistant configuration!
