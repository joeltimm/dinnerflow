# frontend.staging/app.py
import streamlit as st

# --- 1. Imports ---
from ui.css import inject_global_css
from ui.landing import render_landing
from ui.auth import render_auth
from ui.sidebar import render_sidebar
from ui.pages.tonight import render_tonight
from ui.pages.preferences import render_preferences
from ui.pages.recipes import render_recipes_page
# Note: You need a function to LIST recipes, not just render one.
# Assuming you will fix recipes.py to include a list view:
# from ui.pages.recipes import render_recipe_list 

st.set_page_config(
    page_title="Iron Skillet", # Rebranded
    page_icon="static/images/cooking-ogre-favicon.png",
    layout="wide",
)

inject_global_css()

# --- 2. Initialize Session State ---
if "user" not in st.session_state:
    st.session_state.user = None
if "show_auth" not in st.session_state:
    st.session_state.show_auth = False

# --- 3. Database Connection (CRITICAL MISSING PIECE) ---
# You used 'conn' in your code but didn't define it. 
# This assumes you are using st.connection or similar.
# If using raw psycopg2 from auth.py, you need to adapt this.
try:
    conn = st.connection("dinner_db", type="sql")
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# --- 4. Logic Flow ---

# A. Email Magic Link Handler
if "from_email" in st.query_params:
    # You need to handle user identification here securely
    # For now, this would crash because user_id isn't defined
    st.warning("Magic link logic pending...")
    st.stop()

# B. Logged Out State
if not st.session_state.user:
    if st.session_state.show_auth:
        render_auth()
        if st.button("← Back to home"):
            st.session_state.show_auth = False
            st.rerun()
    else:
        render_landing()

# C. Logged In State
else:
    render_sidebar(st.session_state.user)
    
    # DEFINE THE MISSING VARIABLE
    effective_user_id = st.session_state.user["id"]

    # Navigation
    if st.session_state.active_tab == "Tonight":
        render_tonight(conn, effective_user_id)

    elif st.session_state.active_tab == "Recipes":
        render_recipes_page(conn, effective_user_id)

    elif st.session_state.active_tab == "⚙️ Preferences":
        # You need to define these crypto functions or import them
        def encrypt_stub(t): return t 
        def decrypt_stub(t): return t
        
        render_preferences(
            conn,
            effective_user_id,
            encrypt_stub, # Placeholder
            decrypt_stub  # Placeholder
        )