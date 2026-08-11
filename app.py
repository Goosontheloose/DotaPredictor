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
    .stMetric { background: rgba(0, 242, 255, 0.05); border: 1px solid #00f2ff; padding: 15px; border-radius: 5px; }
    .rank-box { 
        background: rgba(112, 0, 255, 0.1); 
        border-left: 4px solid #7000ff; 
        padding: 8px 15px; 
        margin: 5px 0; 
        font-family: 'JetBrains Mono';
        display: flex;
        justify-content: space-between;
    }
    .rank-num { color: #00f2ff; font-weight: bold; margin-right: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNECTIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- DATA FETCHING ---
try:
    results_df = conn.read(worksheet="Results", ttl=0)
    subs_df = conn.read(worksheet="Submissions", ttl=0)
except Exception as e:
    st.error("⚠️ CONNECTION BREACH: Check your Google Sheet tabs (Results & Submissions).")
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

# --- SIDEBAR: THE PROPHECY RECEIPT ---
with st.sidebar:
    st.title("🏮 LOCK IN")
    oracle_name = st.text_input("ORACLE NAME", placeholder="e.g. Ruben")
    
    team_pool = results_df['Team'].tolist() if not results_df.empty else []
    
    # We use a standard multiselect but HIDE the tags using CSS below
    selected_teams = st.multiselect(
        "SELECT TEAMS IN ORDER (1-16)",
        options=team_pool,
        help="Click teams in the order of their predicted finish."
    )

    # --- DYNAMIC RECEIPT UI ---
    if selected_teams:
        st.markdown("### 📝 PROPHECY RECEIPT")
        for i, team in enumerate(selected_teams):
            st.markdown(f"""
                <div class="rank-box">
                    <span><span class="rank-num">#{i+1:02d}</span> {team}</span>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"**Progress:** {len(selected_teams)}/16")
        
        # Action Button (Outside of a form for better reliability)
        can_submit = len(selected_teams) == 16 and oracle_name
        if st.button("🔥 FINALIZE PROPHECY", disabled=not can_submit, use_container_width=True):
            with st.spinner("Encrypting to Vault..."):
                new_data = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%m/%d %H:%M"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(selected_teams)
                }])
                updated_df = pd.concat([subs_df, new_data], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                st.success("VAULT UPDATED.")
                st.balloons()
                st.rerun()

# --- MAIN DASHBOARD ---
st.title("🏮 AEGIS ORACLE: SHANGHAI 2026")

tab1, tab2 = st.tabs(["🏆 LEADERBOARD", "📊 TOURNAMENT STATUS"])

with tab1:
    if not subs_df.empty:
        scores = []
        for _, row in subs_df.iterrows():
            p_list = row['Rankings'].split(",")
            total = calculate_score(p_list, results_df)
            scores.append({"Oracle": row['Oracle Name'], "Penalty Points": total})
        
        score_df = pd.DataFrame(scores).sort_values("Penalty Points")
        c = st.columns(len(score_df))
        for i, (idx, row) in enumerate(score_df.iterrows()):
            c[i].metric(row['Oracle'], f"{row['Penalty Points']} PTS")
        st.dataframe(score_df, use_container_width=True, hide_index=True)
    else:
        st.info("Vault is empty. Awaiting first prophecy.")

with tab2:
    st.subheader("CURRENT STANDINGS")
    st.dataframe(results_df, use_container_width=True, hide_index=True)
