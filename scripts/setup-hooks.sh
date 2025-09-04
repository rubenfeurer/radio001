#!/bin/bash

# Git Hooks Setup Script
# Ensures Husky git hooks are properly installed after npm install

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Setting up Git hooks...${NC}"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Not in a git repository, skipping hook setup${NC}"
    exit 0
fi

# Check if this is a CI environment
if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ -n "$GITLAB_CI" ] || [ -n "$JENKINS_URL" ]; then
    echo -e "${YELLOW}⚠️  CI environment detected, skipping hook setup${NC}"
    exit 0
fi

# Check if .husky directory exists
if [ ! -d ".husky" ]; then
    echo -e "${RED}❌ .husky directory not found${NC}"
    exit 1
fi

# Function to install hook
install_hook() {
    local hook_name=$1
    local source_file=".husky/${hook_name}"
    local target_file=".git/hooks/${hook_name}"

    if [ -f "$source_file" ]; then
        echo -e "${BLUE}📎 Installing ${hook_name} hook...${NC}"
        cp "$source_file" "$target_file"
        chmod +x "$target_file"
        echo -e "${GREEN}✅ ${hook_name} hook installed${NC}"
    else
        echo -e "${YELLOW}⚠️  ${source_file} not found, skipping${NC}"
    fi
}

# Install hooks
echo -e "${BLUE}📋 Installing Git hooks...${NC}"

install_hook "pre-commit"
install_hook "commit-msg"
install_hook "pre-push"

# Verify installation
echo -e "${BLUE}🔍 Verifying installation...${NC}"

if [ -x ".git/hooks/pre-commit" ]; then
    echo -e "${GREEN}✅ pre-commit hook installed and executable${NC}"
else
    echo -e "${RED}❌ pre-commit hook not properly installed${NC}"
fi

if [ -x ".git/hooks/commit-msg" ]; then
    echo -e "${GREEN}✅ commit-msg hook installed and executable${NC}"
else
    echo -e "${RED}❌ commit-msg hook not properly installed${NC}"
fi

echo -e "${GREEN}🎉 Git hooks setup complete!${NC}"
echo ""
echo -e "${BLUE}ℹ️  What this enables:${NC}"
echo "  • Automatic linting and formatting on commit"
echo "  • TypeScript type checking (branch-aware)"
echo "  • Conventional commit message validation"
echo "  • Prevents broken code from being committed"
echo ""
echo -e "${YELLOW}💡 To test the hooks:${NC}"
echo "  1. Make a code change"
echo "  2. git add <file>"
echo "  3. git commit -m \"feat: your message\""
echo "  4. Watch the pre-commit checks run!"
