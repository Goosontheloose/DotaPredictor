import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items
import datetime

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Aegis Oracle | TI 2026", layout="wide", page_icon="🏆")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #ffffff; }
    .stButton>button { 
        width: 100%; 
        background-color: #e32929; 
        color: white; 
        border-radius: 8px; 
        height: 3.5em; 
        font-weight: bold; 
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #ff4b4b; border: 1px solid white; }
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; border-radius: 5px; }
    h1, h2, h3 { color: #f0ad4e; text-align: center; font-family: 'serif'; }
    .prediction-box { padding: 20px; border-radius: 10px; background-color: #161b22; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# --- 2. DATA ---
TEAMS = [
    "Team Spirit", "Gaimin Gladiators", "Team Liquid", "Xtreme Gaming",
    "Falcons", "Tundra Esports", "BetBoom Team", "Cloud9",
    "Entity", "Aurora", "HEROIC", "beastcoast",
    "PSG.Quest", "G2.iG", "Nouns", "1win", "Team Zero"
]

# --- 3. SESSION STATE ---
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# --- 4. MAIN INTERFACE ---
st.title("🏆 AEGIS ORACLE: TI 2026")
st.markdown("### The International Prediction Arena")

if not st.session_state.submitted:
    # Sidebar or Header for Input
    with st.container():
        player_name = st.text_input("ENTER ORACLE NAME", placeholder="Type your name to claim your prophecy...")
    
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.info("💡 **Instructions:** Drag and drop teams to rank them from 1st (Top) to 17th (Bottom). Your score will be calculated based on this exact order.")
        
        # Drag and Drop List
        user_ranking = sort_items(TEAMS, direction='vertical')
        
        st.write("") # Spacing
        
        if st.button("LOCK IN PREDICTIONS"):
            if not player_name:
                st.error("⚠️ The Oracle requires a name to record your fate.")
            else:
                with st.spinner("Writing your destiny to the Aegis Ledger..."):
                    try:
                        # Establish Connection
                        conn = st.connection("gsheets", type=GSheetsConnection)
                        
                        # Fetch existing data to append correctly
                        # Ensure 'ttl=0' to bypass caching and get the absolute latest sheet state
                        existing_data = conn.read(worksheet="Submissions", ttl=0)
                        
                        # Create new record
                        new_record = pd.DataFrame([{
                            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Oracle Name": player_name,
                            "Rankings": ", ".join(user_ranking)
                        }])
                        
                        # Combine and Push
                        updated_df = pd.concat([existing_data, new_record], ignore_index=True)
                        conn.update(worksheet="Submissions", data=updated_df)
                        
                        # Mark as Success
                        st.session_state.submitted = True
                        st.rerun()
                        
                    except Exception as e:
                        st.error("🔮 **Prophecy Interrupted!**")
                        # Detailed error reporting for debugging
                        st.exception(e) 
                        st.info("Check: 1. Is 'Submissions' tab name correct? 2. Is Service Account an Editor? 3. Is Google Drive API enabled?")

else:
    # Success State
    st.container()
    st.success("✅ **YOUR PROPHECY HAS BEEN RECORDED!**")
    st.balloons()
    
    st.markdown("""
        <div style="text-align: center; padding: 50px;">
            <h2>The Aegis awaits.</h2>
            <p>Your rankings are secured in the ledger. Check the leaderboard after the Grand Finals.</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("SUBMIT ANOTHER PREDICTION"):
        st.session_state.submitted = False
        st.rerun()

# --- 5. FOOTER ---
st.divider()
st.caption("Aegis Oracle v1.0 | Data stored securely via Google Cloud")
