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

# --- 1. THE CONNECTION (SIMPLIFIED) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        results = conn.read(worksheet="Results", ttl=0)
        subs = conn.read(worksheet="Submissions", ttl=0)
        return results, subs, None
    except Exception as e:
        return None, None, str(e)

results_df, subs_df, error = get_data()

# --- 2. SYSTEM HEALTH CHECK ---
if error:
    st.error(f"❌ DATABASE OFFLINE")
    st.info("Check these 3 things in your Google Sheet:\n1. Does a tab named 'Results' exist?\n2. Does a tab named 'Submissions' exist?\n3. Did you share the sheet with your service account email as an EDITOR?")
    st.stop()

# --- 3. MAIN INTERFACE ---
st.title("🏮 AEGIS ORACLE: 2026")

tab_submit, tab_leaderboard = st.tabs(["🎯 SUBMIT PREDICTIONS", "🏆 LEADERBOARD"])

with tab_submit:
    st.header("Lock in your Prophecy")
    
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        name = st.text_input("Your Name (Oracle ID)", placeholder="e.g. Ruben")
        
        team_list = results_df['Team'].tolist()
        # The multiselect handles the picking
        picks = st.multiselect("Pick teams in order (1st to 16th)", options=team_list)
        
        st.divider()
        
        # DIRECT SUBMIT LOGIC
        ready = len(picks) == 16 and name
        if st.button("🔥 LOCK IN PROPHECY", disabled=not ready, use_container_width=True):
            with st.spinner("Writing directly to Sheet..."):
                # 1. Create the new row
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": name,
                    "Rankings": ",".join(picks)
                }])
                # 2. Append and Update
                updated_subs = pd.concat([subs_df, new_entry], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_subs)
                st.success(f"Prophecy Sealed for {name}!")
                st.balloons()
                st.rerun()

    with col_preview:
        st.subheader("Your Ranked List")
        if picks:
            for i, team in enumerate(picks):
                st.markdown(f'<div class="rank-tag"><span class="rank-num">#{i+1:02d}</span> {team}</div>', unsafe_allow_html=True)
            st.caption(f"Count: {len(picks)}/16")
        else:
            st.info("Select teams on the left to see their rank here.")

with tab_leaderboard:
    st.subheader("Current Rankings")
    if not subs_df.empty:
        st.dataframe(subs_df[['Oracle Name', 'Timestamp']], use_container_width=True)
    else:
        st.write("No predictions submitted yet.")
