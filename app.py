import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- 1. UI CONFIG & SHANGHAI TECH THEME ---
st.set_page_config(page_title="Aegis Oracle: TI 2026", layout="wide", page_icon="🔮")

st.markdown("""
    <style>
    /* Main Background and Text */
    .main { background-color: #0b0e14; color: #e0e0e0; }
    
    /* Custom Buttons */
    .stButton>button { 
        background: linear-gradient(90deg, #00f2ff, #7000ff); 
        color: white; border: none; border-radius: 5px; width: 100%; font-weight: bold;
    }
    
    /* Leaderboard Cards */
    .leaderboard-card {
        background: rgba(255, 255, 255, 0.03);
        border-left: 5px solid #00f2ff;
        padding: 20px; border-radius: 10px; margin-bottom: 15px;
        transition: 0.3s;
    }
    .leaderboard-card:hover { background: rgba(255, 255, 255, 0.08); }
    
    /* Headers */
    h1, h2, h3 { color: #00f2ff !important; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 2px; }
    
    /* Metric styling */
    [data-testid="stMetricValue"] { color: #7000ff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CONNECTIONS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. THE AUTO-ARBITER (SCRAPER) ---
def run_auto_scrape():
    """Targeting TI 2024/2025 for calibration testing."""
    url = "https://liquipedia.net/dota2/The_International/2024" 
    headers = {'User-Agent': 'AegisOracle-Bot-2.0'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'wikitable'})
        
        data = []
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) >= 2:
                # Rank logic (handles '1st', '2nd', '3rd-4th')
                rank_raw = cols[0].text.strip().split('-')[0]
                rank_num = ''.join(filter(str.isdigit, rank_raw))
                # Team Name logic
                team_name = cols[1].find('span', {'class': 'team-template-text'}).text.strip()
                
                if rank_num and team_name:
                    data.append({"Team": team_name, "Rank": int(rank_num)})
        
        return pd.DataFrame(data).sort_values("Rank")
    except Exception as e:
        st.error(f"Scraper Offline: {e}")
        return None

def sync_with_google_sheets():
    """On-demand sync logic."""
    try:
        meta = conn.read(worksheet="Metadata", ttl=0)
        last_update = datetime.strptime(meta.iloc[0, 0], "%Y-%m-%d %H:%M:%S")
        
        if datetime.now() - last_update > timedelta(minutes=30):
            with st.spinner("Scrying Liquipedia for latest standings..."):
                new_results = run_auto_scrape()
                if new_results is not None:
                    # Update 'Results' tab
                    conn.update(worksheet="Results", data=new_results)
                    # Update 'Metadata' timestamp
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn.update(worksheet="Metadata", data=pd.DataFrame({"LastUpdate": [now_str]}))
                    st.toast("Oracle Synchronized!")
    except:
        st.warning("Metadata tab is empty or missing. Check your Google Sheet.")

# --- 4. THE SCORING ENGINE ---
def calculate_oracle_score(pred_list, actual_df):
    actual_dict = dict(zip(actual_df['Team'], actual_df['Rank']))
    total_score = 0
    details = []
    
    for i, team in enumerate(pred_list):
        pred_rank = i + 1
        official_rank = int(actual_dict.get(team, 0))
        
        if official_rank == 0: continue
        
        # Multipliers
        multiplier = 1
        if pred_rank == 1: multiplier = 4
        elif pred_rank == 2: multiplier = 3
        elif pred_rank in [3, 4]: multiplier = 2
        
        gap = abs(pred_rank - official_rank)
        points = gap * multiplier
        total_score += points
        details.append({"Team": team, "Prediction": pred_rank, "Actual": official_rank, "Multiplier": f"{multiplier}x", "Points": points})
        
    return total_score, pd.DataFrame(details)

# --- 5. MAIN APP INTERFACE ---
st.title("🏮 AEGIS ORACLE: SHANGHAI 2026")
sync_with_google_sheets()

tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🔮 LOCK PROPHECY", "📊 LIVE DATA"])

with tab1:
    st.subheader("Global Oracle Standings")
    try:
        results_df = conn.read(worksheet="Results", ttl=0)
        subs_df = conn.read(worksheet="Submissions", ttl=0)
        
        if not subs_df.empty:
            leaderboard_data = []
            for _, row in subs_df.iterrows():
                p_list = row['Rankings'].split(",")
                score, detail_df = calculate_oracle_score(p_list, results_df)
                leaderboard_data.append({"Name": row['Oracle Name'], "Score": score, "Data": detail_df})
            
            # Sort: Lowest Score = Rank 1
            lb_sorted = sorted(leaderboard_data, key=lambda x: x['Score'])
            
            for rank, entry in enumerate(lb_sorted, 1):
                with st.expander(f"RANK #{rank} | {entry['Name']} — {entry['Score']} Points"):
                    st.table(entry['Data'])
        else:
            st.info("The Oracle awaits your first prediction in the 'Lock Prophecy' tab.")
    except:
        st.error("Connection lost. Verify Google Sheet permissions.")

with tab2:
    st.subheader("Enter the Prediction Arena")
    # Fetch team names for the picker
    teams_for_picker = results_df['Team'].tolist() if 'results_df' in locals() else []
    
    with st.form("submission_form"):
        oracle_name = st.text_input("Enter Oracle Name (Ruben, Stok, Frederik):")
        st.write("Rank the teams from 1st to 16th (Select in order):")
        user_picks = st.multiselect("Sequence of Victory:", teams_for_picker)
        
        if st.form_submit_button("LOCK IN PROPHECY"):
            if len(user_picks) != len(teams_for_picker):
                st.warning(f"Prophecy incomplete. You must rank all {len(teams_for_picker)} teams.")
            elif not oracle_name:
                st.warning("Identity required to enter the leaderboard.")
            else:
                new_row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(user_picks)
                }])
                existing = conn.read(worksheet="Submissions")
                updated = pd.concat([existing, new_row], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated)
                st.success("Your vision has been recorded in the cloud.")
                st.rerun()

with tab3:
    st.subheader("Current Tournament Data")
    if 'results_df' in locals():
        st.dataframe(results_df, use_container_width=True, hide_index=True)
    
    st.sidebar.markdown("### SYSTEM STATUS")
    st.sidebar.write(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
    st.sidebar.info("Auto-Arbiter: ONLINE")
