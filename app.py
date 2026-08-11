import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Aegis Oracle | Dota 2 TI 2026", layout="wide")

# Corrected Markdown parameter
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #e32929; color: white; border-radius: 5px; height: 3em; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    h1, h2, h3 { color: #f0ad4e; text-align: center; font-family: 'serif'; }
    </style>
""", unsafe_allow_html=True)

# --- DATA ---
TEAMS = [
    "Team Spirit", "Gaimin Gladiators", "Team Liquid", "Xtreme Gaming",
    "Falcons", "Tundra Esports", "BetBoom Team", "Cloud9",
    "Entity", "Aurora", "HEROIC", "beastcoast",
    "PSG.Quest", "G2.iG", "Nouns", "1win", "Team Zero"
]

# --- SESSION STATE ---
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- UI ---
st.title("🏆 AEGIS ORACLE: TI 2026")
st.subheader("Rank the teams from 1st to 17th. Prophesy their fate.")

if not st.session_state.submitted:
    player_name = st.text_input("Enter your Oracle Name (Required)", placeholder="e.g. Kunkka_Fan_99")
    
    st.info("💡 Drag and drop the teams into your predicted finishing order.")
    
    # Drag and Drop Interface
    user_ranking = sort_items(TEAMS, direction='vertical')
    
    st.write("---")
    
    if st.button("LOCK IN PREDICTIONS"):
        if not player_name:
            st.error("The Oracle requires a name to record your fate.")
        else:
            with st.spinner("Etching your prophecy into the ledger..."):
                try:
                    # 1. Initialize Connection
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    # 2. Read existing data to maintain the sheet structure
                    # Note: Worksheet must be named "Submissions"
                    existing_data = conn.read(worksheet="Submissions", ttl=0)
                    
                    # 3. Create the new entry
                    new_entry = pd.DataFrame([{
                        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Oracle Name": player_name,
                        "Rankings": ", ".join(user_ranking)
                    }])
                    
                    # 4. Append and Update
                    updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                    conn.update(worksheet="Submissions", data=updated_df)
                    
                    st.session_state.submitted = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Prophecy Interrupted: {e}")
                    st.warning("Ensure your Google Sheet has a tab named 'Submissions' and your Service Account has 'Editor' access.")

else:
    st.success(f"Prophecy recorded, Oracle {st.session_state.player_name if 'player_name' in locals() else ''}!")
    st.balloons()
    st.markdown("### Your fate is sealed. The International awaits.")
    if st.button("Submit another prediction"):
        st.session_state.submitted = False
        st.rerun()
