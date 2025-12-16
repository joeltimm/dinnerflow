import streamlit as st
import auth as auth_backend

def render_auth():
    st.markdown("## For home cooks who are done negotiating with themselves.")
    st.caption("No spam. No ads. No recipe essays.")

    tab_login, tab_signup = st.tabs(["Welcome back.", "Set up your skillet."])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            if st.form_submit_button("Continue", type="primary"):
                user = auth_backend.authenticate_user(email, password)
                if user:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("That didn’t work. Try again.")

    with tab_signup:
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm password", type="password")

            if st.form_submit_button("Create account"):
                if password != confirm:
                    st.error("Passwords don’t match.")
                elif auth_backend.register_user(email, password, None):
                    st.success("Account created. Log in and let’s cook.")
                else:
                    st.error("That email is already in the dungeon.")
