import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import json

# --- CONFIGURATION & UI SETUP ---
st.set_page_config(page_title="Aegis Oracle: TI 2026", layout="wide", page_icon="🔮")

# Shanghai Shadow-Tech Styling
st.markdown("""
    <style>
    .main { background-color: #0b0e14; color: #e0e0e0; }
    .stButton>button { 
        background: linear-gradient(90deg, #00f2ff, #7000ff); 
        color: white; border: none; border-radius: 5px; width: 100%;
    }
    .leaderboard-card {
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid #00f2ff;
        padding: 15px; border-radius: 10px; margin-bottom: 10px;
    }
    h1, h2, h3 { color: #00f2ff !important; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CORE LOGIC: THE ORACLE SCORING ---
def calculate_golf_score(pred_list, actual_results_df):
    """
    Calculates points: ABS(Predicted Rank - Official Rank) * Multiplier.
    Lowest score wins.
    """
    total_score = 0
    actual_dict = dict(zip(actual_results_df['Team'], actual_results_df['Rank']))
    
    for i, team in enumerate(pred_list):
        pred_rank = i + 1
        official_rank = actual_dict.get(team, 0)
        
        if official_rank == 0: continue # Game not played/result not in
        
        # Multipliers for top 3 picks
        multiplier = 1
        if pred_rank == 1: multiplier = 4
        elif pred_rank == 2: multiplier = 3
        elif pred_rank in [3, 4]: multiplier = 2
        
        gap = abs(pred_rank - official_rank)
        total_score += (gap * multiplier)
        
    return total_score

# --- ON-DEMAND SCRAPER (Placeholder for Aug 13) ---
def auto_refresh_standings():
    """Triggered if data is > 30 mins old."""
    try:
        # Step 1: Check Metadata
        meta = conn.read(worksheet="Metadata", ttl=0)
        last_update_str = meta.iloc[0, 0]
        last_update = datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S")

        if datetime.now() - last_update > timedelta(minutes=30):
            # ON AUG 13: We replace this with real scraping logic
            # For now, it just notifies that it's checking
            st.toast("Synchronizing with Shanghai Main Stage...")
            
            # Update Timestamp in Sheet
            new_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.update(worksheet="Metadata", data=pd.DataFrame({"LastUpdate": [new_time]}))
    except Exception as e:
        pass # Fail silently to not block the UI

# --- APP TABS ---
st.title("🏯 AEGIS ORACLE: SHANGHAI 2026")
tab1, tab2, tab3 = st.tabs(["🏆 Leaderboard", "🔮 Lock Predictions", "📊 Tournament Intel"])

auto_refresh_standings()

with tab1:
    st.subheader("Current Standings (Ruben vs Stok vs Frederik)")
    
    try:
        results_df = conn.read(worksheet="Results", ttl=0)
        subs_df = conn.read(worksheet="Submissions", ttl=0)
        
        if not subs_df.empty:
            leaderboard = []
            for index, row in subs_df.iterrows():
                # Rankings are stored as a comma-separated string in the sheet
                pred_list = row['Rankings'].split(",")
                score = calculate_golf_score(pred_list, results_df)
                leaderboard.append({"Oracle": row['Oracle Name'], "Score": score})
            
            # Display sorted leaderboard
            lb_df = pd.DataFrame(leaderboard).sort_values(by="Score")
            for i, row in lb_df.iterrows():
                st.markdown(f"""
                <div class="leaderboard-card">
                    <span style="font-size: 20px;"><b>{row['Oracle']}</b></span>
                    <span style="float: right; color: #00f2ff;">{row['Score']} Points</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No prophecies have been locked in yet.")
    except Exception as e:
        st.error(f"Grand Arbiter Error: Ensure your Sheet tabs are named 'Submissions' and 'Results'.")

with tab2:
    st.subheader("The Prediction Arena")
    # Get team list from Results tab
    teams_df = conn.read(worksheet="Results", ttl=3600)
    team_list = teams_df['Team'].tolist()
    
    with st.form("prophecy_form"):
        oracle_name = st.text_input("Enter your Oracle Name (e.g., Ruben):")
        st.write("Rank the teams (Top to Bottom):")
        
        # NOTE: Using a simple multiselect as a fallback for drag-drop 
        # because streamlit-sortables requires specific environment setup
        ranked_prediction = st.multiselect("Select teams in order (1st to 16th):", team_list)
        
        submitted = st.form_submit_button("LOCK IN PREDICTIONS")
        
        if submitted:
            if len(ranked_prediction) != len(team_list):
                st.warning(f"You must rank all {len(team_list)} teams!")
            elif not oracle_name:
                st.warning("Enter your name to claim your prophecy.")
            else:
                # Format data for GSheets
                new_data = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(ranked_prediction)
                }])
                
                # Append to 'Submissions' tab
                existing_data = conn.read(worksheet="Submissions")
                updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                st.success("Prophecy Locked. The Aegis awaits.")

with tab3:
    st.subheader("Official Tournament Ranks")
    st.write("These ranks are updated by the Arbiter (You) or the Auto-Scraper.")
    try:
        st.table(results_df)
    except:
        st.write("Results table not found.")

st.sidebar.markdown("---")
st.sidebar.info("Aegis Oracle v2.6 | Shanghai International Hub")
