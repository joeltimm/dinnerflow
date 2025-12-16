#dinnerflow/frontend/app.py
import streamlit as st
from sqlalchemy import text
from datetime import datetime
import pandas as pd
import os
import requests
import auth
import time
from cryptography.fernet import Fernet
from infisical_client import InfisicalClient, ClientSettings, GetSecretOptions
from todoist_api_python.api import TodoistAPI

# 1. SETUP PAGE CONFIG
st.set_page_config(
    page_title="Dinnerflow",
    page_icon="static/images/cooking-ogre-favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
#  SECURITY: FETCH KEY FROM INFISICAL
# ==========================================
@st.cache_resource
def get_encryption_key():
    """
    Fetches the FERNET_KEY from Infisical securely using a Service Token.
    """
    try:
        # 1. Initialize Client with Settings
        # We pass the token directly into 'access_token'
        settings = ClientSettings(
            site_url=os.getenv("INFISICAL_API_URL", "http://infisical-backend:8085"),
            access_token=os.getenv("INFISICAL_TOKEN") 
        )

        client = InfisicalClient(settings)

        # 2. Fetch the Secret
        # All arguments here are strictly named (keyword=value)
        secret = client.getSecret(options=GetSecretOptions(
            environment="prod",
            project_id="7705167e-1bee-47fc-8ccc-4a1522bcb7d3",
            secret_name="FERNET_KEY"
        ))

        return secret.secret_value
    except Exception as e:
        st.error(f"CRITICAL: Could not fetch encryption key. Error: {e}")
        st.stop()
        return None

# Load the key
ENCRYPTION_KEY = get_encryption_key()
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_token(token_str):
    if not token_str: return None
    # Encrypts and returns a string (not bytes)
    return cipher_suite.encrypt(token_str.encode()).decode()

def decrypt_token(token_enc):
    if not token_enc: return ""
    try:
        return cipher_suite.decrypt(token_enc.encode()).decode()
    except Exception:
        return ""

# ==========================================
#  SESSION STATE INITIALIZATION (MOVED TO TOP)
# ==========================================
# This guarantees these variables exist before ANY logic runs
if 'user' not in st.session_state:
    st.session_state.user = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "📥 Add Recipe"
if 'selected_recipe_id' not in st.session_state:
    st.session_state.selected_recipe_id = None

# ==========================================
#  AUTH SCREENS
# ==========================================

def login_screen():
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("static/images/cooking-ogre.png", use_container_width=True)

    with col2:
        st.title("Welcome to Dinnerflow")

        tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

        # LOGIN TAB
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Log In", type="primary"):
                    user = auth.authenticate_user(email, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid email or password")

        # SIGNUP TAB (Updated with Confirm Password)
        with tab_signup:
            with st.form("signup_form"):
                new_email = st.text_input("Email")
                new_name = st.text_input("Full Name (Optional)")
                new_pass = st.text_input("Password", type="password")
                new_pass_confirm = st.text_input("Confirm Password", type="password")

                submit_signup = st.form_submit_button("Create Account")

                if submit_signup:
                    if new_pass != new_pass_confirm:
                        st.error("Passwords do not match!")
                    elif len(new_pass) < 6:
                        st.error("Password must be at least 6 characters")
                    else:
                        # Now calling the correctly named function
                        success = auth.register_user(new_email, new_pass, new_name)
                        if success:
                            st.success("Account created! Please log in.")
                        else:
                            st.error("Email already exists.")

# ==========================================
#  MAIN APP
# ==========================================
def main_app():
    # --- DATABASE CONNECTION ---
    try:
        conn = st.connection("dinner_db", type="sql")
    except Exception as e:
        st.error("Connection Error")
        st.stop()

    # --- ADMIN IMPERSONATION LOGIC ---
    # Default: You see your own data
    effective_user_id = st.session_state.user['id']
    is_impersonating = False

    # --- HELPER FUNCTIONS ---
    def update_recipe(recipe_id, update_query, params):
        try:
            params['uid'] = effective_user_id
            secure_query = update_query + " AND user_id = :uid"
            with conn.session as s:
                s.execute(text(secure_query), params)
                s.commit()
            st.toast("Updated successfully!", icon="✅")
            st.rerun()
        except Exception as e:
            st.error(f"Update failed: {e}")

    def delete_recipe(recipe_id):
        try:
            df = conn.query("SELECT local_image_path FROM recipes WHERE id = :id AND user_id = :uid",
                            params={"id": recipe_id, "uid": effective_user_id}, ttl=0)
            if not df.empty:
                image_path = df.iloc[0]['local_image_path']
                with conn.session as s:
                    s.execute(text("DELETE FROM recipes WHERE id = :id AND user_id = :uid"),
                              params={"id": recipe_id, "uid": effective_user_id})
                    s.commit()
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception: pass
                st.session_state.selected_recipe_id = None
                st.toast("Recipe deleted!", icon="🗑️")
                st.rerun()
        except Exception as e:
            st.error(f"Delete failed: {e}")

    # ==========================
    # SIDEBAR NAVIGATION
    # ==========================
    with st.sidebar:
        #Logo
        st.image("static/images/cooking-ogre.png", use_container_width=True)
        # User Profile info
        st.write(f"👤 **{st.session_state.user['name'] or st.session_state.user['email']}**")

        # --- SUPER ADMIN PANEL ---
        if st.session_state.user.get('is_admin'):
            st.info("🔧 Admin Mode Active")

            # Fetch all users for the dropdown
            # SQL Injection Safe: No user input used in query
            all_users = conn.query("SELECT id, email FROM users ORDER BY id")

            # Create a dictionary for the dropdown: "email" -> ID
            user_options = {row['email']: row['id'] for index, row in all_users.iterrows()}

            # Add "Me" option
            my_email = st.session_state.user['email']

            selected_email = st.selectbox(
                "View as User:", 
                options=[my_email] + [e for e in user_options.keys() if e != my_email]
            )

            # If admin selects someone else, update the effective ID
            if selected_email != my_email:
                effective_user_id = user_options[selected_email]
                is_impersonating = True
                st.warning(f"Viewing data for: {selected_email}")

        if st.button("Log Out"):
            st.session_state.user = None
            st.rerun()
        st.markdown("---")

        # ----------------------------------------------------
        # NEW: Persistent Navigation (Fixes Tab Jumping)
        # ----------------------------------------------------
        nav_options = ["📥 Add Recipe", "📖 Cookbook", "📊 Dashboard", "⚙️ Settings"]

        # Calculate index safely so it doesn't crash if state is weird
        try:
            curr_index = nav_options.index(st.session_state.active_tab)
        except ValueError:
            curr_index = 0

        selected_nav = st.radio(
            "Menu", 
            nav_options, 
            index=curr_index, 
            label_visibility="collapsed"
        )

        # Update State
        st.session_state.active_tab = selected_nav

        st.markdown("---")

        # --- AUTO CHEF ---
        if st.button("🚀 Generate Email Plan", type="primary", use_container_width=True):
            with st.spinner("Compiling profile & Triggering n8n..."):
                try:
                    # 1. Get Target User Info
                    target_email = selected_email if is_impersonating else st.session_state.user['email']

                    # 2. Get Preferences (Fetch fresh from DB to be safe)
                    pref_df = conn.query("SELECT dietary_preferences FROM users WHERE id = :uid", 
                                         params={"uid": effective_user_id}, ttl=0)
                    user_prefs = pref_df.iloc[0]['dietary_preferences'] if not pref_df.empty else ""

                    # 3. Get Favorites (List of titles)
                    fav_df = conn.query("SELECT title FROM recipes WHERE user_id = :uid AND is_favorite = TRUE", 
                                        params={"uid": effective_user_id}, ttl=0)
                    favorites_list = fav_df['title'].tolist() if not fav_df.empty else []

                    # 4. Construct Payload
                    payload = {
                        "user_id": effective_user_id,
                        "email": target_email,
                        "preferences": user_prefs,
                        "favorites": favorites_list
                    }

                    # 5. Send POST Request
                    # Update this URL to your specific n8n Webhook URL
                    #test url:
                    #n8n_url = "https://n8n.joeltimm.dev/webhook-test/get-more-dinner"

                    #production url:
                    n8n_url = "https://n8n.joeltimm.dev/webhook/get-more-dinner"

                    response = requests.post(n8n_url, json=payload)

                    if response.status_code == 200:
                        st.toast(f"Plan sent to {target_email}!", icon="📧")
                    else:
                        st.error(f"n8n Error: {response.status_code}")

                except Exception as e:
                    st.error(f"Failed: {e}")

    # ==========================
    # MAIN CONTENT (Switched by State)
    # ==========================

    st.title(st.session_state.active_tab)

    # --- VIEW 1: ADD RECIPE ---
    if st.session_state.active_tab == "📥 Add Recipe":
        if is_impersonating:
            st.warning(f"⚠️ You are adding this recipe to another user's account (ID: {effective_user_id})")

        with st.form("recipe_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Recipe Title")
                url = st.text_input("Recipe URL")
            with col2:
                image_url = st.text_input("Image URL")
                source = st.selectbox("Method", ["manual", "family_classic", "experimental"])
            content = st.text_area("Content / Notes")
            submitted = st.form_submit_button("Save Recipe")

            if submitted and title:
                try:
                    with conn.session as s:
                        s.execute(
                            text("INSERT INTO recipes (title, source_url, local_image_path, full_text_content, entry_method, user_id) VALUES (:title, :url, :img, :content, :method, :uid)"),
                            params={
                                "title": title, "url": url, "img": image_url,
                                "content": content, "method": source,
                                "uid": effective_user_id
                            }
                        )
                        s.commit()
                    st.success(f"Saved '{title}'!")
                except Exception as e:
                    st.exception(e)
            elif submitted:
                st.error("⚠️ Please enter a Recipe Title.")

# --- VIEW 2: COOKBOOK ---
    elif st.session_state.active_tab == "📖 Cookbook":
        if st.session_state.selected_recipe_id is not None:
            # DETAIL VIEW
            recipe_id = st.session_state.selected_recipe_id
            df = conn.query("SELECT * FROM recipes WHERE id = :id AND user_id = :uid",
                            params={"id": recipe_id, "uid": effective_user_id}, ttl=0)

            if not df.empty:
                row = df.iloc[0]
                col_back, col_fav, col_cooked_date = st.columns([2, 2, 3])
                with col_back:
                    if st.button("← Back", use_container_width=True):
                        st.session_state.selected_recipe_id = None
                        st.rerun()
                with col_fav:
                    is_fav = st.checkbox("❤️ Favorite", value=bool(row['is_favorite']))
                    if is_fav != bool(row['is_favorite']):
                        update_recipe(recipe_id, "UPDATE recipes SET is_favorite = :fav WHERE id = :id", {"fav": is_fav, "id": recipe_id})
                with col_cooked_date:
                    if row['last_cooked']:
                        st.caption(f"📅 Last: **{str(row['last_cooked']).split()[0]}**")
                    else:
                        st.caption("📅 Never cooked")

                st.markdown(f"## {row['title']}")
                col_media, col_details = st.columns([1, 2], gap="large")
                with col_media:
                    if row['local_image_path']: st.image(row['local_image_path'], use_container_width=True)
                    st.markdown("---")
                    current_rating = int(row['rating']) if row['rating'] is not None else 0
                    new_rating = st.slider("Stars", 0, 5, value=current_rating, label_visibility="collapsed")
                    if new_rating != current_rating:
                        update_recipe(recipe_id, "UPDATE recipes SET rating = :r WHERE id = :id", {"r": new_rating, "id": recipe_id})
                    st.caption(f"Cooked {row['times_cooked'] or 0} times")
                    if st.button("🔥 I Cooked This Today!", use_container_width=True):
                        update_recipe(recipe_id, 
                                      "UPDATE recipes SET last_cooked = :date, times_cooked = COALESCE(times_cooked, 0) + 1 WHERE id = :id", 
                                      {"date": datetime.now(), "id": recipe_id})

                with col_details:
                    st.subheader("Chef's Notes")
                    with st.form(key=f"notes_{recipe_id}"):
                        updated_notes = st.text_area("Instructions:", value=row['full_text_content'] or "", height=300)
                        if st.form_submit_button("💾 Save Notes"):
                            update_recipe(recipe_id, "UPDATE recipes SET full_text_content = :n WHERE id = :id", {"n": updated_notes, "id": recipe_id})
                    st.write("")
                    with st.expander("⚠️ Danger Zone"):
                        if st.button("Delete Recipe", type="primary", use_container_width=True):
                            delete_recipe(recipe_id)
            else:
                st.error("Recipe not found.")
        else:
            # GALLERY VIEW
            col_head, col_filter, col_ref = st.columns([3, 2, 1])
            with col_head: st.markdown("### My Collection")
            with col_filter: show_favs = st.checkbox("❤️ Favorites Only")
            with col_ref:
                if st.button("🔄 Refresh"): st.rerun()

            base_query = "SELECT id, title, local_image_path, rating, times_cooked, is_favorite FROM recipes WHERE user_id = :uid"
            if show_favs: base_query += " AND is_favorite = TRUE"
            base_query += " ORDER BY id DESC"

            df_all = conn.query(base_query, params={"uid": effective_user_id}, ttl=0)

            if not df_all.empty:
                df_all['rating'] = df_all['rating'].fillna(0)
                df_all['times_cooked'] = df_all['times_cooked'].fillna(0)
                COLS = 3
                rows = [df_all.iloc[i:i+COLS] for i in range(0, len(df_all), COLS)]
                for row_chunk in rows:
                    cols = st.columns(COLS)
                    for col, row in zip(cols, row_chunk.itertuples()):
                        with col:
                            with st.container(border=True):
                                if row.local_image_path: st.image(row.local_image_path, use_container_width=True)
                                title_display = f"❤️ {row.title}" if row.is_favorite else row.title
                                st.markdown(f"**{title_display}**")
                                meta_text = f"{'⭐' * int(row.rating)}"
                                if row.times_cooked > 0: meta_text += f" • 🔥 {int(row.times_cooked)}"
                                st.caption(meta_text)
                                if st.button("View", key=f"btn_{row.id}", use_container_width=True):
                                    st.session_state.selected_recipe_id = row.id
                                    st.rerun()
            else:
                st.info("No recipes found for this user.")

    # --- VIEW 3: ANALYTICS ---
    elif st.session_state.active_tab == "📊 Dashboard":
        st.header("📊 Kitchen Analytics")
        df_stats = conn.query("SELECT title, rating, times_cooked, entry_method FROM recipes WHERE user_id = :uid",
                              params={"uid": effective_user_id}, ttl=0)

        if not df_stats.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Recipes", len(df_stats))
            m2.metric("Total Meals Cooked", int(df_stats['times_cooked'].sum() or 0))
            m3.metric("Avg Rating", f"{df_stats['rating'].mean():.1f} ⭐")

            st.markdown("---")
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.subheader("🏆 Most Cooked")
                top_cooked = df_stats[df_stats['times_cooked'] > 0].sort_values(by='times_cooked', ascending=False).head(10)
                if not top_cooked.empty:
                    st.bar_chart(top_cooked, x="title", y="times_cooked", color="#FF4B4B", horizontal=True)
            with col_chart2:
                st.subheader("⭐ Hall of Fame")
                top_rated = df_stats[df_stats['rating'] > 0].sort_values(by='rating', ascending=False).head(10)
                if not top_rated.empty:
                    st.bar_chart(top_rated, x="title", y="rating", color="#FFD700", horizontal=True)
        else:
            st.info("No data available.")

# --- VIEW 4: SETTINGS ---
    elif st.session_state.active_tab == "⚙️ Settings":
        st.header("⚙️ User Preferences")

        # 1. Fetch Data
        current_prefs_df = conn.query("SELECT dietary_preferences FROM users WHERE id = :uid", params={"uid": effective_user_id}, ttl=0)
        current_int_df = conn.query("SELECT api_token, target_list_id FROM user_integrations WHERE user_id = :uid AND provider = 'todoist'", params={"uid": effective_user_id}, ttl=0)

        # Defaults
        default_diet_val = current_prefs_df.iloc[0]['dietary_preferences'] if not current_prefs_df.empty and current_prefs_df.iloc[0]['dietary_preferences'] else ""
        
        # Decrypt Token
        encrypted_token = current_int_df.iloc[0]['api_token'] if not current_int_df.empty else None
        saved_list_id = current_int_df.iloc[0]['target_list_id'] if not current_int_df.empty else None
        
        default_token_val = decrypt_token(encrypted_token) if encrypted_token else ""

        # Helper: Validate Token
        def validate_todoist_token(token):
            try:
                test_api = TodoistAPI(token)
                list(test_api.get_projects()) # Force fetch
                return True
            except Exception:
                return False

        # ------------------------------------------------
        # UNIFIED SETTINGS CARD (No st.form, using Container)
        # ------------------------------------------------
        with st.container(border=True):
            
            # --- SECTION 1: DIETARY ---
            st.subheader("🍽️ Dietary Profile")
            new_prefs = st.text_area("Dietary Restrictions", value=default_diet_val, height=100)
            
            # Save Button for Diet/Key
            if st.button("💾 Save Profile & Connection", type="primary"):
                try:
                    with conn.session as s:
                        # Update Prefs
                        s.execute(text("UPDATE users SET dietary_preferences = :p WHERE id = :uid"), 
                                  params={"p": new_prefs, "uid": effective_user_id})
                        s.commit()
                    st.toast("Profile saved!")
                except Exception as e:
                    st.error(f"Error: {e}")

            st.markdown("---")
            
            # --- SECTION 2: TODOIST CONNECTION ---
            # Adjusted ratio [1, 5] gives the logo way more room than [1, 15]
            col_logo, col_text = st.columns([1, 8], vertical_alignment="center")
            with col_logo:
                if os.path.exists("static/images/todoist-logo.png"):
                    # Use container width to fill the column space naturally
                    st.image("static/images/todoist-logo.png", use_container_width=True)
                else:
                    st.header("✅") 
            with col_text:
                st.subheader("Todoist Connection")

            new_token = st.text_input("Todoist API Token", value=default_token_val, type="password", help="Found in Todoist Settings > Integrations")

            # Logic to Save the Token
            if st.button("Verify & Save Token"):
                if new_token.strip() and not validate_todoist_token(new_token):
                    st.error("❌ Invalid API Token. Please check your key.")
                else:
                    try:
                        with conn.session as s:
                            final_token_to_save = None
                            if new_token.strip():
                                final_token_to_save = encrypt_token(new_token)
                                upsert_query = text("""
                                    INSERT INTO user_integrations (user_id, provider, api_token)
                                    VALUES (:uid, 'todoist', :token)
                                    ON CONFLICT (user_id, provider) DO UPDATE SET api_token = EXCLUDED.api_token;
                                """)
                                s.execute(upsert_query, params={"uid": effective_user_id, "token": final_token_to_save})
                            elif encrypted_token and not new_token.strip():
                                s.execute(text("DELETE FROM user_integrations WHERE user_id = :uid"), params={"uid": effective_user_id})
                            s.commit()
                        
                        st.success("Token verified & saved!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not save settings: {e}")

            # --- SECTION 3: LIST SELECTION (Inside the same box!) ---
            if default_token_val:
                st.markdown("---")
                st.subheader("🛒 Shopping List Selection")
                
                try:
                    api = TodoistAPI(default_token_val)
                    raw_data = api.get_projects()
                    
                    # Flatten Data Logic
                    if not isinstance(raw_data, list): raw_data = list(raw_data)
                    if len(raw_data) > 0 and isinstance(raw_data[0], list): raw_data = raw_data[0]

                    project_options = {}
                    for p in raw_data:
                        p_name = getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else None)
                        p_id = getattr(p, "id", None) or (p.get("id") if isinstance(p, dict) else None)
                        if p_name and p_id:
                            project_options[p_name] = p_id

                    project_options["➕ Create New 'Groceries' List"] = "create_new"

                    # Find Index
                    current_index = 0
                    if saved_list_id and saved_list_id in project_options.values():
                        found = [k for k, v in project_options.items() if v == saved_list_id]
                        if found: current_index = list(project_options.keys()).index(found[0])

                    col_sel, col_btn = st.columns([3, 1], vertical_alignment="bottom")
                    with col_sel:
                        selected_option = st.selectbox("Sync Ingredients To:", options=list(project_options.keys()), index=current_index)
                    
                    with col_btn:
                        if st.button("Update List"):
                            target_id = project_options[selected_option]
                            if target_id == "create_new":
                                try:
                                    new_proj = api.add_project(name="Groceries")
                                    target_id = new_proj.id
                                    st.toast("Created new list: Groceries")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                                    st.stop()
                            try:
                                with conn.session as s:
                                    s.execute(text("UPDATE user_integrations SET target_list_id = :lid WHERE user_id = :uid AND provider = 'todoist'"), 
                                              params={"lid": target_id, "uid": effective_user_id})
                                    s.commit()
                                st.success("Saved!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                st.error(f"DB Error: {e}")

                except Exception as e:
                    st.warning(f"Could not load lists. Error: {e}")

# ==========================================
#  APP ENTRY POINT
# ==========================================
if not st.session_state.user:
    login_screen()
else:
    main_app()
