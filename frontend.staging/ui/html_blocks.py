#frontend.staging/ui/html_blocks.py
import streamlit as st
from streamlit.components.v1 import html

def landing_hero():
    st.markdown("""
    <section class="hero">
        <h1>
            Iron Skillet
            Dinner. Decided.
        </h1>

        <p>
            Once a week, you get a short list of dinners.
            You pick one. The ingredients go to Todoist.
            We handle the remembering.
        </p>

        <ul>
            <li>Stop planning. Start cooking.</li>
            <li>Iron Skillet sends you dinner ideas you’ll actually make.</li>
            <li>Not aspirational. Not overwhelming. Just solid meals.</li>
            <li>🧌 Powered by a mildly aggressive cooking ogre.</li>
        </ul>
    </section>
    """, height=520, unsafe_allow_html=True)

def recipe_hero(recipe):
    st.markdown(f"""
    <section class="hero">
        <h1>{recipe['title']}</h1>

        <p>
            Built from your habits
            It remembers what you cook, what you love, and what you never want again.
        </p>
    </section>
    """, height=260, unsafe_allow_html=True)


def recipe_ingredients(recipe):
    items = "".join(
        f"<li>{i}</li>" for i in recipe["ingredients"]
    )

    st.markdown(f"""
    <section style="max-width: 720px; margin: 2rem auto;">
        <h3>Ingredients</h3>
        <ul style="line-height: 1.7;">
            {items}
        </ul>
    </section>
    """, height=400, unsafe_allow_html=True)
