# Home Assistant Development Guide

This document outlines consistent workflows and processes to follow when making changes to this Home Assistant configuration. Following these guidelines will ensure consistent, high-quality contributions that align with the project's standards and make the system more maintainable.

## Development Workflow

### 1. Feature Selection and Planning

When selecting a new feature or automation to implement:

1. **Check GitHub issues** to see if it's already being worked on
2. **Understand dependencies** - identify if the feature depends on other incomplete components
3. **Create a GitHub issue** if one doesn't exist:
   ```
   gh issue create --title "Feature Name" --body "Description..." --label "enhancement,category"
   ```

### 2. Branch Management

1. **Always start from the latest main branch**:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create feature branches** with consistent naming:
   ```bash
   git checkout -b feature/descriptive-name
   ```
   For bug fixes:
   ```bash
   git checkout -b fix/descriptive-name
   ```

3. **Keep branches focused** on a single feature or bug fix

### 3. Implementation Standards

Follow these standards for all Home Assistant configuration changes:

1. **Package structure**:
   - Place new integrations in appropriate `packages/` directories
   - Follow existing patterns in similar packages
   - Create subpackages when appropriate for complex features

2. **Configuration design**:
   - Group related automations, scripts, and entities logically
   - Use descriptive entity names with consistent naming conventions
   - Leverage input booleans for user-toggleable features
   - Use variables and templates to reduce duplication

3. **Automation structure**:
   - Each automation should have a clear purpose defined in its alias and description
   - Group conditions logically
   - Use appropriate action sequences with proper error handling
   - Consider using blueprints for reusable automation patterns

4. **YAML formatting**:
   - Use 2-space indentation
   - Keep lines to a reasonable length (around 80-100 characters)
   - Use YAML lists and dictionaries appropriately
   - Be consistent with quoting strings

5. **Comment standards**:
   - Add a header comment to each file explaining its purpose
   - Document complex templates or non-obvious automation logic
   - Use consistent comment formatting

### 4. Testing

Before considering a feature complete:

1. **Check configuration validity** with Home Assistant's built-in checker:
   ```bash
   hass --script check_config
   ```

2. **Test in isolation** when possible:
   - Validate scripts independently
   - Test automations by manually triggering conditions
   - Verify template syntax in the Developer Tools

3. **Verify Lovelace integration** if adding UI elements

4. **Monitor logs** for any errors or warnings related to your changes

### 5. Commit Guidelines

Follow the established commit message format:

1. **Use conventional commits**:
   ```
   <type>(<scope>): <description>
   
   [optional body]
   
   [optional footer(s)]
   ```

2. **Types**:
   - `feat`: New feature or automation
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Formatting, no code change
   - `refactor`: Code change that neither fixes a bug nor adds a feature
   - `perf`: Code change that improves performance
   - `test`: Adding test configurations
   - `chore`: Changes to auxiliary tools/configurations

3. **Scope** should be the package or component being modified

4. **Description** should be concise and descriptive in imperative mood

5. **Example commits**:
   ```
   feat(security): add camera motion detection notifications
   
   docs(README): update with new security camera instructions
   
   fix(automation): correct good night routine condition check
   ```

### 6. Pull Request and Merging

For completing a feature:

1. **Verify all files are included** in the commit

2. **Push branch** to GitHub:
   ```bash
   git push origin feature/feature-name
   ```

3. **Create a pull request** to merge into main:
   ```bash
   gh pr create --title "Feature: Add descriptive name" --body "Description and closes #ISSUE_NUMBER" --base main
   ```

4. **Wait for review** if working with others, or verify quality if self-reviewing

5. **Merge to main** once approved:
   ```bash
   gh pr merge --squash
   ```

6. **Close related GitHub issue** if not auto-closed:
   ```bash
   gh issue close ISSUE_NUMBER
   ```

## Feature Implementation Patterns

### Adding a New Package

When adding a new package:

1. **Create package file** in appropriate location (e.g., `packages/new-feature.yaml`)

2. **Follow package template**:
   ```yaml
   # packages/new-feature.yaml
   #
   # Description of what this package does
   #
   # Features:
   # - Feature 1
   # - Feature 2
   
   # Configuration
   [configuration sections]
   
   # Automations
   automation:
     - alias: "Feature Automation"
       description: "Detailed description"
       trigger:
         [triggers]
       condition:
         [conditions]
       action:
         [actions]
   
   # Scripts
   script:
     feature_script:
       alias: "Feature Script"
       sequence:
         [sequence]
   
   # Other components as needed
   ```

3. **Reference in `configuration.yaml`** if needed for global imports

### Creating Automations

For complex automation implementation:

1. **Consider using blueprints** for reusable patterns

2. **Break complex sequences** into separate scripts for better maintainability

3. **Use helper entities** to track states and reduce complexity:
   - Input booleans for modes and flags
   - Input selects for multi-state options
   - Input numbers for thresholds

4. **Implement proper error handling**:
   - Choose appropriate action modes (single, restart, parallel, etc.)
   - Add timeouts to wait_for actions
   - Include notification for critical failures

### Implementing Device Integration

When adding new device integrations:

1. **Verify entity naming** follows project conventions

2. **Group related devices** with appropriate groups

3. **Create consistent UI cards** for the device

4. **Test compatibility** with existing automations

5. **Document any special setup requirements** for the device

## Common Troubleshooting

When troubleshooting issues:

1. **Check Home Assistant logs** for errors:
   ```bash
   tail -f home-assistant.log
   ```

2. **Verify YAML syntax** is correct

3. **Test templates** in Developer Tools > Template

4. **Check entity availability** before referencing in automations

5. **Restart Home Assistant** after configuration changes:
   ```bash
   ha core restart
   ```

6. **Review entity history** to understand state changes

## Best Practices

1. **Use packages** to organize complex configurations

2. **Leverage templates** for dynamic content

3. **Keep automations focused** on single tasks

4. **Document complex logic** with comments

5. **Use meaningful names** for all entities and scripts

6. **Test all edge cases** before considering implementation complete

7. **Keep UI clean and intuitive** for all users

8. **Maintain consistency** with existing configuration patterns

By following this guide, all contributions will maintain a consistent, high-quality standard that ensures the Home Assistant configuration remains maintainable and reliable over time.
