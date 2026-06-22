"""
Email service — sends through the host Postfix relay over SMTP.

Postfix (on joelrockslinuxserver) is configured with relayhost smtp.gmail.com,
so it smarthosts outbound mail via Gmail. The host's mynetworks trusts the
container subnet, so this hop needs no auth and no TLS — Postfix handles TLS +
SASL auth upstream. Configure via SMTP_HOST / SMTP_PORT / SMTP_FROM (config.py).
"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode

from config import get_settings

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, html_body: str) -> None:
    """Low-level send via the host Postfix SMTP relay."""
    settings = get_settings()
    from_addr = settings.smtp_from or settings.sender_email

    msg = MIMEMultipart("alternative")
    msg["To"] = to
    msg["From"] = from_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.ehlo()
        # The relay enforces STARTTLS even from trusted networks. We reach it via
        # the host-gateway IP, which won't match the relay's cert CN, so verify is
        # off — this hop is host-local and trusted by IP (mynetworks). The real
        # cert-verified TLS + auth happens upstream (Postfix -> smtp.gmail.com).
        if smtp.has_extn("starttls"):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            smtp.starttls(context=ctx)
            smtp.ehlo()
        smtp.send_message(msg, from_addr=from_addr, to_addrs=[to])

    logger.info("Email sent to %s | subject: %s", to, subject)


# ── Email templates ───────────────────────────────────────────────────────────

def _email_footer(settings, unsub_url: str | None = None) -> str:
    """Standard compliance footer for all emails."""
    privacy_url = f"{settings.app_base_url}/privacy"
    settings_url = f"{settings.app_base_url}/settings"

    unsub_line = ""
    if unsub_url:
        unsub_line = (
            f'<a href="{unsub_url}" style="color:#999;text-decoration:underline;">'
            'Unsubscribe</a> · '
        )

    return f"""
        <div style="padding:16px 32px; background:#f5f5f5; text-align:center;
                    color:#999; font-size:12px; line-height:1.8;">
          Iron Skillet · Self-hosted meal planning<br>
          {unsub_line}<a href="{settings_url}" style="color:#999;text-decoration:underline;">Email preferences</a>
          · <a href="{privacy_url}" style="color:#999;text-decoration:underline;">Privacy policy</a>
        </div>
    """


def send_welcome_email(to_email: str, user_name: str) -> None:
    """
    Onboarding email sent on registration.
    Replicates the 'Ironskillet Registration Welcome Email' n8n workflow.
    """
    settings = get_settings()
    prefs_url = f"{settings.app_base_url}/settings"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                 background:#f9f9f9; margin:0; padding:40px 20px;">
      <div style="max-width:560px; margin:0 auto; background:#fff;
                  border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.08);">

        <div style="background:#1a1a2e; padding:32px; text-align:center;">
          <h1 style="color:#e2b96f; margin:0; font-size:28px; letter-spacing:1px;">
            Iron Skillet
          </h1>
          <p style="color:#aaa; margin:8px 0 0; font-size:14px;">
            Your personal AI-powered recipe vault
          </p>
        </div>

        <div style="padding:32px;">
          <h2 style="color:#1a1a2e; margin-top:0;">
            Welcome, {user_name}!
          </h2>
          <p style="color:#444; line-height:1.6;">
            You're all set up. Here's how to get the most out of Iron Skillet:
          </p>

          <ol style="color:#444; line-height:2;">
            <li><strong>Add recipes</strong> — paste a URL or type your own</li>
            <li><strong>Set your dietary preferences</strong> — so the AI knows what to suggest</li>
            <li><strong>Connect Todoist</strong> — to sync ingredient shopping lists automatically</li>
            <li><strong>Use Instant Chef</strong> — get AI meal ideas, click one, and the recipe is
                scraped and saved for you</li>
          </ol>

          <h3 style="color:#1a1a2e;">Connecting Todoist (optional)</h3>
          <p style="color:#444; line-height:1.6;">
            To enable automatic grocery list syncing:
          </p>
          <ol style="color:#444; line-height:2;">
            <li>Go to <a href="https://todoist.com/app/settings/integrations/developer"
                style="color:#e2b96f;">Todoist → Settings → Integrations → Developer</a></li>
            <li>Copy your <strong>API token</strong></li>
            <li>Paste it in your <a href="{prefs_url}" style="color:#e2b96f;">Preferences page</a></li>
          </ol>

          <div style="text-align:center; margin-top:32px;">
            <a href="{prefs_url}"
               style="background:#e2b96f; color:#1a1a2e; padding:14px 28px;
                      border-radius:8px; text-decoration:none; font-weight:700;
                      display:inline-block;">
              Set Up Preferences →
            </a>
          </div>
        </div>

        {_email_footer(settings)}
      </div>
    </body>
    </html>
    """

    _send(to_email, "Welcome to Iron Skillet", html)


def send_meal_plan_email(
    to_email: str,
    user_name: str,
    user_id: int,
    recipes: list[dict],
    select_token: str,
    unsub_token: str = "",
) -> None:
    """
    Weekly meal plan email with recipe cards and 'Select This' action links.
    Replicates the 'Ironskillet' n8n workflow email output.

    Each recipe dict: {"title": str, "url": str, "description": str, "is_favorite": bool}
    select_token: HMAC-signed token for this user (from services/chef.py) embedded in links.
    """
    settings = get_settings()

    def recipe_card(r: dict) -> str:
        badge = (
            '<span style="background:#e2b96f;color:#1a1a2e;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:700;">⭐ Favourite</span>'
            if r.get("is_favorite")
            else '<span style="background:#4a90d9;color:#fff;padding:3px 8px;'
            'border-radius:4px;font-size:11px;font-weight:700;">🤖 AI Pick</span>'
        )
        btn_style = (
            "background:#1a1a2e; color:#e2b96f; padding:10px 20px;"
            "border-radius:6px; text-decoration:none; font-weight:700;"
            "font-size:14px; display:inline-block;"
        )
        if r.get("is_favorite"):
            # Already in the user's vault — link to the app instead of the
            # add/scrape action so it can't create a duplicate.
            action_html = (
                f'<a href="{settings.app_base_url}/recipes" style="{btn_style}">'
                "View in Iron Skillet →</a>"
            )
        else:
            params = urlencode({
                "token": select_token,
                "title": r["title"],
                "url": r.get("url", ""),
            })
            select_url = f"{settings.app_base_url}/api/chef/select-from-email?{params}"
            action_html = (
                f'<a href="{select_url}" style="{btn_style}">Add to My Recipes →</a>'
            )

        return f"""
        <div style="border:1px solid #eee; border-radius:10px; padding:20px;
                    margin-bottom:16px; background:#fff;">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <h3 style="margin:0 0 6px; color:#1a1a2e; font-size:17px;">{r['title']}</h3>
            {badge}
          </div>
          <p style="color:#666; margin:8px 0 12px; font-size:14px; line-height:1.5;">
            {r.get('description', '')}
          </p>
          {'<a href="' + r["url"] + '" style="color:#999;font-size:12px;">View source</a>' if r.get("url") else ''}
          <div style="margin-top:14px;">
            {action_html}
          </div>
        </div>
        """

    cards_html = "".join(recipe_card(r) for r in recipes)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                 background:#f9f9f9;margin:0;padding:40px 20px;">
      <div style="max-width:600px;margin:0 auto;background:#fff;
                  border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">

        <div style="background:#1a1a2e;padding:28px 32px;text-align:center;">
          <h1 style="color:#e2b96f;margin:0;font-size:26px;">🍽️ Your Meal Plan</h1>
          <p style="color:#aaa;margin:6px 0 0;font-size:14px;">
            Curated just for you, {user_name}
          </p>
        </div>

        <div style="padding:28px 32px;">
          <p style="color:#444;margin:0 0 20px;line-height:1.6;">
            Here are this week's meal ideas based on your preferences.
            Click <strong>Add to My Recipes</strong> on any card to save it and
            automatically sync the ingredients to your Todoist grocery list.
          </p>

          {cards_html}
        </div>

        {_email_footer(settings, unsub_url=f"{settings.app_base_url}/api/account/unsubscribe?token={unsub_token}" if unsub_token else None)}
      </div>
    </body>
    </html>
    """

    _send(to_email, "Your Weekly Meal Ideas — Iron Skillet", html)
