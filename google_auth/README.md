# Google OAuth Setup Instructions

## Setup Guide for Gmail API Integration

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Configure the OAuth consent screen if prompted
4. Choose "Desktop application" as application type
5. Download the credentials JSON file
6. Rename it to `credentials.json` and place in this directory

### 3. Required Scopes

The application requires these OAuth scopes:
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/drive.file`

### 4. First Run

On first run, the application will:
1. Open a browser window for OAuth authorization
2. Ask you to sign in with your Google account
3. Request permission for the required scopes
4. Save the authorization token as `token.json` in this directory

## Important Notes

### Single Credentials File for Multiple APIs

**The SAME `credentials.json` file works for multiple Google APIs:**
- Gmail API
- Google Calendar API  
- Google Drive API (if added later)

**You only need to:**
1. Enable additional APIs in the same Google Cloud project
2. The OAuth scopes will be requested as needed
3. Separate token files will be created (e.g., `calendar_token.json`)

### File Structure
```
google_auth/
├── credentials.json     ← One file for all Google APIs
├── token.json          ← Gmail access token
└── calendar_token.json ← Calendar access token (auto-created)
```

### Troubleshooting

**"File not found" errors:**
- Ensure `credentials.json` is in the correct location
- Check file permissions

**Authentication errors:**
- Delete `token.json` to force re-authorization
- Verify OAuth scopes in Google Cloud Console
- Check that Gmail API is enabled

**Quota exceeded:**
- Monitor API usage in Google Cloud Console
- Implement rate limiting in your application
- Consider upgrading quota limits if needed

google_auth/
├── credentials.json     ← ONE file for Gmail AND Calendar
├── token.json          ← Gmail token (if Gmail setup)
└── calendar_token.json ← Calendar token (auto-created)