import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

# --- CONFIG & STYLING ---
st.set_page_config(page_title="TI 2026 Aegis Oracle", page_icon="🔮")

# Custom CSS for the "Cyber-Arcane" look
st.markdown("""<style>...</style>""", unsafe_allow_html=True)

# --- INITIAL DATA ---
TI2026_TEAMS = [
    "Team Spirit", "Team Liquid", "Gaimin Gladiators", "Team Falcons",
    "Xtreme Gaming", "BetBoom Team", "Cloud9", "Tundra Esports",
    "Aurora", "Entity", "HEROIC", "G2 x iG", "nouns", "PSG Quest",
    "1win", "Team Zero", "Talon Esports"
]

# --- SESSION STATE ---
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- PAGE 1: SUBMISSION ---
if not st.session_state.submitted:
    st.title("🔮 The Aegis Oracle: TI 2026")
    st.markdown("### Rank the 17 contenders. Submit your Prophecy.")
    
    with st.container():
        col1, col2 = st.columns([2, 1])
        
        with col2:
            st.info("💡 **How to play:** Drag the teams on the left into your predicted finishing order. 1st place goes at the top.")
            player_name = st.text_input("Enter Oracle Name", placeholder="e.g. DendiFan_99")
            
            # Multiplier Warning
            st.warning("""
                **Scoring Rules:**
                - Ranks 1-4 carry Multipliers (4x, 3x, 2x).
                - Lower scores are better (Golf Scoring).
                - You get -1 for hitting the correct tier!
            """)

        with col1:
            # The Drag and Drop Interface
            user_ranking = sort_items(TI2026_TEAMS, direction='vertical')

    # Submit Button
       if st.button("LOCK IN PREDICTIONS"):
        if not player_name:
            st.error("The Oracle requires a name to record your fate.")
        else:
            with st.spinner("Etching your prophecy into the ledger..."):
                try:
                    # 1. Connect
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    # 2. Get existing data to find the next row
                    existing_data = conn.read(worksheet="Submissions", ttl=0) # ttl=0 ensures we don't use old cached data
                    
                    # 3. Create new row
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Oracle Name": player_name,
                        "Rankings": ",".join(user_ranking)
                    }])
                    
                    # 4. Combine and Update
                    updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                    conn.update(worksheet="Submissions", data=updated_df)
                    
                    st.session_state.submitted = True
                    st.rerun()
                except Exception as e:
                    # This will now show you the ACTUAL error instead of hiding it
                    st.error(f"Database Error: {e}")

# --- PAGE 2: SUCCESS / CONFIRMATION ---
else:
    st.balloons()
    st.title("✅ Prophecy Recorded")
    st.success(f"Your rankings have been etched into the Aegis Ledger.")
    
    st.markdown("### Your Top 4:")
    # Display the top 4 teams they picked
    final_picks = getattr(st.session_state, 'local_rank', []) # Pull from local if DB failed
    if final_picks:
        for i, team in enumerate(final_picks[:4]):
            st.write(f"**{i+1}. {team}**")
    
    if st.button("Submit Another Prediction"):
        st.session_state.submitted = False
        st.rerun()
