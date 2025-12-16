import streamlit as st
from sqlalchemy import text
import time
import os
from todoist_api_python.api import TodoistAPI

def render_preferences(conn, user_id, encrypt_token, decrypt_token):
    st.header("⚙️ Your Rules")
    st.caption("We won’t fight you. Just tell us how you eat.")

    # --- FETCH DATA ---
    prefs_df = conn.query(
        "SELECT dietary_preferences FROM users WHERE id = :uid",
        params={"uid": user_id}, ttl=0
    )

    integrations_df = conn.query(
        "SELECT api_token, target_list_id FROM user_integrations "
        "WHERE user_id = :uid AND provider = 'todoist'",
        params={"uid": user_id}, ttl=0
    )

    dietary = prefs_df.iloc[0]["dietary_preferences"] if not prefs_df.empty else ""
    encrypted_token = integrations_df.iloc[0]["api_token"] if not integrations_df.empty else None
    saved_list_id = integrations_df.iloc[0]["target_list_id"] if not integrations_df.empty else None

    token = decrypt_token(encrypted_token) if encrypted_token else ""

    # --- DIETARY PROFILE ---
    with st.container(border=True):
        st.subheader("🍽️ How you eat")

        new_prefs = st.text_area(
            "Dietary rules, allergies, hard no's",
            value=dietary,
            height=120,
            placeholder="No shellfish. Low-carb-ish. Cilantro is banned."
        )

        if st.button("Lock it in", type="primary"):
            with conn.session as s:
                s.execute(
                    text("UPDATE users SET dietary_preferences = :p WHERE id = :uid"),
                    {"p": new_prefs, "uid": user_id}
                )
                s.commit()
            st.toast("Saved. The ogre remembers 🧠")

    # --- TODOIST ---
    with st.container(border=True):
        st.subheader("🛒 Grocery brain (Todoist)")

        new_token = st.text_input(
            "Todoist API Token",
            value=token,
            type="password"
        )

        if st.button("Verify & save token"):
            try:
                TodoistAPI(new_token).get_projects()
                with conn.session as s:
                    s.execute(
                        text("""
                        INSERT INTO user_integrations (user_id, provider, api_token)
                        VALUES (:uid, 'todoist', :t)
                        ON CONFLICT (user_id, provider)
                        DO UPDATE SET api_token = EXCLUDED.api_token
                        """),
                        {"uid": user_id, "t": encrypt_token(new_token)}
                    )
                    s.commit()
                st.success("Connected. Ingredients now have a destiny.")
                time.sleep(0.5)
                st.rerun()
            except Exception:
                st.error("That token is cursed. Try again.")
