import streamlit as st
from ui.html_blocks import landing_hero

def render_landing():
    landing_hero()

    st.markdown('<hr class="divider"/>', unsafe_allow_html=True)

    st.markdown("### Ready to stop thinking about dinner?")
    st.caption("This takes about 30 seconds. We timed it.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Feed me", type="primary", use_container_width=True):
            st.session_state.show_auth = True

    with col2:
        if st.button("I already have an account", use_container_width=True):
            st.session_state.show_auth = True
