# dinnerflow/frontend/auth.py
import bcrypt
import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "dinner-db"),
        database=os.getenv("POSTGRES_DB", "dinnerflow"),
        user=os.getenv("POSTGRES_USER", "dinneruser"),
        password=os.getenv("POSTGRES_PASSWORD", "password")
    )

def verify_password(plain_password, hashed_password):
    # Check if the provided password matches the stored hash
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def hash_password(plain_password):
    # Generate a secure hash
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')

def authenticate_user(email, password):
    """Returns user dict if valid, None otherwise."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Fetch ID, Email, Hash, Name, AND Admin Status
        cur.execute("SELECT id, email, password_hash, full_name, is_admin FROM users WHERE email = %s", (email,))
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
        print(f"Auth Error: {e}")
        return None
    finally:
        conn.close()

# RENAME FIX: We are standardizing on 'register_user' to match app.py
def register_user(email, password, full_name):
    """Returns new user_id or None."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        hashed = hash_password(password)
        cur.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s) RETURNING id",
            (email, hashed, full_name)
        )
        new_id = cur.fetchone()[0]
        conn.commit()

        # --- TRIGGER N8N ONBOARDING ---
        try:
            webhook_url = "https://n8n.joeltimm.dev/webhook/welcome-email"

            # Send data to n8n
            requests.post(webhook_url, json={
                "user_id": new_id,
                "email": email,
                "full_name": full_name,
                "first_name": full_name.split()[0] if full_name else "Chef" 
            }, timeout=2) # 2s timeout so UI doesn't hang if n8n is slow

        except Exception as we:
            # Log error but DO NOT fail the registration. 
            # The user should still be able to log in even if the email fails.
            print(f"Warning: Failed to trigger onboarding webhook: {we}")
        # ------------------------------

        return new_id
    except Exception as e:
        print(f"Registration Error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()
