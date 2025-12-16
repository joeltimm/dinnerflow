import streamlit as st

NAV_OPTIONS = [
    "🍳 Tonight",
    "📚 Recipes",
    "📈 Patterns",
    "⚙️ Preferences"
]

def render_sidebar(user):
    with st.sidebar:
        st.image("static/images/cooking-ogre.png", use_container_width=True)
        st.write(f"👤 **{user['name'] or user['email']}**")

        if st.button("Disappear"):
            st.session_state.user = None
            st.rerun()

        st.markdown("---")

        current = st.session_state.get("active_tab", NAV_OPTIONS[0])
        index = NAV_OPTIONS.index(current) if current in NAV_OPTIONS else 0

        selected = st.radio(
            "Menu",
            NAV_OPTIONS,
            index=index,
            label_visibility="collapsed"
        )

        st.session_state.active_tab = selected
