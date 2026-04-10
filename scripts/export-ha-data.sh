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

# Export entity states from Home Assistant state files
export_entities() {
  echo "Exporting entity states..."

  # Check for entity registry file
  if [ -f "$CONFIG_DIR/.storage/core.entity_registry" ]; then
    echo "Found entity registry, extracting entity list..."

    local entity_count
    entity_count=$(grep -o '"entity_id":"[^"]*"' "$CONFIG_DIR/.storage/core.entity_registry" 2>/dev/null | wc -l || echo "0")

    # Create a temporary file for the entities content
    local entities_temp="/tmp/entities_export.txt"

    cat >"$entities_temp" <<'ENTITIES_EOF'
# Entity Registry Summary
ENTITIES_EOF

    echo "Total registered entities: $entity_count" >>"$entities_temp"
    echo "" >>"$entities_temp"
    echo "# Domain Summary" >>"$entities_temp"

    # Extract entities by domain and count them
    if grep -o '"entity_id":"[^"]*"' "$CONFIG_DIR/.storage/core.entity_registry" 2>/dev/null |
      sed 's/"entity_id":"\([^"]*\)"/\1/' |
      cut -d'.' -f1 | sort | uniq -c >/tmp/domain_counts.txt 2>/dev/null; then

      while read -r count domain; do
        echo "- $domain: $count entities" >>"$entities_temp"
      done </tmp/domain_counts.txt
      rm -f /tmp/domain_counts.txt
    fi

    echo "" >>"$entities_temp"
    echo "# All Entities" >>"$entities_temp"
    echo "" >>"$entities_temp"

    # List all entities
    grep -o '"entity_id":"[^"]*"' "$CONFIG_DIR/.storage/core.entity_registry" 2>/dev/null |
      sed 's/"entity_id":"\([^"]*\)"/- \1/' >>"$entities_temp" 2>/dev/null || true

    add_section "ENTITIES" "$(cat "$entities_temp")"
    rm -f "$entities_temp"
  else
    add_section "ENTITIES" "Entity registry not found at $CONFIG_DIR/.storage/core.entity_registry
This is normal if Home Assistant is not running or if this is a fresh installation."
  fi
}

# Function to read .gitignore patterns
read_gitignore_patterns() {
  local gitignore_file="$CONFIG_DIR/.gitignore"
  local patterns=()

  if [ -f "$gitignore_file" ]; then
    echo "Reading .gitignore patterns..."
    while IFS= read -r line; do
      # Skip empty lines and comments
      if [[ -n "$line" && ! "$line" =~ ^[[:space:]]*# ]]; then
        # Remove leading/trailing whitespace
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -n "$line" ]]; then
          patterns+=("$line")
        fi
      fi
    done <"$gitignore_file"
  fi

  printf '%s\n' "${patterns[@]}"
}

# Export configuration files
export_config() {
  echo "Exporting configuration files..."

  # Base exclude patterns (always exclude these)
  local base_exclude_patterns=(
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

  # Read .gitignore patterns
  local gitignore_patterns
  mapfile -t gitignore_patterns < <(read_gitignore_patterns)

  # Combine base patterns with gitignore patterns
  local all_exclude_patterns=("${base_exclude_patterns[@]}" "${gitignore_patterns[@]}")

  echo "Total exclude patterns: ${#all_exclude_patterns[@]} (${#base_exclude_patterns[@]} base + ${#gitignore_patterns[@]} from .gitignore)"

  # Build exclude arguments for find command
  local exclude_args=""
  for pattern in "${all_exclude_patterns[@]}"; do
    # Handle different gitignore pattern types
    if [[ "$pattern" == */ ]]; then
      # Directory pattern (ends with /)
      pattern="${pattern%/}"
      exclude_args="$exclude_args -not -path '*/$pattern' -not -path '*/$pattern/*'"
    elif [[ "$pattern" == */* ]]; then
      # Path pattern (contains /)
      exclude_args="$exclude_args -not -path '*/$pattern'"
    else
      # File pattern
      exclude_args="$exclude_args -not -name '$pattern'"
    fi
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

    cat >>"$OUTPUT_FILE" <<'FILE_HEADER_EOF'


========================================
FILE_HEADER_EOF
    echo "FILE: $clean_path" >>"$OUTPUT_FILE"
    cat >>"$OUTPUT_FILE" <<'FILE_SEPARATOR_EOF'
========================================

FILE_SEPARATOR_EOF

    # Check if file is readable and appears to be text (simple heuristic)
    if [ -r "$yaml_file" ]; then
      # Simple check: if file contains mostly printable characters, treat as text
      # This replaces the 'file' command which isn't available
      if head -c 1000 "$yaml_file" 2>/dev/null | grep -q '^[[:print:][:space:]]*$'; then
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
      cat >>"$OUTPUT_FILE" <<'OTHER_FILE_HEADER_EOF'


========================================
OTHER_FILE_HEADER_EOF
      echo "FILE: $config_file" >>"$OUTPUT_FILE"
      cat >>"$OUTPUT_FILE" <<'OTHER_FILE_SEPARATOR_EOF'
========================================

OTHER_FILE_SEPARATOR_EOF
      if head -c 1000 "$config_file" 2>/dev/null | grep -q '^[[:print:][:space:]]*$'; then
        cat "$config_file" >>"$OUTPUT_FILE"
      else
        echo "[BINARY FILE - CONTENT EXCLUDED]" >>"$OUTPUT_FILE"
      fi
    fi
  done

  echo "Configuration export complete"
}

# Export GitHub issues if available (removed - not available on HA)
export_github_issues() {
  echo "Skipping GitHub issues export (not available on Home Assistant)..."
  add_section "GITHUB ISSUES" "GitHub CLI not available on Home Assistant. Run this script on your local machine with 'gh' installed for issue export."
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
