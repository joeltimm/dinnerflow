import streamlit as st
from sqlalchemy import text
from datetime import date

def render_tonight(conn, user_id):
    st.header("🔥 Tonight")
    st.caption("One call. No overthinking. Iron Skillet handles the rest.")

    df = conn.query(
        """
        SELECT *
        FROM recipes
        WHERE user_id = :uid
        ORDER BY
          last_cooked NULLS FIRST,
          times_cooked ASC,
          RANDOM()
        LIMIT 1
        """,
        params={"uid": user_id},
        ttl=0
    )

    if df.empty:
        st.info("The vault is empty. Feed it recipes and we’ll cook.")
        return

    recipe = df.iloc[0]

    st.subheader(recipe["title"])

    if recipe["local_image_path"]:
        st.image(recipe["local_image_path"], use_container_width=True)

    # INGREDIENTS
    st.markdown("### 🥕 Ingredients")
    ingredients = recipe["ingredients"] or []
    for i in ingredients:
        if isinstance(i, dict):
            st.write(f"- {i.get('quantity','')} {i.get('name','')}".strip())
        else:
            st.write(f"- {i}")

    # INSTRUCTIONS
    st.markdown("### 👨‍🍳 How This Goes Down")
    instructions = recipe["instructions"] or []
    for idx, step in enumerate(instructions, start=1):
        st.markdown(f"**{idx}.** {step}")

    st.divider()

    st.markdown("### After Action Report")

    rating = st.slider(
        "How’d it hit?",
        1, 5, 4,
        format="%d ⭐"
    )

    notes = st.text_area(
        "Notes for future you (optional)",
        placeholder="Too salty? Banger? Changed a step?"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔥 Cooked. Log it.", use_container_width=True):
            with conn.session as s:
                # update recipe stats
                s.execute(
                    text("""
                    UPDATE recipes
                    SET
                      last_cooked = NOW(),
                      times_cooked = COALESCE(times_cooked, 0) + 1,
                      rating = :rating
                    WHERE id = :rid
                    """),
                    {"rid": recipe["id"], "rating": rating}
                )

                # insert cooking log
                s.execute(
                    text("""
                    INSERT INTO cooking_log
                      (recipe_id, date_cooked, rating, notes)
                    VALUES
                      (:rid, :date, :rating, :notes)
                    """),
                    {
                        "rid": recipe["id"],
                        "date": date.today(),
                        "rating": rating,
                        "notes": notes
                    }
                )

                s.commit()

            st.toast("Logged. Skillet stays hot.")
            st.rerun()

    with col2:
        if st.button("🎲 Not tonight", use_container_width=True):
            st.rerun()
