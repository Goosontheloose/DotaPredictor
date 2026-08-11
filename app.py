import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Aegis Oracle | Dota 2 TI 2026", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #e32929; color: white; border-radius: 5px; height: 3em; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    h1, h2, h3 { color: #f0ad4e; text-align: center; font-family: 'serif'; }
    </style>
""", unsafe_allow_html=True)

TEAMS = [
    "Team Spirit", "Gaimin Gladiators", "Team Liquid", "Xtreme Gaming",
    "Falcons", "Tundra Esports", "BetBoom Team", "Cloud9",
    "Entity", "Aurora", "HEROIC", "beastcoast",
    "PSG.Quest", "G2.iG", "Nouns", "1win", "Team Zero"
]

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

st.title("🏆 AEGIS ORACLE: TI 2026")

if not st.session_state.submitted:
    player_name = st.text_input("Enter your Oracle Name", placeholder="e.g. Kunkka_Fan_99")
    
    # Simple list for ranking if sort_items isn't working perfectly
    st.info("💡 Predict the final standings (Top to Bottom)")
    from streamlit_sortables import sort_items
    user_ranking = sort_items(TEAMS, direction='vertical')
    
    if st.button("LOCK IN PREDICTIONS"):
        if not player_name:
            st.error("The Oracle requires a name.")
        else:
            with st.spinner("Writing to the Aegis Ledger..."):
                try:
                    # 1. Establish connection
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    # 2. Fetch the spreadsheet URL from your secrets to be explicit
                    # This ensures we are targeting the right file
                    spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                    
                    # 3. Create the data row
                    new_data = pd.DataFrame([{
                        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Oracle Name": player_name,
                        "Rankings": ", ".join(user_ranking)
                    }])

                    # 4. Use the .update() method with the spreadsheet URL explicitly
                    # We read the data first to ensure we append
                    df_existing = conn.read(worksheet="Submissions", ttl=0)
                    df_final = pd.concat([df_existing, new_data], ignore_index=True)
                    
                    # Note: using the worksheet name explicitly here
                    conn.update(worksheet="Submissions", data=df_final)
                    
                    st.session_state.submitted = True
                    st.rerun()
                except Exception as e:
                    # IMPROVED ERROR LOGGING: This will show the actual traceback
                    st.error(f"Prophecy Interrupted!")
                    st.exception(e) 

else:
    st.success("Prophecy recorded!")
    st.balloons()
    if st.button("Submit another prediction"):
        st.session_state.submitted = False
        st.rerun()
