#!/usr/bin/env bash
# Install OCR-docs git hooks.
#
# Sets `core.hooksPath` to point at ocr-docs-brain/hooks/, so the hooks are
# tracked in git (survive clones) and version-controlled like everything
# else in the brain.
#
# Idempotent — running twice is a no-op.
#
# Uninstall: git config --unset core.hooksPath
# Bypass single commit: git commit --no-verify

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="ocr-docs-brain/hooks"

if [ ! -d "$REPO_ROOT/$HOOKS_DIR" ]; then
    echo "install: hooks directory not found at $HOOKS_DIR" >&2
    exit 1
fi

# Make sure each hook file is executable (no-op on Windows; required on Unix).
for hook in "$REPO_ROOT/$HOOKS_DIR"/*; do
    name="$(basename "$hook")"
    if [ -f "$hook" ] && [ "$name" != "install.sh" ] && [ "$name" != "README.md" ]; then
        chmod +x "$hook" 2>/dev/null || true
    fi
done

CURRENT="$(git config core.hooksPath || echo "")"
if [ "$CURRENT" = "$HOOKS_DIR" ]; then
    echo "OK install: hooks already installed (core.hooksPath = $HOOKS_DIR)"
else
    git config core.hooksPath "$HOOKS_DIR"
    echo "OK install: core.hooksPath set to $HOOKS_DIR"
fi

echo ""
echo "  Active hooks:"
for hook in "$REPO_ROOT/$HOOKS_DIR"/*; do
    name="$(basename "$hook")"
    if [ -f "$hook" ] && [ "$name" != "install.sh" ] && [ "$name" != "README.md" ]; then
        echo "    - $name"
    fi
done
echo ""
echo "  Bypass a single commit:  git commit --no-verify"
echo "  Uninstall hooks entirely: git config --unset core.hooksPath"
echo ""
echo "  Doctrine: ADR-003 Self-Checking Infrastructure"
