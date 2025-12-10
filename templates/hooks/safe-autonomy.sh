#!/bin/bash
# Claudestrator Safe Autonomy Hook
#
# This hook auto-approves safe operations and blocks dangerous ones.
# Used when autonomy level is set to "Full Autonomy" in orchestrator.
#
# Install location: .claude/hooks/safe-autonomy.sh
# Version: 1.0

set -e

# Read JSON input from stdin
input=$(cat)

# Extract tool name and input
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
tool_input=$(echo "$input" | jq -r '.tool_input // empty')

# Get project directory (where .claude/ lives)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Helper: Check if path is within project directory
is_safe_path() {
    local path="$1"
    local resolved_path

    # Handle relative paths
    if [[ "$path" != /* ]]; then
        resolved_path="$PROJECT_DIR/$path"
    else
        resolved_path="$path"
    fi

    # Resolve to absolute path (handle .. and symlinks)
    resolved_path=$(realpath -m "$resolved_path" 2>/dev/null || echo "$resolved_path")

    # Check if within project
    [[ "$resolved_path" == "$PROJECT_DIR"* ]]
}

# Helper: Output allow decision
allow() {
    echo '{"decision":"allow"}'
    exit 0
}

# Helper: Output deny decision with message
deny() {
    local message="$1"
    echo "{\"decision\":\"deny\",\"message\":\"$message\"}"
    exit 0
}

# Helper: Let default permission system handle (no decision)
passthrough() {
    exit 0
}

# ============================================
# TOOL-SPECIFIC RULES
# ============================================

case "$tool_name" in

    # ------------------------------------------
    # READ-ONLY TOOLS - Always allow
    # ------------------------------------------
    "Read"|"Glob"|"Grep"|"WebSearch")
        # Check for sensitive paths
        file_path=$(echo "$tool_input" | jq -r '.file_path // .path // empty')

        # Block sensitive system paths
        if [[ "$file_path" == *"/.ssh/"* ]] || \
           [[ "$file_path" == *"/.aws/"* ]] || \
           [[ "$file_path" == *"/.gnupg/"* ]] || \
           [[ "$file_path" == "/etc/shadow"* ]] || \
           [[ "$file_path" == "/etc/passwd"* ]]; then
            deny "Reading sensitive system files is blocked"
        fi

        allow
        ;;

    # ------------------------------------------
    # EDIT TOOL - Allow within project only
    # ------------------------------------------
    "Edit"|"Write"|"NotebookEdit")
        file_path=$(echo "$tool_input" | jq -r '.file_path // .notebook_path // empty')

        # Block sensitive files
        if [[ "$file_path" == *".env"* ]] || \
           [[ "$file_path" == *"credentials"* ]] || \
           [[ "$file_path" == *"secrets"* ]] || \
           [[ "$file_path" == *".pem" ]] || \
           [[ "$file_path" == *".key" ]]; then
            deny "Editing sensitive files (.env, credentials, secrets, keys) is blocked"
        fi

        # Block system paths
        if [[ "$file_path" == "/etc/"* ]] || \
           [[ "$file_path" == "/usr/"* ]] || \
           [[ "$file_path" == "/bin/"* ]] || \
           [[ "$file_path" == "/sbin/"* ]] || \
           [[ "$file_path" == "$HOME/.bashrc" ]] || \
           [[ "$file_path" == "$HOME/.zshrc" ]] || \
           [[ "$file_path" == "$HOME/.profile" ]]; then
            deny "Editing system files is blocked"
        fi

        # Must be within project directory
        if ! is_safe_path "$file_path"; then
            deny "Editing files outside project directory is blocked"
        fi

        allow
        ;;

    # ------------------------------------------
    # BASH - Selective approval
    # ------------------------------------------
    "Bash")
        command=$(echo "$tool_input" | jq -r '.command // empty')

        # === ALWAYS DENY ===

        # Privilege escalation
        if [[ "$command" =~ ^sudo ]] || \
           [[ "$command" =~ ^su[[:space:]] ]] || \
           [[ "$command" =~ ^doas[[:space:]] ]]; then
            deny "Privilege escalation commands (sudo/su) are blocked"
        fi

        # Dangerous deletions
        if [[ "$command" =~ rm[[:space:]]+-rf?[[:space:]]+/ ]] || \
           [[ "$command" =~ rm[[:space:]]+-rf?[[:space:]]+\* ]] || \
           [[ "$command" =~ rm[[:space:]]+-rf?[[:space:]]+\.\. ]]; then
            deny "Dangerous recursive deletion is blocked"
        fi

        # Pipe to shell (code injection risk)
        if [[ "$command" =~ curl.*\|.*sh ]] || \
           [[ "$command" =~ curl.*\|.*bash ]] || \
           [[ "$command" =~ wget.*\|.*sh ]] || \
           [[ "$command" =~ wget.*\|.*bash ]]; then
            deny "Piping downloaded content to shell is blocked"
        fi

        # System modification
        if [[ "$command" =~ ^chmod[[:space:]]+777 ]] || \
           [[ "$command" =~ ^chown[[:space:]] ]] || \
           [[ "$command" =~ ^chgrp[[:space:]] ]]; then
            deny "System permission modifications are blocked"
        fi

        # Disk operations
        if [[ "$command" =~ ^dd[[:space:]] ]] || \
           [[ "$command" =~ ^mkfs ]] || \
           [[ "$command" =~ ^fdisk ]]; then
            deny "Disk operations are blocked"
        fi

        # Network listeners (potential backdoor)
        if [[ "$command" =~ nc[[:space:]]+-l ]] || \
           [[ "$command" =~ netcat.*-l ]]; then
            deny "Starting network listeners is blocked"
        fi

        # === ALWAYS ALLOW ===

        # Git commands
        if [[ "$command" =~ ^git[[:space:]] ]]; then
            # Block force push to main/master
            if [[ "$command" =~ push.*--force.*main ]] || \
               [[ "$command" =~ push.*--force.*master ]] || \
               [[ "$command" =~ push.*-f.*main ]] || \
               [[ "$command" =~ push.*-f.*master ]]; then
                deny "Force pushing to main/master is blocked"
            fi
            allow
        fi

        # Package managers (read/install operations)
        if [[ "$command" =~ ^npm[[:space:]] ]] || \
           [[ "$command" =~ ^npx[[:space:]] ]] || \
           [[ "$command" =~ ^yarn[[:space:]] ]] || \
           [[ "$command" =~ ^pnpm[[:space:]] ]] || \
           [[ "$command" =~ ^pip[[:space:]] ]] || \
           [[ "$command" =~ ^pip3[[:space:]] ]] || \
           [[ "$command" =~ ^poetry[[:space:]] ]] || \
           [[ "$command" =~ ^cargo[[:space:]] ]] || \
           [[ "$command" =~ ^go[[:space:]] ]]; then
            allow
        fi

        # Runtime/interpreter commands
        if [[ "$command" =~ ^node[[:space:]] ]] || \
           [[ "$command" =~ ^python[[:space:]] ]] || \
           [[ "$command" =~ ^python3[[:space:]] ]] || \
           [[ "$command" =~ ^ruby[[:space:]] ]] || \
           [[ "$command" =~ ^php[[:space:]] ]] || \
           [[ "$command" =~ ^java[[:space:]] ]] || \
           [[ "$command" =~ ^javac[[:space:]] ]]; then
            allow
        fi

        # Build/test commands
        if [[ "$command" =~ ^make[[:space:]] ]] || \
           [[ "$command" =~ ^cmake[[:space:]] ]] || \
           [[ "$command" =~ ^gradle[[:space:]] ]] || \
           [[ "$command" =~ ^mvn[[:space:]] ]] || \
           [[ "$command" =~ ^dotnet[[:space:]] ]]; then
            allow
        fi

        # Safe file operations
        if [[ "$command" =~ ^mkdir[[:space:]] ]] || \
           [[ "$command" =~ ^touch[[:space:]] ]] || \
           [[ "$command" =~ ^cp[[:space:]] ]] || \
           [[ "$command" =~ ^mv[[:space:]] ]] || \
           [[ "$command" =~ ^ls[[:space:]] ]] || \
           [[ "$command" =~ ^ls$ ]] || \
           [[ "$command" =~ ^pwd$ ]] || \
           [[ "$command" =~ ^cat[[:space:]] ]] || \
           [[ "$command" =~ ^head[[:space:]] ]] || \
           [[ "$command" =~ ^tail[[:space:]] ]] || \
           [[ "$command" =~ ^wc[[:space:]] ]] || \
           [[ "$command" =~ ^find[[:space:]] ]] || \
           [[ "$command" =~ ^grep[[:space:]] ]] || \
           [[ "$command" =~ ^rg[[:space:]] ]] || \
           [[ "$command" =~ ^tree[[:space:]] ]] || \
           [[ "$command" =~ ^tree$ ]]; then
            allow
        fi

        # Environment/info commands
        if [[ "$command" =~ ^echo[[:space:]] ]] || \
           [[ "$command" =~ ^printf[[:space:]] ]] || \
           [[ "$command" =~ ^env$ ]] || \
           [[ "$command" =~ ^which[[:space:]] ]] || \
           [[ "$command" =~ ^whereis[[:space:]] ]] || \
           [[ "$command" =~ ^whoami$ ]] || \
           [[ "$command" =~ ^date$ ]] || \
           [[ "$command" =~ ^uname ]]; then
            allow
        fi

        # Docker (non-destructive)
        if [[ "$command" =~ ^docker[[:space:]]+(build|run|ps|images|logs|exec|compose) ]]; then
            allow
        fi

        # === PASSTHROUGH (ask user) ===
        # Anything not explicitly allowed or denied
        passthrough
        ;;

    # ------------------------------------------
    # TASK TOOL - Allow agent spawns
    # ------------------------------------------
    "Task")
        allow
        ;;

    # ------------------------------------------
    # WEB TOOLS - Selective
    # ------------------------------------------
    "WebFetch")
        url=$(echo "$tool_input" | jq -r '.url // empty')

        # Allow documentation and common dev domains
        if [[ "$url" =~ ^https://(docs\.|api\.|raw\.)?(github\.com|githubusercontent\.com|npmjs\.com|pypi\.org|crates\.io|pkg\.go\.dev|developer\.mozilla\.org|stackoverflow\.com|anthropic\.com) ]]; then
            allow
        fi

        # Passthrough for other URLs (let user decide)
        passthrough
        ;;

    # ------------------------------------------
    # DEFAULT - Passthrough to user
    # ------------------------------------------
    *)
        passthrough
        ;;
esac
