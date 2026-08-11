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
    .rank-box { padding: 10px; border-radius: 10px; background: #161b22; border: 1px solid #30363d; margin-bottom: 10px; }
    h3 { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
    .team-logo { vertical-align: middle; margin-right: 10px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- TEAM LOGO MAPPING ---
LOGOS = {
    "Team Liquid": "https://liquipedia.net/commons/images/d/d3/Team_Liquid_2023_allmode.png",
    "Gaimin Gladiators": "https://liquipedia.net/commons/images/d/df/Gaimin_Gladiators_2022_lightmode.png",
    "Tundra Esports": "https://liquipedia.net/commons/images/0/0e/Tundra_Esports_2023_allmode.png",
    "Team Falcons": "https://liquipedia.net/commons/images/1/1d/Team_Falcons_allmode.png",
    "Xtreme Gaming": "https://liquipedia.net/commons/images/0/0d/Xtreme_Gaming_2021_allmode.png",
    "Cloud9": "https://liquipedia.net/commons/images/2/23/Cloud9_2023_allmode.png",
    "BetBoom Team": "https://liquipedia.net/commons/images/0/00/BetBoom_Team_2022_allmode.png",
    "Aurora": "https://liquipedia.net/commons/images/6/60/Aurora_Gaming_2023_allmode.png",
    "Nouns": "https://liquipedia.net/commons/images/1/1a/Nouns_Esports_2022_allmode.png",
    "Team Spirit": "https://liquipedia.net/commons/images/8/8e/Team_Spirit_2021_allmode.png",
    "HEROIC": "https://liquipedia.net/commons/images/e/ef/Heroic_2019_allmode.png",
    "PSG Quest": "https://liquipedia.net/commons/images/e/e9/PSG_Quest_2023_allmode.png",
    "Team Zero": "https://liquipedia.net/commons/images/c/c8/Team_Zero_2023_allmode.png",
    "1win": "https://liquipedia.net/commons/images/d/d4/1win_2024_allmode.png",
    "MOUZ": "https://liquipedia.net/commons/images/8/82/MOUZ_2021_allmode.png",
    "Talon Esports": "https://liquipedia.net/commons/images/0/08/Talon_Esports_2022_allmode.png"
}

TEAMS = list(LOGOS.keys())

# --- DATA ENGINE ---
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
        st.cache_data.clear() 
        return True
    except Exception as e:
        st.error(f"Submission Error: {e}")
        return False

# --- DUAL SCORING LOGIC ---
def calculate_dual_scores(pred_list, actual_df):
    if actual_df is None or actual_df.empty or 'Team' not in actual_df.columns:
        return 0, 0
    
    fixed_score = 0
    projected_score = 0
    actual_map = dict(zip(actual_df['Team'], actual_df['Rank']))
    status_map = dict(zip(actual_df['Team'], actual_df.get('Status', ['Eliminated']*len(actual_df))))
    
    for i, team in enumerate(pred_list):
        pred_rank = i + 1
        official_rank = actual_map.get(team, 0)
        status = status_map.get(team, "Eliminated")
        
        if official_rank == 0: continue 
        
        diff = abs(pred_rank - official_rank)
        
        # Apply Multipliers
        multiplier = 1
        if pred_rank == 1: multiplier = 4
        elif pred_rank == 2: multiplier = 3
        elif pred_rank in [3, 4]: multiplier = 2
        
        points = diff * multiplier
        
        # Add to Projected (Always)
        projected_score += points
        
        # Add to Fixed only if team is "Eliminated" or "Final"
        if status in ["Eliminated", "Winner", "Final"]:
            fixed_score += points
            
    return fixed_score, projected_score

# --- UI LAYOUT ---
res_df, subs_df = load_data()

st.title("🏮 AEGIS ORACLE: SHANGHAI 2026")

tab1, tab2, tab3 = st.tabs(["🔮 LOCK IN", "🏆 LEADERBOARD", "📊 MATRIX"])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("The Prophecy")
        oracle_name = st.text_input("Oracle Name", placeholder="Enter your handle...")
        sorted_teams = sort_items(TEAMS, direction='vertical')
        if st.button("LOCK IN PREDICTIONS"):
            if not oracle_name:
                st.error("Identify yourself, Oracle.")
            else:
                if save_submission(oracle_name, sorted_teams):
                    st.success("Prophecy Recorded.")
                    st.balloons()
    with col2:
        st.subheader("Live Preview")
        for i, team in enumerate(sorted_teams):
            logo = LOGOS.get(team, "")
            st.markdown(f"**{i+1}.** <img src='{logo}' width='25' class='team-logo'> {team}", unsafe_allow_html=True)

with tab2:
    st.subheader("🏟️ Official Tournament Standings")
    if res_df is not None and not res_df.empty:
        live_standings = res_df[res_df['Rank'] > 0].sort_values("Rank")
        if not live_standings.empty:
            for _, row in live_standings.iterrows():
                logo = LOGOS.get(row['Team'], "")
                st.markdown(f"**{row['Rank']}** | <img src='{logo}' width='20' class='team-logo'> {row['Team']}", unsafe_allow_html=True)
        else:
            st.info("Tournament hasn't started. No official ranks assigned yet.")

    st.subheader("🏅 Oracle Leaderboard")
    if subs_df is not None and not subs_df.empty:
        leaderboard = []
        for _, row in subs_df.iterrows():
            p_list = row['Rankings'].split(',')
            f_score, p_score = calculate_dual_scores(p_list, res_df)
            leaderboard.append({
                "Oracle": row['Oracle Name'], 
                "Fixed Score": f_score, 
                "Projected Score": p_score,
                "Last Updated": row['Timestamp']
            })
        
        lb_df = pd.DataFrame(leaderboard).sort_values("Projected Score", ascending=True)
        st.table(lb_df)
    else:
        st.warning("No prophecies recorded yet.")

with tab3:
    st.subheader("Prediction Matrix")
    if subs_df is not None and not subs_df.empty:
        matrix_data = {}
        for _, row in subs_df.iterrows():
            matrix_data[row['Oracle Name']] = row['Rankings'].split(',')
        m_df = pd.DataFrame(matrix_data)
        m_df.index = [f"Rank {i+1}" for i in range(16)]
        st.dataframe(m_df, use_container_width=True)
