import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 0. HARD-CODED ROSTER (THE SOURCE OF SPEED) ---
TEAMS_2026 = [
    "G2 x iG", "Team Falcons", "Xtreme Gaming", "Team Liquid", 
    "Tundra Gaming", "Cloud9", "Aurora", "BetBoom Team", 
    "Team Spirit", "HEROIC", "beastcoast", "Gaimin Gladiators", 
    "Talon Esports", "1win", "Nouns", "Team Zero"
]

# --- UI CONFIG ---
st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide", page_icon="🏮")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&family=JetBrains+Mono:wght@700&display=swap');
    .main { background-color: #0b0e14; }
    .rank-box { 
        background: #1a1c23; border-left: 5px solid #00f2ff; 
        padding: 12px 20px; margin: 8px 0; 
        color: #ffffff !important; font-family: 'Inter', sans-serif;
        font-size: 1.1rem; font-weight: 700; border-radius: 0 8px 8px 0;
    }
    .rank-num { color: #00f2ff; font-weight: 900; margin-right: 20px; font-family: 'JetBrains Mono', monospace; }
    h1, h2, h3 { color: #00f2ff !important; text-transform: uppercase; letter-spacing: 1px; }
    .stMetric { background: rgba(0, 242, 255, 0.05); border: 1px solid #00f2ff; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. DATA ENGINE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300) 
def load_sheet_data():
    try:
        res = conn.read(worksheet="Results")
        sub = conn.read(worksheet="Submissions")
        return res, sub, None
    except Exception as e:
        return None, None, str(e)

# --- 2. THE SCORING LOGIC (RESTORED) ---
def calculate_score(predictions, actual_df):
    actual_map = dict(zip(actual_df['Team'], actual_df['Rank']))
    total_penalty = 0
    for i, team in enumerate(predictions):
        pred_rank = i + 1
        real_rank = actual_map.get(team, 0)
        
        # Skip teams that haven't been placed yet in the 'Results' tab
        if not real_rank or pd.isna(real_rank) or real_rank == 0:
            continue
            
        # Multiplier Logic
        mult = 1
        if pred_rank == 1: mult = 4
        elif pred_rank == 2: mult = 3
        elif pred_rank in [3, 4]: mult = 2
        
        total_penalty += abs(pred_rank - real_rank) * mult
    return total_penalty

# --- 3. MAIN DASHBOARD ---
st.title("🏮 AEGIS ORACLE: 2026")

tabs = st.tabs(["🎯 SUBMIT", "🏆 LEADERBOARD", "📋 MATRIX", "🛠 ARBITER"])

# Load data once for all tabs
results_df, subs_df, error = load_sheet_data()

# --- TAB 1: SUBMIT ---
with tabs[0]:
    col_in, col_pre = st.columns([1, 1], gap="large")
    with col_in:
        st.subheader("I. Identity")
        oracle_name = st.text_input("Oracle Name", placeholder="e.g. Ruben")
        picks = st.multiselect("II. Rank Teams (1st → 16th)", options=TEAMS_2026)
        
        st.divider()
        ready = len(picks) == 16 and oracle_name
        if st.button("🔥 LOCK IN PROPHECY", disabled=not ready, use_container_width=True):
            with st.spinner("Writing to Sheets..."):
                new_row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(picks)
                }])
                # We update by appending to the existing dataframe
                updated_subs = pd.concat([subs_df, new_row], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_subs)
                st.cache_data.clear()
                st.success("Prophecy Recorded!")
                st.balloons()
                st.rerun()

    with col_pre:
        st.subheader("Live Prophecy Receipt")
        if picks:
            for i, team in enumerate(picks):
                st.markdown(f'<div class="rank-box"><span class="rank-num">#{i+1:02d}</span> {team}</div>', unsafe_allow_html=True)
        else:
            st.info("Your rankings will appear here as you select teams.")

# --- TAB 2: LEADERBOARD ---
with tabs[1]:
    st.subheader("The Great Standings")
    if error:
        st.error(f"Sync Error: {error}")
    elif not subs_df.empty:
        lb_list = []
        for _, row in subs_df.iterrows():
            p_list = str(row['Rankings']).split(",")
            pts = calculate_score(p_list, results_df)
            lb_list.append({"Oracle": row['Oracle Name'], "Penalty Points": pts, "Date": row['Timestamp']})
        
        lb_final = pd.DataFrame(lb_list).sort_values("Penalty Points")
        
        # Top 3 Metrics
        m_cols = st.columns(min(len(lb_final), 3))
        for i, (idx, r) in enumerate(lb_final.head(3).iterrows()):
            m_cols[i].metric(f"Rank #{i+1}", r['Oracle'], f"{r['Penalty Points']} PTS")
            
        st.table(lb_final)
    else:
        st.info("No predictions found in the vault.")

# --- TAB 3: MATRIX ---
with tabs[2]:
    st.subheader("The Oracle Comparison Matrix")
    if not subs_df.empty:
        matrix_data = {"Rank": [f"#{i+1:02d}" for i in range(16)]}
        for _, row in subs_df.iterrows():
            matrix_data[row['Oracle Name']] = str(row['Rankings']).split(",")
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)

# --- TAB 4: ARBITER ---
with tabs[3]:
    st.subheader("Current Tournament Standings")
    st.write("The Oracle scores are calculated based on these ranks:")
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    st.caption("Admin: Update the 'Rank' column in your Google Sheet to refresh scores.")
