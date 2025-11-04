# 🔄 Restart Streamlit Instructions

## ⚠️ CRITICAL: You MUST restart Streamlit to apply code changes!

Your Streamlit server is currently running **old code** that doesn't have the GitHub repository fixes.

---

## 🛑 Step 1: Stop Current Streamlit

In the terminal running Streamlit, press:
```
Ctrl + C
```

Or close the terminal tab labeled "streamlit" in VS Code.

---

## ✅ Step 2: Set Environment Variables

Open a **new PowerShell terminal** and run:

```powershell
$env:GITHUB_TOKEN = "your_github_token_here"
$env:GITHUB_DEFAULT_OWNER = "Hemesh11"
$env:GITHUB_DEFAULT_REPO = "Autotasker-AI"
```

**Replace `"your_github_token_here"`** with your actual GitHub Personal Access Token.

---

## 🚀 Step 3: Start Streamlit (in the same terminal)

```powershell
streamlit run frontend/streamlit_app.py
```

**IMPORTANT**: Run this in the **SAME terminal window** where you just set the environment variables!

---

## 🧪 Step 4: Test Both Fixed Issues

### Test 1: Calendar Event Scheduling (FIXED ✅)
Try this prompt:
```
Add event "Team sync" on Friday at 3pm
```

**Expected Result**: Should schedule successfully without "too many values to unpack" error

---

### Test 2: GitHub Commits Without Repository (FIXED ✅)
Try this prompt:
```
Summarize my commits from last week
```

**Expected Result**: Should auto-detect your repository (Hemesh11/Autotasker-AI) and fetch commits

---

## 📊 What Should You See in Logs

### For Calendar (when scheduling):
```
✅ Task 'Team sync' scheduled successfully!
```

### For GitHub (in execution):
```
INFO - Converted 'username'='Hemesh11' to repository pattern 'Hemesh11/*' for auto-detect
INFO - Using most recent repository: Hemesh11/Autotasker-AI
INFO - Retrieved 3 commits from Hemesh11/Autotasker-AI
```

---

## 🔍 If GitHub Still Fails

Check these in order:

### 1. Verify Environment Variables Are Set
In the terminal, run:
```powershell
echo $env:GITHUB_TOKEN
echo $env:GITHUB_DEFAULT_OWNER
echo $env:GITHUB_DEFAULT_REPO
```

Should output your token and "Hemesh11" and "Autotasker-AI"

### 2. Check .env File
Open `config/.env` and verify:
```
GITHUB_TOKEN=your_token_here
GITHUB_DEFAULT_OWNER=Hemesh11
GITHUB_DEFAULT_REPO=Autotasker-AI
```

### 3. Clear Streamlit Cache
In Streamlit UI, press `C` key, then click "Clear cache"

### 4. Check Logs for Normalization
Look in the Streamlit output for lines like:
- "Converted 'username'... to repository pattern"
- "Using most recent repository"
- "Using repository from environment"

If you DON'T see these logs, the old code is still running!

---

## 🆘 Last Resort: Hard Restart

1. Close ALL terminals
2. Close VS Code completely
3. Reopen VS Code
4. Open new PowerShell terminal
5. Set env vars again
6. Run streamlit

---

## ✨ What Was Fixed

### Issue 1: Calendar Scheduling ✅
**Problem**: `day, time = schedule_value.split(':')` expected 2 parts but got 3 (`FRI:03:00`)

**Fix**: Changed to `day, hour, minute = schedule_value.split(':')` to handle 3-part format

**Files Changed**:
- `backend/scheduler.py` (lines 159-173 and 217-223)

### Issue 2: GitHub Repository Parameter ✅
**Problem**: Planner outputs varied formats (username, owner, single names) that weren't normalized

**Fix**: Added comprehensive normalization in `github_task_node`:
- Converts `username` → `username/*` pattern for auto-detect
- Combines `owner` + `repo_name` → `owner/repo`
- Normalizes single values like `"Hemesh11"` → `"Hemesh11/*"`
- Falls back to `GITHUB_DEFAULT_OWNER/REPO` from environment

**Files Changed**:
- `backend/langgraph_runner.py` (lines 257-291)

---

## 📞 Still Having Issues?

Paste the following:
1. Output from `echo $env:GITHUB_TOKEN` (first 10 chars only!)
2. Full Streamlit execution log for the failing prompt
3. Any error messages shown in terminal

I'll help debug further!
