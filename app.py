import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- UI CONFIG ---
st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide", page_icon="🏮")

# --- SHANGHAI SHADOW-TECH CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@700&family=JetBrains+Mono&display=swap');
    .main { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    h1, h2 { color: #00f2ff !important; text-transform: uppercase; letter-spacing: 2px; }
    .stMetric { background: rgba(0, 242, 255, 0.05); border: 1px solid #00f2ff; padding: 15px; border-radius: 5px; }
    .rank-box { 
        background: rgba(112, 0, 255, 0.1); 
        border-left: 4px solid #7000ff; 
        padding: 8px 15px; 
        margin: 5px 0; 
        font-family: 'JetBrains Mono';
    }
    .rank-num { color: #00f2ff; font-weight: bold; margin-right: 10px; }
    /* Table Styling for the Matrix */
    div[data-testid="stTable"] { background: #161b22; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNECTIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DATA FETCHING ---
try:
    results_df = conn.read(worksheet="Results", ttl=0)
    subs_df = conn.read(worksheet="Submissions", ttl=0)
except Exception as e:
    st.error("⚠️ CONNECTION ERROR: Check 'Results' and 'Submissions' tabs.")
    st.stop()

# --- SCORING LOGIC ---
def calculate_score(predictions, actual_results):
    actual_map = dict(zip(actual_results['Team'], actual_results['Rank']))
    total_pts = 0
    for i, team in enumerate(predictions):
        pred_rank = i + 1
        real_rank = actual_map.get(team, 0)
        if real_rank == 0: continue 
        mult = 4 if pred_rank == 1 else 3 if pred_rank == 2 else 2 if pred_rank in [3, 4] else 1
        total_pts += abs(pred_rank - real_rank) * mult
    return total_pts

# --- SIDEBAR: RANKING INTERFACE ---
with st.sidebar:
    st.title("🏮 SUBMIT")
    oracle_name = st.text_input("ORACLE NAME", placeholder="Enter Name")
    
    team_pool = results_df['Team'].tolist() if not results_df.empty else []
    selected_teams = st.multiselect("RANK TEAMS (1-16)", options=team_pool)

    if selected_teams:
        st.markdown("### 🔮 YOUR RANKINGS")
        for i, team in enumerate(selected_teams):
            st.markdown(f'<div class="rank-box"><span class="rank-num">#{i+1:02d}</span> {team}</div>', unsafe_allow_html=True)
        
        st.caption(f"Progress: {len(selected_teams)}/16")
        
        can_submit = len(selected_teams) == 16 and oracle_name
        if st.button("🔥 LOCK IN PROPHECY", disabled=not can_submit, use_container_width=True):
            new_data = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%m/%d %H:%M"),
                "Oracle Name": oracle_name,
                "Rankings": ",".join(selected_teams)
            }])
            updated_df = pd.concat([subs_df, new_data], ignore_index=True)
            conn.update(worksheet="Submissions", data=updated_df)
            st.success("VAULT UPDATED.")
            st.rerun()

# --- MAIN DASHBOARD ---
st.title("🏮 AEGIS ORACLE: SHANGHAI 2026")

# Reorganized tabs as requested
tab1, tab2, tab3, tab4 = st.tabs(["🏆 LEADERBOARD", "📋 PREDICTION MATRIX", "🔍 INDIVIDUAL VIEW", "🛠 ARBITER VIEW"])

with tab1:
    if not subs_df.empty:
        scores = []
        for _, row in subs_df.iterrows():
            p_list = row['Rankings'].split(",")
            total = calculate_score(p_list, results_df)
            scores.append({"Oracle": row['Oracle Name'], "Penalty Points": total})
        
        score_df = pd.DataFrame(scores).sort_values("Penalty Points")
        cols = st.columns(len(score_df))
        for i, (idx, row) in enumerate(score_df.iterrows()):
            cols[i].metric(row['Oracle'], f"{row['Penalty Points']} PTS")
        st.table(score_df)
    else:
        st.info("Awaiting first prophecy...")

with tab2:
    st.subheader("GLOBAL PREDICTION MATRIX")
    if not subs_df.empty:
        # Transforming data into a column-per-person format
        matrix_data = {"Rank": [f"#{i+1:02d}" for i in range(16)]}
        for _, row in subs_df.iterrows():
            matrix_data[row['Oracle Name']] = row['Rankings'].split(",")
        
        matrix_df = pd.DataFrame(matrix_data)
        st.table(matrix_df)
    else:
        st.info("No prophecies found in the vault.")

with tab3:
    st.subheader("DETAILED PROPHECIES")
    if not subs_df.empty:
        for _, row in subs_df.iterrows():
            with st.expander(f"PROPHECY: {row['Oracle Name']}"):
                p_list = row['Rankings'].split(",")
                for i, team in enumerate(p_list):
                    st.write(f"**{i+1}.** {team}")
    else:
        st.info("No data in vault.")

with tab4:
    st.subheader("GRAND ARBITER (LIVE RESULTS)")
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    st.info("Edit your Google Sheet 'Results' tab to update tournament rankings.")
