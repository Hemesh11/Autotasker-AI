# Google Calendar Setup Guide

## Quick Setup for Calendar Integration

### 🚨 IMPORTANT: You Only Need ONE credentials.json File!

**If you already set up Gmail, you DON'T need new credentials!**
- Gmail and Calendar use the SAME `credentials.json` file
- Just enable Calendar API in the same Google Cloud project

### 1. Enable Calendar API (in your existing project)

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Select the SAME project** you used for Gmail
3. **Enable Calendar API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

**That's it! Your existing `google_auth/credentials.json` will work for both Gmail AND Calendar.**

### 2. File Structure (should already exist)

```
google_auth/
├── credentials.json     ← SAME file for Gmail AND Calendar
├── token.json          ← Gmail token  
└── calendar_token.json ← Calendar token (auto-created)
```

### 3. Config (probably already set)

Your `config/.env` should have:

```env
# Google APIs (works for BOTH Gmail and Calendar)
GOOGLE_CREDENTIALS_PATH=google_auth/credentials.json
GOOGLE_TOKEN_PATH=google_auth/token.json
GOOGLE_CALENDAR_TOKEN_PATH=google_auth/calendar_token.json
```

### 4. Test It!

```bash
# In your autotasker environment:
python agents/calendar_agent.py
```

**Or through the main app:**

```
"mark a meeting in google calendar on 13th august 9 am, give reminder"
```

### 5. OAuth Flow

**First time:**
1. Your browser will open
2. Sign in to Google
3. Allow calendar access
4. Token gets saved automatically

**After that:** Works automatically!

### 6. Calendar Scopes

The agent requests these permissions:
- `https://www.googleapis.com/auth/calendar` - Full calendar access
- `https://www.googleapis.com/auth/calendar.events` - Create/edit events

### 7. Example Commands

- "Schedule dentist appointment next Tuesday 2 PM"
- "Add team meeting every Monday 10 AM with 30 min reminder"  
- "Create birthday reminder for mom on March 15th"
- "Show me my calendar events for next week"
- "Mark a meeting in google calendar on 13th august 9 am, give reminder"

### Troubleshooting

**Error: "Calendar service not initialized"**
- Missing credentials.json file
- Run OAuth flow again

**Error: "Credentials file not found"**
- Download credentials.json from Google Cloud Console
- Place in `google_auth/` folder

**Error: "Calendar API not available"**
- Install: `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
