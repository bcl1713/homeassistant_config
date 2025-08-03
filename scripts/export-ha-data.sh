#!/bin/bash

# Simple Home Assistant Data Exporter
# Safe for placement in Home Assistant config directory
#
# Usage: ./scripts/export-ha-data.sh
#
# This script is designed to be part of your Home Assistant configuration
# repository and will not interfere with Home Assistant operation.

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
CONFIG_DIR="$(dirname "$SCRIPT_DIR")"

# Create exports directory if it doesn't exist
EXPORTS_DIR="$CONFIG_DIR/exports"
mkdir -p "$EXPORTS_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="$EXPORTS_DIR/ha_export_${TIMESTAMP}.txt"

echo "# Home Assistant Export - $(date)" >"$OUTPUT_FILE"
echo "# Generated for AI development assistance" >>"$OUTPUT_FILE"
echo "" >>"$OUTPUT_FILE"

# Function to add a section to the output
add_section() {
  local title="$1"
  local content="$2"

  cat >>"$OUTPUT_FILE" <<EOF

========================================
$title
========================================

$content

EOF
}

# Export entity states using Home Assistant CLI if available, otherwise use REST API
export_entities() {
  echo "Exporting entity states..."

  if command -v ha &>/dev/null; then
    # Use Home Assistant CLI
    local entities_json
    entities_json=$(ha --output json state list 2>/dev/null || echo '[]')

    # Convert to markdown format
    local entities_md
    entities_md=$(echo "$entities_json" | jq -r '
            group_by(.entity_id | split(".")[0]) |
            to_entries[] |
            "## " + (.value[0].entity_id | split(".")[0]) + "\n\n" +
            (.value[] | 
                "- " + .entity_id + 
                (if .friendly_name then " (" + .friendly_name + ")" else "" end) +
                " - State: " + .state +
                (if .unit_of_measurement then " " + .unit_of_measurement else "" end)
            ) + "\n"
        ' 2>/dev/null || echo "Unable to parse entity data")

    add_section "ENTITIES" "$entities_md"
  else
    add_section "ENTITIES" "Home Assistant CLI not available. Please install 'ha' command or use the full script with API access."
  fi
}

# Export configuration files
export_config() {
  echo "Exporting configuration files..."

  # Directories and files to exclude from the search
  local exclude_patterns=(
    ".git"
    ".storage"
    "__pycache__"
    "*.pyc"
    "deps"
    "tts"
    "*.log"
    "*.db"
    "*.db-shm"
    "*.db-wal"
    "home-assistant.log*"
    "OZW_Log.txt"
    "*.disabled"
    ".HA_VERSION"
    ".uuid"
    "*.noload"
    "core.*"
    "exports"
    "scripts/export-ha-data.sh"
    ".cloud"
    ".google.token"
    "google_calendars.yaml"
    "ip_bans.yaml"
    "known_devices.yaml"
    "secrets.yaml"
    "www"
    "custom_components/*/translations"
  )

  # Build exclude arguments for find command
  local exclude_args=""
  for pattern in "${exclude_patterns[@]}"; do
    exclude_args="$exclude_args -not -path '*/$pattern' -not -name '$pattern'"
  done

  # Change to config directory for consistent file discovery
  cd "$CONFIG_DIR"

  # Find all YAML files recursively, excluding unwanted directories
  echo "Scanning for YAML files in: $CONFIG_DIR"
  local yaml_files
  yaml_files=$(eval "find . -type f \\( -name '*.yaml' -o -name '*.yml' \\) $exclude_args" | sort)

  local file_count
  file_count=$(echo "$yaml_files" | wc -l)
  echo "Found $file_count YAML files"

  # Process each YAML file
  while IFS= read -r yaml_file; do
    # Skip empty lines
    [ -z "$yaml_file" ] && continue

    # Remove leading ./ from path for cleaner display
    local clean_path="${yaml_file#./}"

    echo "Processing: $clean_path"

    cat >>"$OUTPUT_FILE" <<EOF


========================================
FILE: $clean_path
========================================

EOF

    # Check if file is readable and not binary
    if [ -r "$yaml_file" ]; then
      if file "$yaml_file" | grep -q "text"; then
        cat "$yaml_file" >>"$OUTPUT_FILE"
      else
        echo "[BINARY FILE - CONTENT EXCLUDED]" >>"$OUTPUT_FILE"
      fi
    else
      echo "[FILE NOT READABLE]" >>"$OUTPUT_FILE"
    fi

  done <<<"$yaml_files"

  # Also include some important non-YAML config files
  local other_config_files=(
    "README.md"
    "DEVELOPMENT.md"
    "CONTRIBUTING.md"
    "LICENSE.md"
    ".gitignore"
  )

  echo "Checking for additional configuration files..."
  for config_file in "${other_config_files[@]}"; do
    if [ -f "$config_file" ]; then
      echo "Processing: $config_file"
      cat >>"$OUTPUT_FILE" <<EOF


========================================
FILE: $config_file
========================================

EOF
      if file "$config_file" | grep -q "text"; then
        cat "$config_file" >>"$OUTPUT_FILE"
      else
        echo "[BINARY FILE - CONTENT EXCLUDED]" >>"$OUTPUT_FILE"
      fi
    fi
  done

  echo "Configuration export complete"
}

# Export GitHub issues if available
export_github_issues() {
  echo "Exporting GitHub issues..."

  if command -v gh &>/dev/null && [ -f ".git/config" ]; then
    local issues_json
    issues_json=$(gh issue list --json assignees,body,labels,number,state,title --limit 50 2>/dev/null || echo '[]')
    add_section "GITHUB ISSUES" "$issues_json"
  else
    add_section "GITHUB ISSUES" "GitHub CLI not available or not in a git repository."
  fi
}

# Main execution
main() {
  echo "Starting Home Assistant data export..."
  echo "Config directory: $CONFIG_DIR"
  echo "Output file: $OUTPUT_FILE"

  export_entities
  export_config
  export_github_issues

  echo ""
  echo "========================================" >>"$OUTPUT_FILE"
  echo "EXPORT COMPLETE" >>"$OUTPUT_FILE"
  echo "Generated: $(date)" >>"$OUTPUT_FILE"
  echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)" >>"$OUTPUT_FILE"
  echo "Config directory: $CONFIG_DIR" >>"$OUTPUT_FILE"
  echo "========================================" >>"$OUTPUT_FILE"

  echo "Export complete!"
  echo "File: $OUTPUT_FILE"
  echo "Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
  echo ""
  echo "You can now upload this file to provide complete context to your AI assistant."
  echo ""
  echo "Note: Export files are saved in the 'exports' directory and excluded from"
  echo "      future exports to prevent recursive inclusion."
}

main
