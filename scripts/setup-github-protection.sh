#!/bin/bash

# GitHub Branch Protection Setup Script
# This script provides instructions and commands to set up branch protection rules
# for the radio001 project workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛡️  GitHub Branch Protection Setup${NC}"
echo "=================================="
echo

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Get repository information
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [[ $REPO_URL =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
    OWNER="${BASH_REMATCH[1]}"
    REPO="${BASH_REMATCH[2]}"
    REPO="${REPO%.git}"  # Remove .git suffix if present
else
    echo -e "${RED}❌ Error: Could not determine GitHub repository from remote URL${NC}"
    echo "Make sure you have a GitHub remote configured"
    exit 1
fi

echo -e "${GREEN}📋 Repository Information${NC}"
echo "Owner: $OWNER"
echo "Repository: $REPO"
echo "URL: https://github.com/$OWNER/$REPO"
echo

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✅ GitHub CLI detected${NC}"
    USE_CLI=true
else
    echo -e "${YELLOW}⚠️  GitHub CLI not found${NC}"
    echo "Install GitHub CLI for automated setup: https://cli.github.com/"
    USE_CLI=false
fi
echo

echo -e "${BLUE}🔧 Branch Protection Configuration${NC}"
echo "=================================="
echo

if [ "$USE_CLI" = true ]; then
    echo -e "${GREEN}Option 1: Automated Setup (Recommended)${NC}"
    echo "Run the following commands to set up branch protection:"
    echo

    # Check if user is authenticated
    if gh auth status &>/dev/null; then
        echo -e "${GREEN}✅ GitHub CLI is authenticated${NC}"
        echo

        echo "Setting up branch protection for 'main' branch..."
        echo

        # Create the branch protection rule
cat << 'EOF'
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Lint & Type Check","Integration Tests","Security Scan"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":false}' \
  --field restrictions=null
EOF

        echo
        echo "Setting up branch protection for 'develop' branch..."
        echo

cat << 'EOF'
gh api repos/:owner/:repo/branches/develop/protection \
  --method PUT \
  --field required_status_checks='{"strict":false,"contexts":["Lint & Type Check","Build Validation","Docker Build Test"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews=null \
  --field restrictions=null
EOF

        echo
        echo -e "${YELLOW}💡 Would you like to run these commands now? (y/n)${NC}"
        read -r response

        if [[ $response =~ ^[Yy]$ ]]; then
            echo "Setting up main branch protection..."

            # First check if develop branch exists, create if not
            if ! git ls-remote --heads origin develop | grep -q develop; then
                echo "Creating develop branch..."
                git checkout -b develop 2>/dev/null || git checkout develop
                git push -u origin develop
            fi

            # Set up main branch protection
            if gh api "repos/$OWNER/$REPO/branches/main/protection" \
              --method PUT \
              --field required_status_checks='{"strict":true,"contexts":["Lint & Type Check","Integration Tests","Security Scan"]}' \
              --field enforce_admins=true \
              --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true,"require_code_owner_reviews":false}' \
              --field restrictions=null 2>/dev/null; then
                echo -e "${GREEN}✅ Main branch protection configured${NC}"
            else
                echo -e "${YELLOW}⚠️  Could not set main branch protection (branch may not exist yet)${NC}"
            fi

            # Set up develop branch protection (lighter rules)
            if gh api "repos/$OWNER/$REPO/branches/develop/protection" \
              --method PUT \
              --field required_status_checks='{"strict":false,"contexts":["Lint & Type Check","Build Validation"]}' \
              --field enforce_admins=false \
              --field required_pull_request_reviews=null \
              --field restrictions=null 2>/dev/null; then
                echo -e "${GREEN}✅ Develop branch protection configured${NC}"
            else
                echo -e "${YELLOW}⚠️  Could not set develop branch protection${NC}"
            fi
        fi

    else
        echo -e "${YELLOW}⚠️  GitHub CLI not authenticated${NC}"
        echo "Run: gh auth login"
    fi
else
    echo -e "${YELLOW}Option 1: Install GitHub CLI (Recommended)${NC}"
    echo "Install GitHub CLI and re-run this script for automated setup"
    echo "https://cli.github.com/"
fi

echo
echo -e "${BLUE}Option 2: Manual Setup via GitHub Web Interface${NC}"
echo "=============================================="
echo
echo "1. Go to your repository settings:"
echo "   https://github.com/$OWNER/$REPO/settings/branches"
echo
echo -e "${GREEN}For 'main' branch:${NC}"
echo "   ✅ Require pull request reviews before merging"
echo "   ✅ Require status checks to pass before merging"
echo "   ✅ Require branches to be up to date before merging"
echo "   ✅ Required status checks:"
echo "      - Lint & Type Check"
echo "      - Integration Tests"
echo "      - Security Scan"
echo "   ✅ Restrict pushes that create files larger than 100 MB"
echo "   ✅ Do not allow bypassing the above settings"
echo
echo -e "${GREEN}For 'develop' branch (lighter rules):${NC}"
echo "   ❌ No pull request reviews required"
echo "   ✅ Require status checks to pass before merging"
echo "   ❌ Do not require branches to be up to date"
echo "   ✅ Required status checks:"
echo "      - Lint & Type Check"
echo "      - Build Validation"
echo "      - Docker Build Test"
echo

echo -e "${BLUE}🚀 Workflow Summary${NC}"
echo "=================="
echo
echo -e "${GREEN}✅ What this setup provides:${NC}"
echo "• Protected main branch - requires PR reviews and full CI"
echo "• Protected develop branch - lighter checks for fast development"
echo "• Automated quality gates before production deployment"
echo "• Clear development workflow with quick feedback"
echo
echo -e "${GREEN}✅ Development flow:${NC}"
echo "1. Work on develop branch (quick CI feedback)"
echo "2. Create PR: develop → main (full validation)"
echo "3. Merge to main triggers production deployment"
echo

echo -e "${BLUE}📚 Next Steps${NC}"
echo "============"
echo
echo "1. Set up branch protection (above)"
echo "2. Read the workflow guide: cat WORKFLOW.md"
echo "3. Initialize develop branch: npm run workflow:init"
echo "4. Start developing: npm run dev"
echo
echo -e "${GREEN}🎉 Happy coding!${NC}"
