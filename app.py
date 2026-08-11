import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- UI CONFIG ---
st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide", page_icon="🏮")

# --- SHANGHAI SHADOW-TECH CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&family=JetBrains+Mono&display=swap');
    .main { background-color: #0b0e14; color: #e0e0e0; font-family: 'Inter', sans-serif; }
    h1, h2 { color: #00f2ff !important; text-transform: uppercase; letter-spacing: 3px; font-family: 'Inter'; }
    .stMetric { background: rgba(112, 0, 255, 0.1); border: 1px solid #7000ff; padding: 15px; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: #00f2ff !important; font-family: 'JetBrains Mono'; }
    .leaderboard-row { border-bottom: 1px solid #1a1d23; padding: 10px 0; }
    .status-locked { color: #ff4b4b; font-weight: bold; }
    .status-play { color: #00f2ff; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNECTIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- SCORING LOGIC ---
def calculate_score(predictions, actual_results):
    """
    Points = ABS(Pred - Actual) * Multiplier
    Multipliers: 1st=4x, 2nd=3x, 3rd/4th=2x, rest=1x
    """
    actual_map = dict(zip(actual_results['Team'], actual_results['Rank']))
    total_pts = 0
    
    for i, team in enumerate(predictions):
        pred_rank = i + 1
        real_rank = actual_map.get(team, 0)
        
        if real_rank == 0: continue # Team not in results yet
        
        multiplier = 1
        if pred_rank == 1: multiplier = 4
        elif pred_rank == 2: multiplier = 3
        elif pred_rank in [3, 4]: multiplier = 2
        
        total_pts += abs(pred_rank - real_rank) * multiplier
        
    return total_pts

# --- DATA FETCHING ---
try:
    results_df = conn.read(worksheet="Results", ttl=0)
    subs_df = conn.read(worksheet="Submissions", ttl=0)
except Exception as e:
    st.error(f"⚠️ CONNECTION BREACH: Ensure 'Results' and 'Submissions' tabs exist. {e}")
    st.stop()

# --- HEADER SECTION ---
col1, col2 = st.columns([2, 1])
with col1:
    st.title("🏮 AEGIS ORACLE: SHANGHAI 2026")
    st.caption("ULTIMATE TOURNAMENT PREDICTION TERMINAL")

with col2:
    if not results_df.empty:
        locked_count = len(results_df[results_df['Status'] == 'Locked'])
        st.metric("TOURNAMENT PROGRESS", f"{locked_count}/16 LOCKED")

# --- MAIN INTERFACE ---
tab1, tab2, tab3 = st.tabs(["🏆 ORACLE LEADERBOARD", "📋 PREDICTOR STANDINGS", "🛠 ARBITER VIEW"])

with tab1:
    st.subheader("CURRENT SCOREBOARD")
    if not subs_df.empty and not results_df.empty:
        scores = []
        for _, row in subs_df.iterrows():
            pred_list = row['Rankings'].split(",")
            total = calculate_score(pred_list, results_df)
            scores.append({"Oracle": row['Oracle Name'], "Total Penalty Points": total})
        
        score_df = pd.DataFrame(scores).sort_values("Total Penalty Points")
        
        # Display large metrics for the top 3
        cols = st.columns(len(score_df))
        for i, (idx, row) in enumerate(score_df.iterrows()):
            cols[i].metric(row['Oracle'], f"{row['Total Penalty Points']} PTS")
            
        st.table(score_df)
    else:
        st.info("Awaiting predictions and results...")

with tab2:
    st.subheader("THE PREDICTIONS")
    if not subs_df.empty:
        for _, row in subs_df.iterrows():
            with st.expander(f"VIEW PROPHECY: {row['Oracle Name']}"):
                p_list = row['Rankings'].split(",")
                for i, team in enumerate(p_list):
                    st.write(f"**{i+1}.** {team}")
    else:
        st.info("No prophecies locked in.")

with tab3:
    st.subheader("GRAND ARBITER TERMINAL (LIVE RESULTS)")
    if not results_df.empty:
        # Display the current results with status colors
        styled_df = results_df.copy()
        st.dataframe(
            styled_df,
            use_container_width=True,
            column_config={
                "Status": st.column_config.TextColumn("Status", help="Locked = Final Result, In-Play = Estimate")
            }
        )
        st.info("💡 To update these rankings, edit your Google Sheet directly. The app will refresh automatically.")
    else:
        st.warning("No teams found in 'Results' tab.")

# --- SIDEBAR SUBMISSION ---
with st.sidebar:
    st.header("LOCK IN PROPHECY")
    with st.form("oracle_submission"):
        oracle_name = st.text_input("Name (e.g., Ruben, Stok, Frederik)")
        # Get list of teams from Results tab
        team_pool = results_df['Team'].tolist() if not results_df.empty else []
        ranked_selection = st.multiselect("Select Teams in order (1st to 16th)", team_pool)
        
        if st.form_submit_button("LOCK IN"):
            if len(ranked_selection) == 16 and oracle_name:
                new_sub = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(ranked_selection)
                }])
                # Append to existing
                updated_subs = pd.concat([subs_df, new_sub], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_subs)
                st.success("Prophecy encrypted and stored.")
                st.rerun()
            else:
                st.error("You must rank all 16 teams.")
