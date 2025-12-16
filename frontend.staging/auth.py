# dinnerflow/frontend/auth.py
import bcrypt
import psycopg2
import os
import requests  # Added missing import
import logging

# Configure logging to keep console clean but informative
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Establishes connection to the Postgres database."""
    try:
        return psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "dinner-db"),
            database=os.getenv("POSTGRES_DB", "dinnerflow"),
            user=os.getenv("POSTGRES_USER", "dinneruser"),
            password=os.getenv("POSTGRES_PASSWORD", "password")
        )
    except Exception as e:
        logging.error(f"Database Connection Failed: {e}")
        return None

def verify_password(plain_password, hashed_password):
    """Checks if the provided password matches the stored hash."""
    if not plain_password or not hashed_password:
        return False
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def hash_password(plain_password):
    """Generates a secure bcrypt hash for storage."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

def authenticate_user(email, password):
    """
    Validates credentials.
    Returns: User dict (id, email, name, is_admin) if valid, None otherwise.
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cur = conn.cursor()
        # Fetch ID, Email, Hash, Name, AND Admin Status
        cur.execute(
            "SELECT id, email, password_hash, full_name, is_admin FROM users WHERE email = %s", 
            (email,)
        )
        user = cur.fetchone()

        if user:
            user_id, db_email, db_hash, db_name, is_admin = user
            if verify_password(password, db_hash):
                return {
                    "id": user_id,
                    "email": db_email,
                    "name": db_name,
                    "is_admin": is_admin
                }
        return None
    except Exception as e:
        logging.error(f"Auth Error for {email}: {e}")
        return None
    finally:
        if conn: conn.close()

def register_user(email, password, full_name):
    """
    Registers a new user and triggers the Welcome webhook.
    Returns: new user_id or None on failure.
    """
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cur = conn.cursor()
        hashed = hash_password(password)
        
        # Insert new user
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s) RETURNING id",
            (email, hashed, full_name)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        logging.info(f"New user registered: {email} (ID: {new_id})")

        # --- TRIGGER N8N ONBOARDING ---
        # This sends a "Welcome" email via n8n without blocking the UI
        try:
            webhook_url = "https://n8n.joeltimm.dev/webhook/welcome-email"
            
            payload = {
                "user_id": new_id,
                "email": email,
                "full_name": full_name,
                "first_name": full_name.split()[0] if full_name else "Chef"
            }

            # 2s timeout prevents the signup form from hanging if n8n is slow
            requests.post(webhook_url, json=payload, timeout=2)
            logging.info(f"Triggered onboarding webhook for {email}")

        except Exception as we:
            # We log the error but do NOT fail the registration. 
            # The user account is created; the email just failed.
            logging.warning(f"Failed to trigger onboarding webhook: {we}")
        # ------------------------------

        return new_id

    except psycopg2.IntegrityError:
        # This handles duplicate emails gracefully
        logging.warning(f"Registration attempt failed: Email {email} already exists.")
        conn.rollback()
        return None
    except Exception as e:
        logging.error(f"Registration Error: {e}")
        conn.rollback()
        return None
    finally:
        if conn: conn.close()
