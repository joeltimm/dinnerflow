import streamlit as st
from ui.html_blocks import recipe_hero, recipe_ingredients

def render_recipes_page(conn, user_id):
    """
    Main controller for the Recipes tab.
    Decides whether to show the full list (Vault) or a single recipe.
    """
    # Initialize selection state if missing
    if "selected_recipe_id" not in st.session_state:
        st.session_state.selected_recipe_id = None

    # LOGIC: If a recipe is selected, show details. Otherwise, show the vault.
    if st.session_state.selected_recipe_id:
        # Fetch the specific recipe details
        df = conn.query(
            "SELECT * FROM recipes WHERE id = :rid AND user_id = :uid",
            params={"rid": st.session_state.selected_recipe_id, "uid": user_id},
            ttl=0
        )
        
        if not df.empty:
            render_recipe_detail(df.iloc[0])
        else:
            st.error("Recipe not found.")
            if st.button("Back to Vault"):
                st.session_state.selected_recipe_id = None
                st.rerun()
    else:
        render_recipe_list(conn, user_id)


def render_recipe_list(conn, user_id):
    """
    The Vault View: Displays a grid of all recipes for the user.
    """
    st.header("📚 The Vault")
    st.caption("Everything you've taught the ogre to cook.")

    # Query fields based on your schema
    df = conn.query(
        """
        SELECT id, title, local_image_path, rating, times_cooked, last_cooked 
        FROM recipes 
        WHERE user_id = :uid 
        ORDER BY title ASC
        """,
        params={"uid": user_id},
        ttl=0
    )

    if df.empty:
        st.info("The vault is empty. Add a recipe to get started.")
        return

    # --- GRID LAYOUT ---
    # We'll do a responsive grid (3 columns wide)
    cols = st.columns(3)
    
    for idx, row in df.iterrows():
        # Cycle through columns: 0, 1, 2, 0, 1, 2...
        with cols[idx % 3]:
            with st.container(border=True):
                # Image handling
                if row["local_image_path"]:
                    st.image(row["local_image_path"], use_container_width=True)
                else:
                    # Fallback placeholder if no image exists
                    st.markdown("🥘 *No Image*")

                st.subheader(row["title"])
                
                # Stats row
                c1, c2 = st.columns(2)
                c1.metric("Rating", f"{row['rating'] or '-'} / 5")
                c2.metric("Cooked", f"{row['times_cooked']}x")

                # The "View" button
                if st.button("Open", key=f"btn_{row['id']}", use_container_width=True):
                    st.session_state.selected_recipe_id = row["id"]
                    st.rerun()


def render_recipe_detail(recipe):
    """
    The Detail View: Shows one specific recipe (formerly render_recipe).
    """
    # --- NAVIGATION ---
    if st.button("← Back to Vault"):
        st.session_state.selected_recipe_id = None
        st.rerun()

    # ---- HERO ----
    recipe_hero(recipe)

    # ---- ACTIONS ----
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button("🍳 Cook this tonight", type="primary", use_container_width=True):
            # You might want to link this to the "Tonight" view logic later
            st.toast("Stove is hot! (Logic pending)")

    with col2:
        st.button("⭐ Favorite", use_container_width=True)

    with col3:
        st.button("✏️ Edit", use_container_width=True)

    st.markdown("---")

    # ---- INGREDIENTS ----
    # Ensure ingredients is not None before passing
    if recipe["ingredients"]:
        recipe_ingredients(recipe)
    else:
        st.info("No ingredients listed.")

    # ---- INSTRUCTIONS ----
    st.markdown("### 👨‍🍳 Instructions")
    instructions = recipe["instructions"] or []
    
    if instructions:
        for idx, step in enumerate(instructions, start=1):
            st.markdown(f"**{idx}.** {step}")
    else:
        st.caption("No instructions found. You're on your own, chef.")

    st.markdown("---")