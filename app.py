import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- UI SETTINGS ---
st.set_page_config(page_title="AEGIS ORACLE", layout="wide")

st.markdown("""
    <style>
    .rank-tag { 
        background: #1e2128; border-left: 5px solid #00f2ff; 
        padding: 10px; margin: 5px 0; border-radius: 5px;
        font-family: monospace; font-size: 18px;
    }
    .rank-num { color: #00f2ff; font-weight: bold; margin-right: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. THE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # We read without TTL to ensure we see the latest data
        results = conn.read(worksheet="Results")
        subs = conn.read(worksheet="Submissions")
        return results, subs, None
    except Exception as e:
        return None, None, str(e)

results_df, subs_df, error_msg = get_data()

# --- 2. DIAGNOSTICS (Only shows if there is a problem) ---
if error_msg:
    st.error("🚨 CONNECTION FAILED")
    with st.expander("Show Technical Error Details"):
        st.code(error_msg)
    st.info("💡 COMMON FIX: Ensure your Service Account has 'Editor' access and the Sheet URL is in your Streamlit Secrets.")
    st.stop()

# Ensure Results tab isn't empty
if 'Team' not in results_df.columns:
    st.warning("⚠️ SETUP REQUIRED: Your 'Results' tab must have a column header named **Team** with the list of teams below it.")
    st.stop()

# --- 3. MAIN INTERFACE ---
st.title("🏮 AEGIS ORACLE: 2026")

tab_submit, tab_leaderboard = st.tabs(["🎯 SUBMIT PREDICTIONS", "🏆 LEADERBOARD"])

with tab_submit:
    st.header("Lock in your Prophecy")
    
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        name = st.text_input("Your Name (Oracle ID)", placeholder="e.g. Ruben")
        
        # Populate team list from your Results tab
        team_list = results_df['Team'].dropna().tolist()
        
        # Immediate Rank Numbers: The order picked = Rank
        picks = st.multiselect("Pick teams in order (1st to 16th)", options=team_list)
        
        st.divider()
        
        # DIRECT SUBMIT
        ready = len(picks) == len(team_list) and len(team_list) > 0 and name
        if st.button("🔥 LOCK IN PROPHECY", disabled=not ready, use_container_width=True):
            with st.spinner("Writing to Sheet..."):
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": name,
                    "Rankings": ",".join(picks)
                }])
                # Combine and update
                updated_subs = pd.concat([subs_df, new_entry], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_subs)
                st.success(f"Prophecy Sealed for {name}!")
                st.balloons()
                st.rerun()

    with col_preview:
        st.subheader("Your Ranked List")
        if picks:
            for i, team in enumerate(picks):
                # This displays the Rank Number #01, #02, etc. next to the team immediately
                st.markdown(f'<div class="rank-tag"><span class="rank-num">#{i+1:02d}</span> {team}</div>', unsafe_allow_html=True)
            st.caption(f"Progress: {len(picks)}/{len(team_list)}")
        else:
            st.info("Select teams on the left to see their rank here.")

with tab_leaderboard:
    st.subheader("Submitted Prophecies")
    if not subs_df.empty:
        st.dataframe(subs_df, use_container_width=True, hide_index=True)
    else:
        st.write("No predictions submitted yet.")
