---
description: Sync local fork with upstream main branch
---

This workflow syncs your local repository with the upstream repository's `main` branch. It ensures you have the latest stable updates while preserving your local configuration.

1. Configure upstream remote if missing
// turbo
2. Fetch latest updates from upstream
// turbo
3. Merge upstream changes into your local main branch
4. Push updates to your origin

```bash
# Step 1: Check and add upstream remote if it doesn't exist
if ! git remote | grep -q "upstream"; then
    git remote add upstream https://github.com/ZhuLinsen/daily_stock_analysis.git
    echo "Added upstream remote."
else
    echo "Upstream remote already exists."
fi

# Step 2: Fetch the latest specific stable updates from upstream
git fetch upstream

# Step 3: Merge upstream/main into local main
# We explicitly use upstream/main to avoid pulling in any testing branches
echo "Merging upstream/main..."
if git merge upstream/main; then
    echo "Merge successful."
else
    echo "Merge conflict detected. Please resolve conflicts manually in VS Code, then run 'git commit' and 'git push'."
    exit 1
fi

# Step 3.5: Local Verification (Prevent CI failures)
echo "Running local verification..."
# Check for Python syntax errors
if ! python -m py_compile src/config.py src/analyzer.py data_provider/*.py; then
   echo "❌ Validation Failed: Syntax errors detected."
   exit 1
fi

# Check for crucial imports (smoke test)
if ! python -c "from src.config import get_config; from data_provider import DataFetcherManager; print('Imports OK')"; then
   echo "❌ Validation Failed: Import verification failed."
   exit 1
fi
echo "✅ Local verification passed."

# Step 4: Push the updated code to your personal GitHub repository
git push origin main
echo "Sync complete! Your repository is now up to date."

# Step 5: Check GitHub Action Status (Conditional)
echo "Checking GitHub Action status..."
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
TARGET_REPO="SunnRayy/daily_stock_analysis"

if [[ "$REMOTE_URL" == *"$TARGET_REPO"* ]]; then
    if command -v gh &> /dev/null; then
        echo "Configuring gh for $TARGET_REPO..."
        gh repo set-default "$TARGET_REPO"
        
        echo "Recent Workflow Runs:"
        gh run list --limit 3
    else
        echo "⚠️  gh CLI not installed. Skipping automated status check."
        echo "Please check status manually: https://github.com/$TARGET_REPO/actions"
    fi
else
    echo "Current repo remote ($REMOTE_URL) does not match $TARGET_REPO. Skipping gh status check."
fi
```
