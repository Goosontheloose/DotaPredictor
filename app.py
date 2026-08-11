import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIGURATION ---
GITHUB_USER = "Gooseontheloose"  # <--- CHANGE TO YOUR GITHUB USERNAME
REPO_NAME = "DotaPredictor"
BRANCH = "main"

# DEFINITIVE SHANGHAI 16 LIST
TEAMS = [
    "Team Falcons", "LGD Gaming", "Iron Wing", "Nigma Galaxy",
    "BoomBoys", "OG", "TEAM VISION", "Team Resilience",
    "Team Spirit", "Xtreme Gaming", "Team Liquid", "Vici Gaming",
    "Aurora Gaming", "GamerLegion", "Team Yandex", "HULIGANI"
]

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide", initial_sidebar_state="collapsed")

# --- UI STYLING ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; background-color: #ffffff; color: #1a1a1a; }}
    
    .header-container {{
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 20px 0;
        border-bottom: 2px solid #f0f0f0;
        margin-bottom: 30px;
    }}
    .team-row {{
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 12px;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid #e9ecef;
    }}
    .rank-badge {{
        background: #1a1a1a;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
        min-width: 35px;
        text-align: center;
    }}
    .protocol-card {{
        background: #ffffff;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }}
    </style>
""", unsafe_allow_html=True)

def get_logo_url(file_name):
    formatted_name = file_name.replace(" ", "%20")
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/logos/{formatted_name}.png"

# --- DATA ENGINE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data():
    try:
        results = conn.read(worksheet="Results")
        subs = conn.read(worksheet="Submissions")
        return results, subs
    except:
        return pd.DataFrame(), pd.DataFrame()

results_df, subs_df = load_data()

# --- HEADER WITH AEGIS LOGO ---
aegis_url = get_logo_url("aegis")
st.markdown(f"""
    <div class="header-container">
        <img src="{aegis_url}" width="60" height="60" onerror="this.src='https://img.icons8.com/ios-filled/100/000000/shield.png'">
        <h1 style="margin:0; letter-spacing:-1.5px; font-weight:700;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔮 LOCK-IN", "📊 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

# --- TAB 1: LOCK-IN ---
with tabs[0]:
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        st.subheader("Your Prophecy")
        oracle_name = st.text_input("Oracle Name", placeholder="Enter your name...")
        
        if 'selections' not in st.session_state:
            st.session_state.selections = []

        remaining_teams = sorted([t for t in TEAMS if t not in st.session_state.selections])
        
        selected_team = st.selectbox(
            f"Select Team for Rank #{len(st.session_state.selections)+1}", 
            ["Choose Team..."] + remaining_teams,
            key=f"select_{len(st.session_state.selections)}"
        )
        
        if selected_team != "Choose Team...":
            st.session_state.selections.append(selected_team)
            st.rerun()

        if st.button("Reset Predictions"):
            st.session_state.selections = []
            st.rerun()

    with col_preview:
        st.subheader("Live Standings Preview")
        if not st.session_state.selections:
            st.write("Start ranking teams to see the preview...")
        
        for i, team in enumerate(st.session_state.selections):
            logo = get_logo_url(team)
            st.markdown(f"""
                <div class="team-row">
                    <div class="rank-badge">#{i+1}</div>
                    <img src="{logo}" width="28" height="28" onerror="this.src='https://img.icons8.com/ios-filled/50/999999/shield.png'">
                    <span style="font-weight:500;">{team}</span>
                </div>
            """, unsafe_allow_html=True)

    if len(st.session_state.selections) == 16 and oracle_name:
        st.divider()
        if st.button("LOCK IN PROPHECY", use_container_width=True, type="primary"):
            try:
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(st.session_state.selections)
                }])
                updated_subs = pd.concat([subs_df, new_entry], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_subs)
                st.success("Prophecy Recorded. May the Aegis guide you.")
                st.balloons()
            except Exception as e:
                st.error(f"Connection Error: {e}")

# --- TAB 4: PROTOCOL ---
with tabs[3]:
    st.markdown("""
    <div class="protocol-card">
        <h3>Aegis Oracle Scoring Protocol</h3>
        <p>This is a <b>Golf Scoring</b> system: The lower your score, the higher you rank.</p>
        <hr>
        <h4>Point Multipliers</h4>
        <p>Mistakes at the top of the bracket carry heavier penalties:</p>
        <ul>
            <li><b>Rank 1 Prediction:</b> 4x Distance Multiplier</li>
            <li><b>Rank 2 Prediction:</b> 3x Distance Multiplier</li>
            <li><b>Rank 3-4 Predictions:</b> 2x Distance Multiplier</li>
            <li><b>Rank 5-16 Predictions:</b> 1x Distance Multiplier</li>
        </ul>
        <h4>The Formula</h4>
        <p><code>Points = |Predicted Rank - Actual Rank| × Multiplier</code></p>
        <h4>Bracket Tiers</h4>
        <p>Teams tied in the bracket (e.g., 5th-6th) are both assigned the better rank (5) for calculation purposes.</p>
    </div>
    """, unsafe_allow_html=True)
