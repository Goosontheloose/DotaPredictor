import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items

# --- CONFIGURATION & THEME ---
st.set_page_config(page_title="AEGIS ORACLE: 2026", layout="wide", initial_sidebar_state="collapsed")

# REFINED READABILITY CSS
st.markdown("""
    <style>
    /* Use high-quality system fonts */
    html, body, [class*="st-"] {
        font-family: 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', Helvetica, Arial, sans-serif !important;
        background-color: #0d1117;
    }

    .main { background-color: #0d1117; }
    
    /* Force High Contrast White Text */
    p, li, b, i, span, label, .stMarkdown {
        color: #ffffff !important;
        line-height: 1.6 !important;
        font-size: 1.05rem !important;
    }

    /* Clean Blue Headings */
    h1, h2, h3, h4 {
        color: #58a6ff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* Cards with better spacing and borders */
    .protocol-card { 
        background: #161b22 !important; 
        padding: 24px; 
        border-radius: 8px; 
        border: 1px solid #30363d;
        border-left: 4px solid #1f6feb !important; 
        margin-bottom: 20px;
    }

    /* Tags */
    .multiplier-tag { background: #238636; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 800; text-transform: uppercase; }
    .bonus-tag { background: #da3633; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 800; text-transform: uppercase; }

    /* Buttons */
    .stButton>button { 
        background-color: #1f6feb !important; 
        color: #ffffff !important; 
        border: none !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
    }
    
    /* Table Fixes */
    .stTable td, .stTable th {
        color: #ffffff !important;
        background-color: #0d1117 !important;
        border-bottom: 1px solid #30363d !important;
    }
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
    except: return None, None

def save_submission(name, rankings_list):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Submissions", ttl=0)
        new_entry = pd.DataFrame([{"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Oracle Name": name, "Rankings": ",".join(rankings_list)}])
        updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
        conn.update(worksheet="Submissions", data=updated_df)
        st.cache_data.clear() 
        return True
    except: return False

def calculate_dual_scores(pred_list, actual_df):
    if actual_df is None or actual_df.empty or 'Team' not in actual_df.columns: return 0, 0
    f_score, p_score = 0, 0
    actual_map = dict(zip(actual_df['Team'], actual_df['Rank']))
    status_map = dict(zip(actual_df['Team'], actual_df.get('Status', ['Eliminated']*len(actual_df))))
    for i, team in enumerate(pred_list):
        pred_rank = i + 1
        official_rank = actual_map.get(team, 0)
        if official_rank == 0: continue 
        base_penalty = -1 if pred_rank == official_rank else abs(pred_rank - official_rank)
        mult = 4 if pred_rank == 1 else 3 if pred_rank == 2 else 2 if pred_rank in [3, 4] else 1
        points = base_penalty * mult
        p_score += points
        if status_map.get(team) in ["Eliminated", "Winner", "Final"]: f_score += points
    return f_score, p_score

# --- UI ---
res_df, subs_df = load_data()
st.title("🏮 AEGIS ORACLE: SHANGHAI 2026")
t1, t2, t3, t4 = st.tabs(["🔮 LOCK IN", "🏆 LEADERBOARD", "📊 MATRIX", "📖 PROTOCOL"])

with t1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("The Prophecy")
        name = st.text_input("Oracle Name", placeholder="Your handle...")
        sorted_teams = sort_items(TEAMS, direction='vertical')
        if st.button("LOCK IN"):
            if name and save_submission(name, sorted_teams): st.success("Prophecy Locked."); st.balloons()
            else: st.error("Check connection.")
    with col2:
        st.subheader("Live Preview")
        for i, t in enumerate(sorted_teams):
            st.markdown(f"**{i+1}.** <img src='{LOGOS.get(t)}' width='25' style='vertical-align:middle; margin-right:10px;'> {t}", unsafe_allow_html=True)

with t2:
    st.subheader("🏟️ Official Standings")
    if res_df is not None:
        live = res_df[res_df['Rank'] > 0].sort_values("Rank")
        cols = st.columns(4)
        for idx, r in enumerate(live.itertuples()):
            cols[idx % 4].markdown(f"**#{r.Rank}** <img src='{LOGOS.get(r.Team)}' width='20' style='vertical-align:middle;'> {r.Team}", unsafe_allow_html=True)

    st.subheader("🏅 Oracle Leaderboard")
    if subs_df is not None:
        lb = []
        for _, r in subs_df.iterrows():
            f, p = calculate_dual_scores(r['Rankings'].split(','), res_df)
            lb.append({"Oracle": r['Oracle Name'], "Fixed": f, "Projected": p})
        st.table(pd.DataFrame(lb).sort_values("Projected"))

with t3:
    if subs_df is not None:
        m_data = {r['Oracle Name']: r['Rankings'].split(',') for _, r in subs_df.iterrows()}
        st.dataframe(pd.DataFrame(m_data, index=[f"Rank {i+1}" for i in range(16)]), use_container_width=True)

with t4:
    st.header("The Oracle Protocol")
    st.markdown(f"""
    <div class='protocol-card'>
        <h3>🎯 The Bullseye Reward</h3>
        <p>Predicting the <b>exact</b> rank of a team grants a <b>-1 point base penalty</b>.</p>
        <p>Correct #1 pick grants <span class='bonus-tag'>-4 POINTS</span>.</p>
    </div>
    <div class='protocol-card'>
        <h3>⛳ Golf Scoring</h3>
        <p>If you miss, your penalty is the <b>absolute difference</b> between ranks.</p>
        <p>Multipliers: 1st (4x), 2nd (3x), 3rd/4th (2x).</p>
        <p><b>LOWEST SCORE WINS.</b></p>
    </div>
    """, unsafe_allow_html=True)
