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

# Step 4: Push the updated code to your personal GitHub repository
git push origin main
echo "Sync complete! Your repository is now up to date."
```
