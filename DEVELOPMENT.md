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

This repository does not have a separate Home Assistant staging environment, so the branch model should reflect reality rather than ceremony.

1. **Treat `dev` as the active trunk and normal deployment source**:
   ```bash
   git checkout dev
   git pull origin dev
   ```

2. **Create focused branches** with consistent naming for any non-trivial work:
   ```bash
   git checkout -b feature/descriptive-name
   ```
   For bug fixes:
   ```bash
   git checkout -b fix/descriptive-name
   ```
   For documentation or maintenance work:
   ```bash
   git checkout -b docs/descriptive-name
   git checkout -b chore/descriptive-name
   ```

3. **Keep branches focused** on a single feature or bug fix.
4. **Target pull requests at `dev`**. Do not treat `main` as the normal merge target.
5. **Use direct commits to `dev` only for truly low-risk changes** such as docs, comments, typos, or harmless cleanup.
6. **Tag successful live deployments** so rollback does not depend on `main` staying current.

See [docs/branching-and-deployment.md](docs/branching-and-deployment.md) for the full branch, deploy, and rollback policy.

### 3. Implementation Standards

Follow these standards for all Home Assistant configuration changes:

0. **Repository structure**:
   - `packages: !include_dir_named packages` loads feature packages
   - `automation: !include_dir_merge_list automation` loads standalone automation files
   - `input_boolean: !include_dir_merge_named input_boolean` loads helper toggles
   - Prefer extending the existing modular structure instead of placing unrelated logic in `configuration.yaml`

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

1. **Prefer safe static validation first**:
   - Parse changed YAML files
   - Run repository-provided documentation or lint checks when available
   - Review diffs for accidental entity renames, indentation problems, or package loading mistakes

2. **Run a Home Assistant config check only when the task or repo provides a known-safe local command/environment**:
   - Do not assume ad hoc access to a live instance is safe
   - Do not rely on live reloads or restarts as part of normal development verification

3. **Test in isolation** when possible:
   - Validate scripts independently
   - Verify template syntax in a safe development context

4. **Verify Lovelace integration** if adding UI elements

5. **Monitor logs** for any errors or warnings related to your changes when a task explicitly includes a safe log-review path

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

3. **Create a pull request** to merge into `dev`:
   ```bash
   gh pr create --title "Feature: Add descriptive name" --body "Description and closes #ISSUE_NUMBER" --base dev
   ```

4. **Wait for review** if working with others, or verify quality if self-reviewing

5. **Merge to `dev`** once approved:
   ```bash
   gh pr merge --squash
   ```

6. **Do not self-merge automation changes**; wait for reviewer approval and the established integration flow.

7. **Close related GitHub issue** if not auto-closed:
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

### Common Troubleshooting

When troubleshooting issues:

1. **Check Home Assistant logs** for errors when the task explicitly includes a safe way to do so:
   ```bash
   tail -f home-assistant.log
   ```

2. **Verify YAML syntax** is correct

3. **Test templates** in a safe development environment before relying on live behavior

4. **Check entity availability** before referencing in automations

5. **Do not restart or reload Home Assistant as part of routine development work unless the task explicitly authorizes the live action and rollback plan**

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
