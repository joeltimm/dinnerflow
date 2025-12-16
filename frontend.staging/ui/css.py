import streamlit as st

def inject_global_css():
    st.markdown("""
    <style>
    :root {
        --fg: #0f172a;
        --muted: #475569;
        --accent: #16a34a;
    }

    body {
        font-family: Inter, system-ui, sans-serif;
    }

    .hero {
        max-width: 960px;
        margin: 6rem auto 4rem;
    }

    .hero h1 {
        font-size: 3.75rem;
        line-height: 1.05;
        letter-spacing: -0.03em;
        margin-bottom: 1rem;
    }

    .hero p {
        font-size: 1.25rem;
        color: var(--muted);
        max-width: 44rem;
    }

    .hero ul {
        margin-top: 2rem;
        font-size: 1.05rem;
        color: var(--fg);
    }

    .hero li {
        margin-bottom: 0.75rem;
    }

    .divider {
        margin: 4rem 0;
        opacity: 0.15;
    }
    </style>
    """, unsafe_allow_html=True)
