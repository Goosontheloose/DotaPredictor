import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# --- CONFIGURATION (MATCHING YOUR GITHUB SCREENSHOT) ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"

# Exact names from your GitHub file list to ensure logos link correctly
TEAMS = [
    "Team Falcons", "LGD Gaming", "Iron Wing", "Nigma Galaxy",
    "BoomBoys", "OG", "TEAM VISION", "Team Resilience",
    "Team Spirit", "Xtreme Gaming", "Team Liquid", "Vigi Gaming",
    "Aurora Gaming", "GamerLegion", "Team Yandex", "huligani"
]

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide")

# --- UI STYLING ---
st.markdown(f"""
    <style>
    .header-container {{ display: flex; align-items: center; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; margin-bottom: 25px; }}
    .team-row {{ display: flex; align-items: center; gap: 12px; padding: 10px; background: #f9f9f9; border-radius: 6px; margin-bottom: 5px; border: 1px solid #eee; }}
    .rank-badge {{ background: #222; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; min-width: 35px; text-align: center; }}
    </style>
""", unsafe_allow_html=True)

def get_logo_url(file_name):
    # Pulls from root directory as per your screenshot
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{file_name.replace(' ', '%20')}.png"

# --- DATA ENGINE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_all_data():
    try:
        res = conn.read(worksheet="Results")
        sub = conn.read(worksheet="Submissions")
        return res.dropna(how='all'), sub.dropna(how='all')
    except:
        return pd.DataFrame(), pd.DataFrame()

results_df, subs_df = load_all_data()

# --- HEADER (Matches 'Aegis.png' in your screenshot) ---
st.markdown(f"""
    <div class="header-container">
        <img src="{get_logo_url('Aegis')}" width="50" height="50" onerror="this.src='https://img.icons8.com/ios-filled/50/000000/shield.png'">
        <h1 style="margin:0;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔮 LOCK-IN", "📊 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

# --- TAB 1: LOCK-IN ---
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Your Prophecy")
        name = st.text_input("Oracle Name")
        if 'picks' not in st.session_state: st.session_state.picks = []
        
        rem = sorted([t for t in TEAMS if t not in st.session_state.picks])
        pick = st.selectbox(f"Rank #{len(st.session_state.picks)+1}", ["Select..."] + rem)
        
        if pick != "Select...":
            st.session_state.picks.append(pick)
            st.rerun()
            
        if st.button("Reset"):
            st.session_state.picks = []; st.rerun()

    with c2:
        st.subheader("Preview")
        for i, team in enumerate(st.session_state.picks):
            st.markdown(f'<div class="team-row"><div class="rank-badge">#{i+1}</div><img src="{get_logo_url(team)}" width="25"> {team}</div>', unsafe_allow_html=True)

    if len(st.session_state.picks) == 16 and name:
        if st.button("LOCK IN", use_container_width=True):
            new_row = pd.DataFrame([{"Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "Oracle Name": name, "Rankings": ",".join(st.session_state.picks)}])
            conn.update(worksheet="Submissions", data=pd.concat([subs_df, new_row]))
            st.success("Prophecy Locked!"); st.balloons()

# --- TAB 2: LEADERBOARD ---
with tabs[1]:
    if results_df.empty or "Rank" not in results_df.columns:
        st.info("Waiting for official tournament results to calculate scores.")
    elif subs_df.empty:
        st.warning("No prophecies have been locked in yet.")
    else:
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        leaderboard = []

        for _, row in subs_df.iterrows():
            oracle = row['Oracle Name']
            preds = row['Rankings'].split(',')
            score = 0
            perfect = 0
            
            for i, team in enumerate(preds):
                p_rank = i + 1
                a_rank = actual_ranks.get(team, 0)
                if a_rank > 0:
                    mult = 4 if p_rank == 1 else 3 if p_rank == 2 else 2 if p_rank in [3,4] else 1
                    dist = abs(p_rank - a_rank)
                    score += (dist * mult)
                    if dist == 0: perfect += 1
            
            leaderboard.append({"Oracle": oracle, "Score": score, "Perfect Picks": perfect})
        
        lb_display = pd.DataFrame(leaderboard).sort_values(by=["Score", "Perfect Picks"], ascending=[True, False])
        st.table(lb_display)

# --- TAB 3: MATRIX ---
with tabs[2]:
    st.dataframe(subs_df, use_container_width=True)

# --- TAB 4: PROTOCOL ---
with tabs[3]:
    st.markdown("""
    ### Scoring Protocol
    - **Lowest Score Wins** (Golf Rules)
    - **1st Place Pick:** 4x Penalty Multiplier
    - **2nd Place Pick:** 3x Penalty Multiplier
    - **3rd-4th Place Picks:** 2x Penalty Multiplier
    - **All others:** 1x Penalty Multiplier
    """)
