# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **Home Assistant development workflow system** that provides AI-assisted development, automated branch testing, and safe production deployment. The system uses a dual-repository structure:

- **Main repository** (`homeassistant-dev/`) - Development workflow scripts and tools
- **Config repository** (`homeassistant-dev/config/`) - Home Assistant configuration using packages pattern

## Working with Dual-Repository Structure

### Important Git Workflow Considerations

**Zoxide Compatibility Issues:**
- The local system uses `zoxide` which overrides `cd` command behavior
- **NEVER use `cd` commands on the local machine** - they will fail due to zoxide integration
- **Use `-C` flag instead locally**: `git -C config <command>`
- **For complex directory changes locally**: Use absolute paths like `/home/brian/Projects/homeassistant-dev/config`
- **Remote SSH commands**: `cd` works normally on the server (e.g., `ssh root@$HAOS_IP "cd /config && git checkout main"`)

**Repository-Specific Operations:**
```bash
# CORRECT: Working with config repository locally
git -C config checkout -b feature/branch-name
git -C config add packages/weather.yaml
git -C config commit -m "fix: description"
git -C config push origin feature/branch-name

# WRONG: Will fail on local machine due to zoxide
cd config  # This will fail locally!
git checkout -b feature/branch-name

# CORRECT: Remote server operations
ssh root@$HAOS_IP "cd /config && git checkout branch-name"  # Works fine on server
```

**Branch Management Gotchas:**
- **Main repo branches** ≠ **Config repo branches**
- Always create feature branches in the **config repository** for HA configuration changes
- The `./scripts/deploy-branch.sh` script deploys based on current directory context
- **Manual deployment** for config branches: `ssh root@$HAOS_IP "cd /config && git checkout branch-name"`

**GitHub CLI Operations:**
```bash
# CORRECT: Create PR from config repo with explicit repo specification
gh pr create --repo bcl1713/homeassistant_config --head feature/branch --base main --title "Title" --body "Body"

# WRONG: Running from main repo directory without repo specification
gh pr create --title "Title"  # Creates PR in wrong repository!
```

**Home Assistant API Authentication:**
```bash
# ALWAYS source environment first for API calls
source .env && curl -X POST -H "Authorization: Bearer $HA_TOKEN" "http://$HAOS_IP:8123/api/services/automation/reload"

# Environment variables may not be available without explicit sourcing
```

### Complete Config Change Workflow

1. **Create feature branch in config repo:**
   ```bash
   git -C config checkout -b fix/descriptive-name
   ```

2. **Make changes and commit:**
   ```bash
   git -C config add packages/changed-file.yaml
   git -C config commit -m "fix: description"
   ```

3. **Push branch:**
   ```bash
   git -C config push origin fix/descriptive-name
   ```

4. **Deploy for testing:**
   ```bash
   ssh root@$HAOS_IP "cd /config && git fetch origin && git checkout fix/descriptive-name && git pull origin fix/descriptive-name"
   ssh root@$HAOS_IP "ha core check"  # Validate
   source .env && curl -X POST -H "Authorization: Bearer $HA_TOKEN" "http://$HAOS_IP:8123/api/services/automation/reload"
   ```

5. **Create and merge PR:**
   ```bash
   gh pr create --repo bcl1713/homeassistant_config --head fix/descriptive-name --base main --title "Title" --body "Description"
   gh pr merge PR_NUMBER --repo bcl1713/homeassistant_config --squash
   ```

6. **Deploy merged changes:**
   ```bash
   ssh root@$HAOS_IP "cd /config && git checkout main && git pull origin main"
   source .env && curl -X POST -H "Authorization: Bearer $HA_TOKEN" "http://$HAOS_IP:8123/api/services/automation/reload"
   ```

## Development Commands

### Core Workflow Scripts
```bash
# Get fresh AI context from production HA instance
./scripts/get-ai-context.sh

# Deploy current branch to production for testing
./scripts/deploy-branch.sh  

# Rollback to main branch (emergency recovery)
./scripts/rollback.sh
```

### Configuration Management
The Home Assistant configuration uses standard HA commands via SSH:
```bash
# Configuration validation
ssh $HAOS_USER@$HAOS_IP "ha core check"

# Service reloads (via API)
curl -X POST -H "Authorization: Bearer $HA_TOKEN" "http://$HAOS_IP:8123/api/services/homeassistant/reload_all"
curl -X POST -H "Authorization: Bearer $HA_TOKEN" "http://$HAOS_IP:8123/api/services/automation/reload"
curl -X POST -H "Authorization: Bearer $HA_TOKEN" "http://$HAOS_IP:8123/api/services/script/reload"

# Full restart (if needed)
ssh $HAOS_USER@$HAOS_IP "ha core restart"
```

### GitHub Integration
```bash
# Issue management (configured in .claude/settings.local.json)
gh issue list
gh issue create --title "Feature Name" --body "Description..." --label "enhancement"

# Branch and PR workflow
git checkout -b feature/descriptive-name
git push origin feature-name
gh pr create --title "Feature: Description" --body "Closes #ISSUE_NUMBER" --base main
```

## Architecture

### Development Workflow Structure
- **`scripts/`** - Automation scripts for deployment, context generation, and rollback
- **`config/`** - Git submodule containing Home Assistant configuration
- **`context/`** - AI context files generated from production HA instance (gitignored)
- **`.env`** - Environment configuration (HA connection details, tokens)

### Home Assistant Configuration Architecture
The `config/` directory uses Home Assistant's packages pattern:

- **`packages/`** - Modular feature packages (cameras, presence, notifications, security, etc.)
- **`configuration.yaml`** - Main config with package imports and core settings
- **`automation/`** - Additional automation files via `!include_dir_merge_list`
- **`input_boolean/`** - Boolean controls via `!include_dir_merge_named`
- **`.github/workflows/validate.yaml`** - CI validation using Home Assistant container

### Key Configuration Patterns
```yaml
# Package structure (packages/*.yaml)
automation:
  - alias: "Descriptive Name" 
    description: "Clear purpose description"
    trigger: [triggers]
    condition: [conditions]
    action: [actions]

script:
  script_name:
    alias: "Script Name" 
    sequence: [steps]
```

### Notification System
Multi-device notifications configured in `configuration.yaml`:
- `notify.all_mobile_devices` - Group service for Brian and Hester's phones
- Individual services: `mobile_app_brian_phone`, `mobile_app_hester_phone`

## Environment Setup

### Required Environment Variables (.env)
```bash
# Home Assistant connection
HAOS_IP=192.168.1.XXX
HAOS_USER=root
HA_TOKEN=your_long_lived_access_token_here

# Project paths
PROJECT_DIR=/home/USERNAME/Projects/homeassistant-dev
```

### Prerequisites
- Home Assistant OS instance with SSH access
- GitHub repository for HA configuration 
- Home Assistant long-lived access token
- Modified export script on HAOS: `/config/scripts/export-ha-data-fixed.sh`

## Development Process

### Standard Workflow (90-second cycle)
1. **Get AI Context**: `./scripts/get-ai-context.sh` → Upload `context/ai-context.txt` to AI
2. **Develop**: Create/edit YAML configurations with AI assistance
3. **Commit**: `git add . && git commit -m "feat: description"`
4. **CI Validation**: `git push` triggers GitHub Actions validation
5. **Test on Production**: `./scripts/deploy-branch.sh` after CI passes
6. **Finalize**: Merge PR or `./scripts/rollback.sh` if issues

### Branch Strategy
- Feature branches: `feature/descriptive-name`
- Bug fixes: `fix/descriptive-name`
- CI validation required before production testing
- Squash merge to main after testing

### Claude Code Permissions
The `.claude/settings.local.json` configures allowed GitHub CLI operations:
- `gh issue view:*`, `gh issue create:*`, `gh issue comment:*`
- Default mode: `acceptEdits`

## Special Features

### AI Context Generation
- Exports comprehensive HA state, entities, and configurations
- Generated via remote script execution on production instance
- Provides full context for AI-assisted development

### Safe Production Testing  
- Git-based deployment to production HA instance
- Configuration validation before reload
- API-based reloads (no full restarts needed)
- Instant rollback capability

### CI Integration
- GitHub Actions validate configuration using HA container
- Creates dummy service account file for Google Assistant integration
- Continues on expected errors to allow deployment testing
- config is a separate git repository.  make sure you are branching the right repository
- I use zoxide, so cd commands will give you trouble