import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- UI CONFIG ---
st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide", page_icon="🏮")

# --- CUSTOM CSS (Shanghai Shadow-Tech) ---
st.markdown("""
    <style>
    .rank-box { 
        background: rgba(112, 0, 255, 0.1); 
        border-left: 4px solid #7000ff; 
        padding: 10px 15px; 
        margin: 5px 0; 
        font-family: monospace;
    }
    .rank-num { color: #00f2ff; font-weight: bold; margin-right: 15px; font-size: 1.1rem; }
    .stMetric { background: rgba(0, 242, 255, 0.05); border: 1px solid #00f2ff; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. CONNECTION & DATA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        res = conn.read(worksheet="Results", ttl=0)
        sub = conn.read(worksheet="Submissions", ttl=0)
        return res, sub, None
    except Exception as e:
        return None, None, str(e)

results_df, subs_df, error = load_data()

# --- 2. ERROR HANDLING ---
if error:
    st.error("🚨 CONNECTION ERROR")
    with st.expander("Diagnostic Info"):
        st.code(error)
    st.stop()

# --- 3. SCORING LOGIC ---
def calculate_score(predictions, actual_df):
    # Map teams to their official rank from the Sheet
    actual_map = dict(zip(actual_df['Team'], actual_df['Rank']))
    total_penalty = 0
    
    for i, team in enumerate(predictions):
        pred_rank = i + 1
        real_rank = actual_map.get(team, 0)
        
        # If real_rank is 0 or empty, tournament hasn't finished for that team yet
        if real_rank == 0 or pd.isna(real_rank):
            continue
            
        # Multipliers based on importance of the prediction slot
        multiplier = 1
        if pred_rank == 1: multiplier = 4
        elif pred_rank == 2: multiplier = 3
        elif pred_rank in [3, 4]: multiplier = 2
        
        # Penalty = Distance * Multiplier
        total_penalty += abs(pred_rank - real_rank) * multiplier
        
    return total_penalty

# --- 4. MAIN INTERFACE ---
st.title("🏮 AEGIS ORACLE: SHANGHAI 2026")

tabs = st.tabs(["🎯 SUBMIT PROPHECY", "🏆 LEADERBOARD", "📋 COMPARISON MATRIX", "🛠 ARBITER VIEW"])

# --- TAB: SUBMIT ---
with tabs[0]:
    col_in, col_pre = st.columns([1, 1], gap="large")
    
    with col_in:
        st.subheader("1. Identify & Predict")
        oracle_name = st.text_input("Oracle Name", placeholder="e.g. Ruben")
        
        team_pool = results_df['Team'].dropna().tolist()
        picks = st.multiselect("Select Teams in Order (1st → 16th)", options=team_pool)
        
        st.divider()
        ready = len(picks) == len(team_pool) and oracle_name
        if st.button("🔥 LOCK IN PROPHECY", disabled=not ready, use_container_width=True):
            new_row = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Oracle Name": oracle_name,
                "Rankings": ",".join(picks)
            }])
            updated_subs = pd.concat([subs_df, new_row], ignore_index=True)
            conn.update(worksheet="Submissions", data=updated_subs)
            st.success(f"Prophecy for {oracle_name} recorded.")
            st.balloons()
            st.rerun()

    with col_pre:
        st.subheader("2. Live Rank Preview")
        if picks:
            for i, team in enumerate(picks):
                # Shows the rank number immediately next to the team
                st.markdown(f'<div class="rank-box"><span class="rank-num">#{i+1:02d}</span> {team}</div>', unsafe_allow_html=True)
            st.caption(f"Progress: {len(picks)}/{len(team_pool)}")
        else:
            st.info("Pick teams on the left to generate your ranked prophecy.")

# --- TAB: LEADERBOARD ---
with tabs[1]:
    st.subheader("The Great Standings")
    if not subs_df.empty:
        leaderboard_data = []
        for _, row in subs_df.iterrows():
            p_list = row['Rankings'].split(",")
            score = calculate_score(p_list, results_df)
            leaderboard_data.append({
                "Oracle": row['Oracle Name'],
                "Penalty Points": score,
                "Submission Date": row['Timestamp']
            })
        
        lb_df = pd.DataFrame(leaderboard_data).sort_values("Penalty Points")
        
        # High-score metrics
        top_cols = st.columns(min(len(lb_df), 4))
        for i, (idx, row) in enumerate(lb_df.head(4).iterrows()):
            top_cols[i].metric(f"#{i+1} {row['Oracle']}", f"{row['Penalty Points']} PTS")
            
        st.table(lb_df)
    else:
        st.info("The vault is currently empty.")

# --- TAB: MATRIX ---
with tabs[2]:
    st.subheader("Oracle Comparison Matrix")
    if not subs_df.empty:
        # Build a table where each Oracle is a column
        matrix = {"Rank": [f"#{i+1:02d}" for i in range(len(team_pool))]}
        for _, row in subs_df.iterrows():
            matrix[row['Oracle Name']] = row['Rankings'].split(",")
        
        st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)
    else:
        st.info("No predictions to compare.")

# --- TAB: ARBITER ---
with tabs[3]:
    st.subheader("Tournament Results (Source of Truth)")
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    st.info("Note: To update scores, edit the 'Rank' column in your Google Sheet 'Results' tab.")
