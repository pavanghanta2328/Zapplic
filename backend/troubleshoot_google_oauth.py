"""
Google OAuth Troubleshooting Script
Run this in the backend folder to diagnose Google OAuth issues.

Common Errors:
- invalid_grant: Code already used, expired, or redirect URI mismatch
- Client ID not found: Missing GOOGLE_CLIENT_ID in .env
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("\n" + "="*70)
print("🔍 GOOGLE OAUTH CONFIGURATION & TROUBLESHOOTING")
print("="*70 + "\n")

# Check environment variables
requirements = {
    "GOOGLE_CLIENT_ID": "Google OAuth Client ID",
    "GOOGLE_CLIENT_SECRET": "Google OAuth Client Secret",
    "GOOGLE_REDIRECT_URI": "Google OAuth Redirect URI",
    "FRONTEND_REDIRECT_URL": "Frontend OAuth Callback URL",
}

all_good = True

for env_var, description in requirements.items():
    value = os.getenv(env_var)
    if value:
        # Show only first 40 chars for secrets
        display_value = value[:40] + "..." if len(value) > 40 else value
        print(f"✅ {env_var}")
        print(f"   📝 {display_value}\n")
    else:
        print(f"❌ {env_var} - NOT SET")
        print(f"   ⚠️  {description} is missing\n")
        all_good = False

print("="*70 + "\n")

if all_good:
    print("✅ All environment variables are configured!\n")
    
    # Verify redirect URI matches
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    expected = "http://localhost:8000/api/auth/google/callback"
    
    if redirect_uri == expected:
        print("✅ Redirect URI matches expected format\n")
    else:
        print("⚠️  Redirect URI may not be correct:")
        print(f"   Current:  {redirect_uri}")
        print(f"   Expected: {expected}\n")
    
    print("If you're still getting 'invalid_grant' error:\n")
    print("STEP 1: Check Google Cloud Console")
    print("   1. Go to https://console.cloud.google.com/apis/credentials")
    print("   2. Find your OAuth 2.0 Client ID")
    print("   3. Click on it to edit")
    print("   4. Under 'Authorized redirect URIs' add:")
    print("      http://localhost:8000/api/auth/google/callback\n")
    
    print("STEP 2: Clear browser cookies & cache")
    print("   - Each OAuth code can only be used ONCE")
    print("   - Codes expire after 10 minutes")
    print("   - If you see 'invalid_grant', the code was likely already used\n")
    
    print("STEP 3: Test the OAuth setup")
    print("   Visit these URLs in your browser (while backend is running):\n")
    print("   Config check: http://localhost:8000/api/auth/google/config")
    print("   Get login URL: http://localhost:8000/api/auth/google/test-login\n")
    
    print("STEP 4: Watch the backend console")
    print("   The backend will show detailed logs during OAuth flow:")
    print("   📝 Starting Google OAuth callback")
    print("   🔄 Exchanging auth code for tokens")
    print("   🔐 Verifying ID token\n")
    
    print("If still failing after these steps:")
    print("   → Regenerate OAuth credentials in Google Console")
    print("   → Make sure you're using HTTPS for production (localhost OK for dev)\n")
    
else:
    print("❌ Missing required environment variables!")
    print("\nSetup Instructions:")
    print("="*70 + "\n")
    
    print("1. Create OAuth 2.0 Credentials in Google Cloud Console:")
    print("   a. Go to https://console.cloud.google.com/apis/credentials")
    print("   b. Click '+ Create Credentials' → OAuth 2.0 Client IDs")
    print("   c. Choose 'Web application'")
    print("   d. Add authorized redirect URIs:")
    print("      http://localhost:8000/api/auth/google/callback")
    print("   e. Copy Client ID and Client Secret\n")
    
    print("2. Add to your .env file in the backend folder:")
    print("   GOOGLE_CLIENT_ID=your_very_long_client_id_here")
    print("   GOOGLE_CLIENT_SECRET=your_client_secret_here")
    print("   GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback")
    print("   FRONTEND_REDIRECT_URL=http://localhost:3000/oauth/callback\n")
    
    print("3. Restart the backend server (Ctrl+C and run uvicorn again)")
    print("4. Then run this script again to verify\n")

print("="*70 + "\n")
print("📚 Common invalid_grant Solutions:")
print("   • Clear browser cookies completely")
print("   • Try in incognito/private mode")
print("   • Wait 10+ minutes and try again (code expires)")
print("   • Verify redirect URI matches EXACTLY in Google Console")
print("   • Check that credentials haven't been revoked\n")
print("="*70 + "\n")
