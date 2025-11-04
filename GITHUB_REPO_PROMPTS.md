# 🐙 GitHub Repository Prompts Guide

## Understanding Auto-Detection

When you say **"my GitHub commits"** without specifying a repo, the system:
1. ✅ Authenticates with your GitHub token
2. ✅ Fetches your repositories sorted by most recently updated
3. ✅ Picks the **most recent one** (currently: `Hemesh11/Autotasker-AI`)

This is a **smart feature** that saves you from typing the repo name every time!

---

## 📋 List ALL Your Repositories

Use these prompts to see all your repos:

```
✅ List my GitHub repositories
✅ Show all my repos
✅ Get my GitHub repos
✅ Show me all my repositories
✅ List all repos for Hemesh11
✅ Show repositories for Hemesh11
```

This will list ALL your repos with:
- Repository name
- Description
- Primary language
- Stars, forks
- Last updated date

---

## 🎯 Specify a Specific Repository

### Method 1: Include repo in prompt
```
✅ Summarize commits from Hemesh11/ProjectX from last week
✅ Get commits from Hemesh11/OtherRepo yesterday
✅ Show issues in Hemesh11/MyApp
✅ Get my commits from Hemesh11/SpecificRepo
```

### Method 2: Just use repo name (if you own it)
```
✅ Summarize my commits from ProjectX
✅ Get commits from OtherRepo last week
```

---

## 🔄 How Auto-Detection Works

### When you say:
```
"Summarize my GitHub commits from last week"
```

### The system does:
```
1. No repository specified → trigger auto-detect
2. Check: Is user authenticated? ✅ Yes (Hemesh11)
3. Fetch: Get Hemesh11's repos sorted by last update
4. Select: Pick most recent → Hemesh11/Autotasker-AI
5. Execute: Get commits from Hemesh11/Autotasker-AI
```

---

## 💡 Pro Tips

### See All Repos First
```
1️⃣ List my GitHub repositories
   (See all your repos)

2️⃣ Summarize commits from Hemesh11/SpecificRepo from last week
   (Choose one and get commits)
```

### Change Default Repository
If you want a different repo to be the default, update your `.env`:

```bash
GITHUB_DEFAULT_OWNER=Hemesh11
GITHUB_DEFAULT_REPO=YourPreferredRepo
```

Then restart Streamlit:
```powershell
.\restart_streamlit_with_env.ps1
```

### Get Commits from Multiple Repos
```
✅ Get commits from Hemesh11/Repo1 and Hemesh11/Repo2 from last week
```

---

## 📊 Repository Operations

### 1. List Repositories
```
✅ List my GitHub repositories
✅ Show all my repos
✅ Get repositories for Hemesh11
```

### 2. Repository Info
```
✅ Get info about Hemesh11/Autotasker-AI
✅ Show stats for my repository
✅ Repository details for Hemesh11/ProjectX
```

### 3. Get Commits
```
✅ Get commits from Hemesh11/Autotasker-AI from last week
✅ Show my commits from yesterday (auto-detects recent repo)
✅ Summarize commits from ProjectX
```

### 4. Get Issues
```
✅ Show issues in Hemesh11/Autotasker-AI
✅ Get open issues from my repository
✅ List closed issues for Hemesh11/ProjectX
```

### 5. Search Repositories
```
✅ Search for Python automation repositories
✅ Find AI repositories on GitHub
✅ Search for repos with "machine learning"
```

---

## 🎯 Common Scenarios

### Morning Check
```
List my GitHub repositories and send me a summary
```
**Result**: Email with all your repos, their languages, stars, and last update

### Weekly Review - Specific Repo
```
Summarize commits from Hemesh11/ProjectX from last week and email the report
```

### Weekly Review - All Activity
```
Get my GitHub commits from all repositories from last week
```

### Project Status
```
Get info about Hemesh11/Autotasker-AI and show open issues
```

### Discover New Projects
```
Search for Python automation repositories and email top 10
```

---

## 🚨 Why It Auto-Detected Autotasker-AI

Your most recent activity was on `Hemesh11/Autotasker-AI`, so the system correctly picked it!

To use a different repo, either:
1. **Specify in prompt**: `"Get commits from Hemesh11/OtherRepo"`
2. **Change default**: Update `.env` file
3. **List all first**: `"List my repos"` then choose one

---

## ✅ Testing the New Feature

Try these prompts now:

```bash
# See all your repos
List my GitHub repositories

# Then pick one for commits
Summarize commits from Hemesh11/[YourRepoName] from last week
```

---

## 🔧 Environment Variables

Your current setup in `.env`:
```bash
GITHUB_TOKEN=ghp_your_token
GITHUB_DEFAULT_OWNER=Hemesh11
GITHUB_DEFAULT_REPO=Autotasker-AI
```

This means:
- ✅ Authenticated as: **Hemesh11**
- ✅ Default repo: **Autotasker-AI** (used when no repo specified AND can't auto-detect)
- ✅ Auto-detect: **Most recent repo** (overrides default if available)

---

## 📝 Quick Reference Card

| Your Prompt | What Happens |
|-------------|--------------|
| "my commits" | Auto-detects most recent repo |
| "my commits from ProjectX" | Uses Hemesh11/ProjectX |
| "commits from Hemesh11/Repo1" | Uses exact repo specified |
| "list my repos" | Shows ALL your repositories |
| (no prompt with empty config) | Uses GITHUB_DEFAULT_REPO from .env |

---

🎉 **The system is working perfectly!** It auto-detected your most active repo. Now you can:
1. List all repos to see everything
2. Specify repo names for specific projects
3. Or just keep using auto-detect for your current project
