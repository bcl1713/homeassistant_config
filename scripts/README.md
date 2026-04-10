# Scripts Directory

This directory contains utility scripts for managing and documenting the Home
Assistant configuration.

## Available Scripts

### export-ha-data.sh

A comprehensive data export script that gathers all Home Assistant configuration
files and entity states for AI-assisted development.

**Features:**

- Recursively finds all YAML configuration files
- Exports current entity states (if HA CLI is available)
- Includes GitHub issues for development context
- Safe for inclusion in git repository
- Excludes sensitive and temporary files

**Usage:**

```bash
# Make executable (first time only)
chmod +x scripts/export-ha-data.sh

# Run the export
./scripts/export-ha-data.sh
```

**Output:**

- Creates timestamped export files in the `exports/` directory
- Files are automatically excluded from future exports
- Contains all configuration context needed for AI development assistance

**Git Integration:**

- Script is version controlled as part of the configuration
- Export files are excluded via `.gitignore`
- Safe to run without affecting Home Assistant operation

## Directory Structure

```code
scripts/
├── README.md              # This file
└── export-ha-data.sh      # Data export utility
```

## Adding New Scripts

When adding new utility scripts:

1. Place them in this `scripts/` directory
2. Make them executable: `chmod +x scripts/script-name.sh`
3. Add documentation to this README
4. Ensure they don't interfere with Home Assistant operation
5. Exclude any generated files via `.gitignore`

## Safety Notes

- All scripts in this directory are designed to be safe for inclusion in the Home
  Assistant configuration repository
- Scripts do not modify Home Assistant configuration files
- Generated output files are stored in the `exports/` directory (git-ignored)
- Scripts can be run while Home Assistant is running without interference
