import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- CONFIGURATION ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"
GITHUB_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/"
LIQUIPEDIA_URL = "https://liquipedia.net/dota2/The_International/2026/Group_Stage" # Update to exact tournament URL

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="centered")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- THE SILENT ARBITER (SCRAPER & SYNC) ---
def sync_live_results():
    try:
        # 1. Check if we need to update (30-minute throttle)
        meta = conn.read(worksheet="Metadata", ttl=0)
        last_update_str = meta.iloc[0, 0]
        last_update = datetime.strptime(last_update_str, "%Y-%m-%d %H:%M:%S")
        
        if datetime.now() < last_update + timedelta(minutes=30):
            return # Too soon, skip scraping
            
    except Exception:
        pass # If Metadata is missing, we proceed with scrape anyway

    # 2. Scrape Liquipedia
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(LIQUIPEDIA_URL, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Target the Group Stage tables
        tables = soup.find_all('table', class_='grouptable')
        live_ranks = {}
        
        for table in tables:
            rows = table.find_all('tr')[1:] # Skip header
            for row in rows:
                rank_cell = row.find('td', class_='grouptable-rank')
                team_cell = row.find('span', class_='team-template-text')
                if rank_cell and team_cell:
                    rank = rank_cell.text.strip()
                    team = team_cell.text.strip()
                    live_ranks[team] = rank

        # 3. Update the "Results" Sheet
        current_results = conn.read(worksheet="Results", ttl=0)
        
        for index, row in current_results.iterrows():
            team_name = row['Team']
            if team_name in live_ranks:
                current_results.at[index, 'Rank'] = live_ranks[team_name]
        
        # 4. Write back to Sheets
        conn.update(worksheet="Results", data=current_results)
        
        # 5. Update Timestamp
        new_meta = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S")]], columns=["LastUpdate"])
        conn.update(worksheet="Metadata", data=new_meta)
        
    except Exception as e:
        st.error(f"Arbiter Error: {e}")

# TRIGGER SYNC ON LOAD
sync_live_results()

# --- DATA LOADING ---
@st.cache_data(ttl=60) # Short cache for UI responsiveness
def load_data():
    try:
        res = conn.read(worksheet="Results", ttl=0).dropna(how='all')
        sub = conn.read(worksheet="Submissions", ttl=0).dropna(how='all')
        return res, sub
    except:
        return pd.DataFrame(), pd.DataFrame()

results_df, subs_df = load_data()

# --- LOGO HELPER ---
def get_logo_url(name):
    return f"{GITHUB_BASE}{name.replace(' ', '%20')}.png"

# --- HEADER ---
st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <img src="{GITHUB_BASE}Aegis.png" width="80">
        <h1 style="margin-top: 10px; color: #1a1a1a; letter-spacing: -1px;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

# TAB LAYOUT
tabs = st.tabs(["📊 LIVE STANDINGS", "🏆 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

with tabs[0]:
    st.subheader("Official Tournament Standings (Synced via Liquipedia)")
    if not results_df.empty:
        # Convert Rank to numeric for proper sorting
        results_df['Rank'] = pd.to_numeric(results_df['Rank'], errors='coerce').fillna(0)
        sorted_results = results_df.sort_values("Rank")
        
        for _, row in sorted_results.iterrows():
            t_name = str(row['Team'])
            t_rank = int(row['Rank'])
            t_status = str(row.get('Status', 'Active')).strip().lower()
            t_logo = get_logo_url(t_name)
            
            card_bg = "#fee2e2" if t_status == "completed" else "#ffffff"
            card_border = "#ef4444" if t_status == "completed" else "#eee"
            
            st.markdown(f"""
                <div style="display: flex; align-items: center; background: {card_bg}; 
                            margin-bottom: 8px; padding: 12px; border-radius: 8px; 
                            border: 1px solid {card_border};">
                    <span style="font-weight: bold; color: #57606a; width: 35px; font-family: monospace;">#{t_rank}</span>
                    <img src="{t_logo}" style="width: 28px; height: 28px; margin-right: 12px; object-fit: contain;">
                    <span style="font-weight: 600;">{t_name}</span>
                </div>
            """, unsafe_allow_html=True)

# [Remaining tabs for Leaderboard, Matrix, and Protocol stay identical to previous stable version]
