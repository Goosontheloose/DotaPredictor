import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items

# --- CONFIGURATION & THEME ---
st.set_page_config(page_title="AEGIS ORACLE: 2026", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1f6feb; color: white; border: none; }
    .stButton>button:hover { background-color: #388bfd; border: none; }
    [data-testid="stMetricValue"] { color: #58a6ff; }
    .rank-box { padding: 10px; border-radius: 10px; background: #161b22; border: 1px solid #30363d; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- HARDCODED TEAMS (Optimization) ---
TEAMS = [
    "Team Liquid", "Gaimin Gladiators", "Tundra Esports", "Team Falcons",
    "Xtreme Gaming", "Cloud9", "BetBoom Team", "Aurora", 
    "Nouns", "Team Spirit", "HEROIC", "PSG Quest",
    "Team Zero", "1win", "MOUZ", "Talon Esports"
]

# --- DATA ENGINE (Cached to prevent 429 Errors) ---
@st.cache_data(ttl=600)
def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        results = conn.read(worksheet="Results", ttl=0)
        submissions = conn.read(worksheet="Submissions", ttl=0)
        return results, submissions
    except Exception as e:
        return None, None

def save_submission(name, rankings_list):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Submissions", ttl=0)
        
        new_entry = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Oracle Name": name,
            "Rankings": ",".join(rankings_list)
        }])
        
        updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
        conn.update(worksheet="Submissions", data=updated_df)
        st.cache_data.clear() # Force refresh after new entry
        return True
    except Exception as e:
        st.error(f"Submission Error: {e}")
        return False

# --- SCORING LOGIC ---
def calculate_golf_score(pred_list, actual_df):
    if actual_df is None or actual_df.empty or 'Team' not in actual_df.columns:
        return 0
    
    score = 0
    actual_map = dict(zip(actual_df['Team'], actual_df['Rank']))
    
    for i, team in enumerate(pred_list):
        pred_rank = i + 1
        official_rank = actual_map.get(team, 0)
        
        if official_rank == 0: continue # Team hasn't placed yet
        
        diff = abs(pred_rank - official_rank)
        
        # Weighted Multipliers
        if pred_rank == 1: score += (diff * 4)
        elif pred_rank == 2: score += (diff * 3)
        elif pred_rank in [3, 4]: score += (diff * 2)
        else: score += diff
            
    return score

# --- UI LAYOUT ---
res_df, subs_df = load_data()

st.title("🏮 AEGIS ORACLE: SHANGHAI 2026")

tab1, tab2, tab3 = st.tabs(["🔮 LOCK IN", "🏆 LEADERBOARD", "📊 MATRIX"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("The Prophecy")
        oracle_name = st.text_input("Oracle Name", placeholder="Enter your handle...")
        
        st.info("Drag teams to rank them (1st at the top)")
        sorted_teams = sort_items(TEAMS, direction='vertical')
        
        if st.button("LOCK IN PREDICTIONS"):
            if not oracle_name:
                st.error("Identify yourself, Oracle.")
            else:
                with st.spinner("Writing to the Great Archive..."):
                    if save_submission(oracle_name, sorted_teams):
                        st.success("Prophecy Recorded.")
                        st.balloons()

    with col2:
        st.subheader("Live Preview")
        for i, team in enumerate(sorted_teams):
            st.markdown(f"**{i+1}.** {team}")

with tab2:
    st.subheader("Global Standings")
    if subs_df is not None and not subs_df.empty:
        leaderboard = []
        for _, row in subs_df.iterrows():
            p_list = row['Rankings'].split(',')
            score = calculate_golf_score(p_list, res_df)
            leaderboard.append({"Oracle": row['Oracle Name'], "Score": score, "Submission": row['Timestamp']})
        
        lb_df = pd.DataFrame(leaderboard).sort_values("Score", ascending=True)
        st.table(lb_df)
    else:
        st.warning("No prophecies recorded yet or Database Offline.")

with tab3:
    st.subheader("Prediction Matrix")
    if subs_df is not None and not subs_df.empty:
        matrix_data = {}
        for _, row in subs_df.iterrows():
            matrix_data[row['Oracle Name']] = row['Rankings'].split(',')
        
        m_df = pd.DataFrame(matrix_data)
        m_df.index = [f"Rank {i+1}" for i in range(16)]
        st.dataframe(m_df, use_container_width=True)
    else:
        st.write("Matrix awaiting data.")

# --- DIAGNOSTIC FOOTER ---
with st.expander("System Status"):
    if res_df is None:
        st.error("❌ Connection Failed: Check Sheet Tabs & Permissions")
    else:
        st.success("✅ Database Online")
        st.write(f"Last API Sync: {datetime.now().strftime('%H:%M:%S')}")
