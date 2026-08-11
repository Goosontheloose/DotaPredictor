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
    h1, h2, h3 { color: #00f2ff !important; text-transform: uppercase; letter-spacing: 2px; }
    .stMetric { background: rgba(0, 242, 255, 0.05); border: 1px solid #00f2ff; padding: 15px; border-radius: 5px; }
    
    /* Ranking Box UI */
    .rank-box { 
        background: rgba(112, 0, 255, 0.1); 
        border-left: 4px solid #7000ff; 
        padding: 10px 20px; 
        margin: 8px 0; 
        font-family: 'JetBrains Mono';
        font-size: 1.1rem;
        border-radius: 0 5px 5px 0;
    }
    .rank-num { color: #00f2ff; font-weight: bold; margin-right: 15px; font-size: 1.2rem; }
    
    /* Matrix Table Styling */
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
    st.error("⚠️ CONNECTION ERROR: Ensure 'Results' and 'Submissions' tabs exist in your Sheet.")
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

# --- MAIN DASHBOARD ---
st.title("🏮 AEGIS ORACLE: SHANGHAI 2026")

# New Tab Structure with "SUBMIT PROPHECY" as the first focus
tabs = st.tabs(["🔮 SUBMIT PROPHECY", "🏆 LEADERBOARD", "📋 PREDICTION MATRIX", "🛠 ARBITER VIEW"])

# --- TAB 1: PREDICTION ARENA (The new center-stage submission) ---
with tabs[0]:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("1. YOUR IDENTITY")
        oracle_name = st.text_input("ORACLE NAME", placeholder="Enter your handle (e.g. Ruben)")
        
        st.subheader("2. THE RANKING")
        team_pool = results_df['Team'].tolist() if not results_df.empty else []
        selected_teams = st.multiselect(
            "CHOOSE TEAMS IN ORDER (1st to 16th)", 
            options=team_pool,
            help="The order you click them is the order they are ranked."
        )
        
        st.divider()
        can_submit = len(selected_teams) == 16 and oracle_name
        if st.button("🔥 LOCK IN FINAL PROPHECY", disabled=not can_submit, use_container_width=True):
            with st.spinner("Writing to the Vault..."):
                new_data = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(selected_teams)
                }])
                updated_df = pd.concat([subs_df, new_data], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                st.success(f"Prophecy for {oracle_name} has been sealed.")
                st.balloons()
                st.rerun()

    with col2:
        st.subheader("3. LIVE RECEIPT")
        if selected_teams:
            for i, team in enumerate(selected_teams):
                st.markdown(f'<div class="rank-box"><span class="rank-num">#{i+1:02d}</span> {team}</div>', unsafe_allow_html=True)
            
            progress = len(selected_teams)
            st.progress(progress / 16)
            st.write(f"**Verification Status:** {progress}/16 Teams Selected")
        else:
            st.info("Awaiting selection to generate receipt...")

# --- TAB 2: LEADERBOARD ---
with tabs[1]:
    if not subs_df.empty:
        scores = []
        for _, row in subs_df.iterrows():
            p_list = row['Rankings'].split(",")
            total = calculate_score(p_list, results_df)
            scores.append({"Oracle": row['Oracle Name'], "Penalty Points": total})
        
        score_df = pd.DataFrame(scores).sort_values("Penalty Points")
        
        # Top 3 visual highlights
        m_cols = st.columns(min(len(score_df), 3))
        for i, (idx, row) in enumerate(score_df.head(3).iterrows()):
            m_cols[i].metric(f"Rank {i+1}: {row['Oracle']}", f"{row['Penalty Points']} PTS")
            
        st.table(score_df)
    else:
        st.info("The Oracle vault is empty.")

# --- TAB 3: MATRIX ---
with tabs[2]:
    st.subheader("GLOBAL COMPARISON MATRIX")
    if not subs_df.empty:
        matrix_data = {"Rank": [f"#{i+1:02d}" for i in range(16)]}
        for _, row in subs_df.iterrows():
            matrix_data[row['Oracle Name']] = row['Rankings'].split(",")
        
        matrix_df = pd.DataFrame(matrix_data)
        st.table(matrix_df)
    else:
        st.info("No data available.")

# --- TAB 4: ARBITER ---
with tabs[3]:
    st.subheader("GRAND ARBITER TERMINAL")
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    st.caption("Admin Note: Update the 'Results' tab in Google Sheets to refresh scores.")
