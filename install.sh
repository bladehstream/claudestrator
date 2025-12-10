#!/bin/bash
#
# Claudestrator Installer
# https://github.com/bladehstream/claudestrator
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/bladehstream/claudestrator/main/install.sh | bash
#
# Or inspect first:
#   curl -fsSL https://raw.githubusercontent.com/bladehstream/claudestrator/main/install.sh -o install.sh
#   less install.sh
#   bash install.sh
#
# Options:
#   --global, -g  Install globally (~/.claude/) instead of current project
#   --force       Skip confirmation prompts
#   --uninstall   Remove Claudestrator installation
#   --dry-run     Show what would be done without making changes
#

set -e

# Colors (disabled if not a terminal)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    DIM='\033[2m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    DIM=''
    NC=''
fi

# Default configuration
INSTALL_MODE="local"
FORCE_INSTALL=false
UNINSTALL=false
DRY_RUN=false
REPO_URL="https://github.com/bladehstream/claudestrator.git"
REPO_RAW_URL="https://raw.githubusercontent.com/bladehstream/claudestrator/main"

# Temporary directory for downloads during diff preview
TEMP_DIR=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --global|-g)
            INSTALL_MODE="global"
            shift
            ;;
        --force)
            FORCE_INSTALL=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Claudestrator Installer"
            echo ""
            echo "Usage: install.sh [options]"
            echo ""
            echo "By default, installs to current project directory (.claudestrator/)"
            echo ""
            echo "Options:"
            echo "  --global, -g  Install globally to ~/.claude/ (available in all projects)"
            echo "  --force       Skip confirmation prompts"
            echo "  --uninstall   Remove Claudestrator installation"
            echo "  --dry-run     Show what would be done without making changes"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Utility functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_dry_run() {
    echo -e "${CYAN}[DRY-RUN]${NC} $1"
}

confirm() {
    if [ "$FORCE_INSTALL" = true ]; then
        return 0
    fi

    local prompt="$1 [y/N] "
    read -r -p "$prompt" response
    case "$response" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Cleanup temp directory on exit
cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}
trap cleanup EXIT

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing=()

    if ! command -v git &> /dev/null; then
        missing+=("git")
    fi

    if ! command -v diff &> /dev/null; then
        missing+=("diff")
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing[*]}"
        log_info "Please install them and try again."
        exit 1
    fi

    log_success "Prerequisites satisfied"
}

# Set installation paths based on mode
set_paths() {
    if [ "$INSTALL_MODE" = "global" ]; then
        CLAUDE_DIR="$HOME/.claude"
        REPO_DIR="$CLAUDE_DIR/claudestrator"
        COMMANDS_DIR="$CLAUDE_DIR/commands"
        SKILLS_DIR="$CLAUDE_DIR/skills"
        CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
        log_info "Installation mode: ${BOLD}Global${NC} (~/.claude/)"
    else
        CLAUDE_DIR=".claude"
        REPO_DIR=".claudestrator"
        COMMANDS_DIR="$CLAUDE_DIR/commands"
        SKILLS_DIR="$CLAUDE_DIR/skills"
        CLAUDE_MD="$CLAUDE_DIR/CLAUDE.md"
        log_info "Installation mode: ${BOLD}Local${NC} (current directory)"
    fi
}

# Generate the CLAUDE.md content that will be appended
generate_claude_md_content() {
    if [ "$INSTALL_MODE" = "global" ]; then
        local protocol_path="~/.claude/claudestrator/orchestrator_protocol_v3.md"
        local skills_path="~/.claude/skills/"
        local templates_path="~/.claude/claudestrator/prd_generator/templates/"
    else
        local protocol_path=".claudestrator/orchestrator_protocol_v3.md"
        local skills_path=".claude/skills/"
        local templates_path=".claudestrator/prd_generator/templates/"
    fi

    cat << EOF

## Claudestrator

Multi-agent orchestration framework. When orchestrating:

- **Protocol**: Read and follow $protocol_path
- **Skills**: $skills_path
- **PRD Templates**: $templates_path
- **State Files**: .claude/ (session_state.md, orchestrator_memory.md, knowledge_graph.json)

Commands: /orchestrate, /prdgen, /checkpoint, /status, /tasks, /skills, /deorchestrate, /audit-skills, /skill-enhance
EOF
}

# Show diff between two files (or show new file content)
show_diff() {
    local existing="$1"
    local new_content="$2"
    local file_label="$3"

    echo ""
    echo -e "${BOLD}━━━ $file_label ━━━${NC}"

    if [ -f "$existing" ]; then
        # Create temp file for new content
        local temp_new=$(mktemp)
        echo "$new_content" > "$temp_new"

        echo -e "${DIM}Showing diff: existing → proposed${NC}"
        echo ""

        # Show diff with colors
        if diff -u "$existing" "$temp_new" | head -100; then
            echo -e "${GREEN}(no changes)${NC}"
        else
            # diff returns non-zero when files differ, which is expected
            true
        fi

        rm "$temp_new"
    else
        echo -e "${DIM}New file (does not exist yet):${NC}"
        echo ""
        echo -e "${GREEN}$new_content${NC}" | head -50
        if [ $(echo "$new_content" | wc -l) -gt 50 ]; then
            echo -e "${DIM}... (truncated, $(echo "$new_content" | wc -l) total lines)${NC}"
        fi
    fi

    echo ""
}

# Show diff for skill files
show_skill_diff() {
    local src="$1"
    local dst="$2"
    local label="$3"

    if [ -f "$dst" ]; then
        echo ""
        echo -e "${BOLD}━━━ $label ━━━${NC}"
        echo -e "${DIM}Comparing: $dst (existing) vs $src (new)${NC}"
        echo ""

        if diff -u "$dst" "$src" 2>/dev/null | head -50; then
            echo -e "${GREEN}(files are identical)${NC}"
        fi
        echo ""
    fi
}

# Preview all changes before installation
preview_changes() {
    log_info "Previewing changes..."

    # We need to clone the repo to a temp location to compare
    TEMP_DIR=$(mktemp -d)
    log_info "Fetching repository for comparison..."
    git clone --quiet --depth 1 "$REPO_URL" "$TEMP_DIR/claudestrator" 2>/dev/null || {
        log_error "Failed to fetch repository for preview"
        exit 1
    }

    local has_changes=false
    local changes_summary=()

    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}                    CHANGE PREVIEW                          ${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"

    # 1. Preview CLAUDE.md changes
    echo ""
    echo -e "${BOLD}1. CLAUDE.md Configuration${NC}"

    local claude_md_addition=$(generate_claude_md_content)

    if [ -f "$CLAUDE_MD" ]; then
        if grep -q "## Claudestrator" "$CLAUDE_MD"; then
            echo -e "   ${YELLOW}Already contains Claudestrator section${NC}"
            echo -e "   ${DIM}Will append new section (manual cleanup of old section needed)${NC}"
        else
            echo -e "   ${GREEN}Will append Claudestrator configuration${NC}"
        fi
        has_changes=true
        changes_summary+=("Append to $CLAUDE_MD")

        echo ""
        echo -e "${DIM}Content to be appended:${NC}"
        echo -e "${GREEN}$claude_md_addition${NC}"
    else
        echo -e "   ${GREEN}Will create new file: $CLAUDE_MD${NC}"
        has_changes=true
        changes_summary+=("Create $CLAUDE_MD")

        echo ""
        echo -e "${DIM}Content:${NC}"
        echo -e "${GREEN}$claude_md_addition${NC}"
    fi

    # 2. Preview command symlinks
    echo ""
    echo -e "${BOLD}2. Slash Commands (symlinks to $COMMANDS_DIR)${NC}"

    local cmd_changes=()
    local cmd_skips=()

    for cmd_file in "$TEMP_DIR/claudestrator/commands"/*.md; do
        if [ -f "$cmd_file" ]; then
            local cmd_name=$(basename "$cmd_file")
            local target="$COMMANDS_DIR/$cmd_name"

            if [ -e "$target" ] && [ ! -L "$target" ]; then
                cmd_skips+=("$cmd_name (exists as regular file, will skip)")
            elif [ -L "$target" ]; then
                local link_target=$(readlink "$target" 2>/dev/null || echo "")
                if [[ "$link_target" == *"claudestrator"* ]]; then
                    cmd_changes+=("$cmd_name (update existing symlink)")
                else
                    cmd_skips+=("$cmd_name (symlink to non-claudestrator target)")
                fi
            else
                cmd_changes+=("$cmd_name (new)")
                has_changes=true
            fi
        fi
    done

    if [ ${#cmd_changes[@]} -gt 0 ]; then
        echo -e "   ${GREEN}Will install:${NC}"
        for cmd in "${cmd_changes[@]}"; do
            echo -e "     + $cmd"
        done
        changes_summary+=("Install ${#cmd_changes[@]} commands")
    fi

    if [ ${#cmd_skips[@]} -gt 0 ]; then
        echo -e "   ${YELLOW}Will skip (conflicts):${NC}"
        for cmd in "${cmd_skips[@]}"; do
            echo -e "     - $cmd"
        done
    fi

    # 3. Preview skill files
    echo ""
    echo -e "${BOLD}3. Skills (copy to $SKILLS_DIR)${NC}"

    local skill_new=()
    local skill_diff=()
    local skill_same=()

    for skill_subdir in implementation design quality support maintenance security domain; do
        local src_dir="$TEMP_DIR/claudestrator/skills/$skill_subdir"
        local dst_dir="$SKILLS_DIR/$skill_subdir"

        if [ -d "$src_dir" ]; then
            for skill_file in "$src_dir"/*.md; do
                if [ -f "$skill_file" ]; then
                    local skill_name=$(basename "$skill_file")
                    local target="$dst_dir/$skill_name"

                    if [ ! -f "$target" ]; then
                        skill_new+=("$skill_subdir/$skill_name")
                        has_changes=true
                    elif ! diff -q "$target" "$skill_file" > /dev/null 2>&1; then
                        skill_diff+=("$skill_subdir/$skill_name")
                    else
                        skill_same+=("$skill_subdir/$skill_name")
                    fi
                fi
            done
        fi
    done

    if [ ${#skill_new[@]} -gt 0 ]; then
        echo -e "   ${GREEN}New skills to install:${NC}"
        for skill in "${skill_new[@]}"; do
            echo -e "     + $skill"
        done
        changes_summary+=("Install ${#skill_new[@]} new skills")
    fi

    if [ ${#skill_diff[@]} -gt 0 ]; then
        echo -e "   ${YELLOW}Existing skills with differences (will NOT overwrite):${NC}"
        for skill in "${skill_diff[@]}"; do
            echo -e "     ~ $skill"
        done

        if confirm "   Show diffs for modified skills?"; then
            for skill in "${skill_diff[@]}"; do
                local skill_subdir=$(dirname "$skill")
                local skill_name=$(basename "$skill")
                show_skill_diff \
                    "$TEMP_DIR/claudestrator/skills/$skill" \
                    "$SKILLS_DIR/$skill" \
                    "Skill: $skill"
            done
        fi
    fi

    if [ ${#skill_same[@]} -gt 0 ]; then
        echo -e "   ${DIM}Unchanged (${#skill_same[@]} skills already up to date)${NC}"
    fi

    # 4. Preview directory creation
    echo ""
    echo -e "${BOLD}4. Directory Structure${NC}"

    local dirs_to_create=()
    [ ! -d "$CLAUDE_DIR/journal" ] && dirs_to_create+=("$CLAUDE_DIR/journal")
    [ ! -d "$CLAUDE_DIR/memories" ] && dirs_to_create+=("$CLAUDE_DIR/memories")
    [ ! -d "$COMMANDS_DIR" ] && dirs_to_create+=("$COMMANDS_DIR")
    [ ! -d "$SKILLS_DIR" ] && dirs_to_create+=("$SKILLS_DIR")

    if [ ${#dirs_to_create[@]} -gt 0 ]; then
        echo -e "   ${GREEN}Will create:${NC}"
        for dir in "${dirs_to_create[@]}"; do
            echo -e "     + $dir/"
        done
        has_changes=true
    else
        echo -e "   ${DIM}All directories already exist${NC}"
    fi

    # Summary
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}                       SUMMARY                              ${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    if [ ${#changes_summary[@]} -gt 0 ]; then
        echo -e "Changes to be made:"
        for change in "${changes_summary[@]}"; do
            echo -e "  • $change"
        done
    else
        echo -e "${DIM}No changes needed - everything is up to date${NC}"
    fi

    echo ""
    echo -e "${YELLOW}Note: Existing files will NOT be overwritten.${NC}"
    echo -e "${YELLOW}A backup of CLAUDE.md will be created before modification.${NC}"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        log_dry_run "Dry run complete. No changes were made."
        exit 0
    fi

    if ! confirm "Proceed with installation?"; then
        log_info "Installation cancelled."
        exit 0
    fi
}

# Create backup of existing CLAUDE.md
backup_claude_md() {
    if [ -f "$CLAUDE_MD" ]; then
        local backup="$CLAUDE_MD.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CLAUDE_MD" "$backup"
        log_info "Backed up existing CLAUDE.md to: $backup"
    fi
}

# Clone or update repository
install_repo() {
    log_info "Installing Claudestrator repository..."

    if [ -d "$REPO_DIR" ]; then
        log_info "Repository exists, pulling latest changes..."
        cd "$REPO_DIR"
        git pull --quiet origin main
        cd - > /dev/null
        log_success "Repository updated"
    else
        # If we already cloned to temp dir, move it
        if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR/claudestrator" ]; then
            mv "$TEMP_DIR/claudestrator" "$REPO_DIR"
            log_success "Repository installed to $REPO_DIR"
        else
            git clone --quiet "$REPO_URL" "$REPO_DIR"
            log_success "Repository cloned to $REPO_DIR"
        fi
    fi
}

# Install slash commands
install_commands() {
    log_info "Installing slash commands..."

    mkdir -p "$COMMANDS_DIR"

    local installed=0
    local skipped=0

    for cmd_file in "$REPO_DIR"/commands/*.md; do
        if [ -f "$cmd_file" ]; then
            local cmd_name=$(basename "$cmd_file")
            local target="$COMMANDS_DIR/$cmd_name"

            if [ -e "$target" ] && [ ! -L "$target" ]; then
                log_warning "Skipping $cmd_name (file exists and is not a symlink)"
                ((skipped++))
            else
                # Remove old symlink if exists
                [ -L "$target" ] && rm "$target"

                # Create symlink (use relative path for local, absolute for global)
                if [ "$INSTALL_MODE" = "global" ]; then
                    ln -sf "$cmd_file" "$target"
                else
                    ln -sf "../$REPO_DIR/commands/$cmd_name" "$target"
                fi
                ((installed++))
            fi
        fi
    done

    log_success "Commands installed: $installed, skipped: $skipped"
}

# Install skills
install_skills() {
    log_info "Installing skills..."

    mkdir -p "$SKILLS_DIR"

    local installed=0
    local skipped=0

    # Copy skill subdirectories
    for skill_subdir in implementation design quality support maintenance security domain; do
        local src_dir="$REPO_DIR/skills/$skill_subdir"
        local dst_dir="$SKILLS_DIR/$skill_subdir"

        if [ -d "$src_dir" ]; then
            mkdir -p "$dst_dir"

            for skill_file in "$src_dir"/*.md; do
                if [ -f "$skill_file" ]; then
                    local skill_name=$(basename "$skill_file")
                    local target="$dst_dir/$skill_name"

                    if [ -f "$target" ]; then
                        # File exists - skip (already showed diff in preview)
                        ((skipped++))
                    else
                        cp "$skill_file" "$target"
                        ((installed++))
                    fi
                fi
            done
        fi
    done

    # Copy top-level skill files
    for top_file in skill_manifest.md skill_template.md agent_model_selection.md; do
        local src="$REPO_DIR/skills/$top_file"
        local dst="$SKILLS_DIR/$top_file"

        if [ -f "$src" ]; then
            if [ -f "$dst" ]; then
                ((skipped++))
            else
                cp "$src" "$dst"
                ((installed++))
            fi
        fi
    done

    log_success "Skills installed: $installed, skipped: $skipped"
}

# Configure CLAUDE.md
configure_claude_md() {
    log_info "Configuring CLAUDE.md..."

    backup_claude_md

    # Create directory if needed
    mkdir -p "$(dirname "$CLAUDE_MD")"

    # Append configuration
    generate_claude_md_content >> "$CLAUDE_MD"

    log_success "CLAUDE.md configured"
}

# Create initial directory structure
create_directories() {
    log_info "Creating directory structure..."

    mkdir -p "$CLAUDE_DIR/journal"
    mkdir -p "$CLAUDE_DIR/memories"

    log_success "Directories created"
}

# Uninstall function
uninstall() {
    log_info "Uninstalling Claudestrator..."

    set_paths

    echo ""
    echo "This will remove:"
    echo "  - Repository: $REPO_DIR"
    echo "  - Command symlinks in: $COMMANDS_DIR"
    echo "  - Skills will NOT be removed (may have customizations)"
    echo "  - CLAUDE.md section will NOT be removed (manual cleanup needed)"
    echo ""

    if ! confirm "Proceed with uninstallation?"; then
        log_info "Uninstallation cancelled."
        exit 0
    fi

    # Remove command symlinks
    if [ -d "$COMMANDS_DIR" ]; then
        for cmd in orchestrate deorchestrate checkpoint status tasks skills prdgen audit-skills skill-enhance; do
            local target="$COMMANDS_DIR/$cmd.md"
            if [ -L "$target" ]; then
                local link_target=$(readlink "$target")
                if [[ "$link_target" == *"claudestrator"* ]]; then
                    rm "$target"
                    log_info "Removed: $target"
                fi
            fi
        done
    fi

    # Remove repository
    if [ -d "$REPO_DIR" ]; then
        rm -rf "$REPO_DIR"
        log_info "Removed: $REPO_DIR"
    fi

    log_success "Uninstallation complete"
    echo ""
    log_warning "Manual cleanup needed:"
    echo "  - Remove Claudestrator section from $CLAUDE_MD"
    echo "  - Remove skills from $SKILLS_DIR if desired"
}

# Print summary
print_summary() {
    echo ""
    echo -e "${GREEN}${BOLD}========================================${NC}"
    echo -e "${GREEN}${BOLD}  Claudestrator installed successfully!${NC}"
    echo -e "${GREEN}${BOLD}========================================${NC}"
    echo ""
    echo "Installation location: $REPO_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Start Claude Code in your project directory"
    echo "  2. Run ${BOLD}/prdgen${NC} to generate a PRD (optional)"
    echo "  3. Run ${BOLD}/orchestrate${NC} to start orchestration"
    echo ""
    echo "Verify installation with ${BOLD}/help${NC} - you should see Claudestrator commands."
    echo ""
    echo "Documentation: https://github.com/bladehstream/claudestrator"
    echo ""
}

# Main installation flow
main() {
    echo ""
    echo -e "${BOLD}Claudestrator Installer${NC}"
    echo "========================"
    echo ""

    if [ "$UNINSTALL" = true ]; then
        uninstall
        exit 0
    fi

    check_prerequisites
    set_paths

    # Preview changes and get confirmation
    preview_changes

    echo ""
    log_info "Installing..."
    echo ""

    install_repo
    install_commands
    install_skills
    create_directories
    configure_claude_md
    print_summary
}

# Run main
main
