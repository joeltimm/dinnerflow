#!/usr/bin/env python3
"""
One-time Gmail OAuth token generator.

Mirrors the pattern used in ~/calendar_bot/scripts/generate_google_tokens.py.

Usage:
  1. Download an OAuth 2.0 client secret from Google Cloud Console:
       APIs & Services → Credentials → Create → OAuth client ID → Desktop app
       Save as: client_secret.json in this directory (or any path)

  2. Run this script (requires a browser or printable auth URL):
       python backend/scripts/generate_gmail_token.py

  3. Follow the prompt to authorize via browser.

  4. Token is saved to: GOOGLE_AUTH_PATH/token_{email_suffix}.json
     (defaults to /app/google_auth/token_{suffix}.json, or ./google_auth/ locally)

The token auto-refreshes at runtime — you only need to run this once,
or again if the refresh token is ever revoked.

Required OAuth scope: https://www.googleapis.com/auth/gmail.send
"""
import json
import os
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main():
    # ── Locate the client secret file ─────────────────────────────────────────
    script_dir = Path(__file__).parent
    default_secret = script_dir / "client_secret.json"

    secret_path = Path(
        os.environ.get("GOOGLE_CLIENT_SECRET", str(default_secret))
    )

    if not secret_path.exists():
        print(
            f"\n❌  Client secret not found at: {secret_path}\n\n"
            "  1. Go to https://console.cloud.google.com/apis/credentials\n"
            "  2. Create → OAuth client ID → Desktop app\n"
            "  3. Download JSON and save it as:\n"
            f"     {secret_path}\n"
            "  Or set GOOGLE_CLIENT_SECRET=<path> and re-run.\n"
        )
        sys.exit(1)

    # ── Determine sender email + output path ──────────────────────────────────
    sender_email = os.environ.get("SENDER_EMAIL", "").strip()
    if not sender_email:
        sender_email = input("Enter the Gmail address to send mail from: ").strip()

    suffix = sender_email.split("@")[0]
    auth_dir = Path(os.environ.get("GOOGLE_AUTH_PATH", str(script_dir / "google_auth")))
    auth_dir.mkdir(parents=True, exist_ok=True)
    token_path = auth_dir / f"token_{suffix}.json"

    # ── Run OAuth flow ─────────────────────────────────────────────────────────
    print(f"\n🔑  Starting OAuth flow for: {sender_email}")
    print("    A browser window will open (or copy/paste the URL if running headless).\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)

    # run_local_server opens a browser; use run_console() if no display available
    try:
        creds = flow.run_local_server(port=0, open_browser=True)
    except Exception:
        print("Could not open browser — falling back to console flow.")
        creds = flow.run_console()

    # ── Save token ─────────────────────────────────────────────────────────────
    token_path.write_text(creds.to_json())
    print(f"\n✅  Token saved to: {token_path}")
    print(
        "\n   This token will auto-refresh at runtime.\n"
        "   Mount the google_auth/ directory as a Docker volume so tokens persist.\n"
    )


if __name__ == "__main__":
    main()
