import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIGURATION ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"
GITHUB_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/"
LIQUIPEDIA_URL = "https://liquipedia.net/dota2/The_International/2026/Group_Stage"

st.set_page_config(page_title="TI 2026", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- THE SILENT ARBITER ---
def run_silent_arbiter():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(LIQUIPEDIA_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        live_ranks = {}
        rows = soup.find_all('tr')
        for row in rows:
            t_cell = row.find('span', class_='team-template-text')
            if t_cell:
                team_name = t_cell.get_text().strip().lower()
                cells = row.find_all(['td', 'th'])
                if cells:
                    rank_val = cells[0].get_text().strip().replace('#', '')
                    if rank_val.isdigit():
                        live_ranks[team_name] = rank_val

        res_df = conn.read(worksheet="Results", ttl=0)
        if not res_df.empty:
            updated = False
            for idx, row in res_df.iterrows():
                sheet_name = str(row['Team']).strip().lower()
                if sheet_name in live_ranks:
                    res_df.at[idx, 'Rank'] = live_ranks[sheet_name]
                    updated = True
            
            if updated:
                conn.update(worksheet="Results", data=res_df)
    except:
        pass

# Execute Arbiter
run_silent_arbiter()

@st.cache_data(ttl=5)
def load_data():
    try:
        res = conn.read(worksheet="Results", ttl=0).dropna(how='all')
        sub = conn.read(worksheet="Submissions", ttl=0).dropna(how='all')
        return res, sub
    except:
        return pd.DataFrame(), pd.DataFrame()

results_df, subs_df = load_data()

# --- LOGO HELPER ---
def get_logo_"

# --- HEADER (Fixed aegis.png) ---
st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <img src="{GITHUB_BASE}aegis.png" width="80">
        <h1 style="margin-top: 10px; color: #1a1a1a; letter-spacing: -1px;">The International Predictions 2026</h1>
    </div>
""", unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs(["📊 LIVE STANDINGS", "🏆 LEADERBOARD", "🧬 PREDICTIONS", "📜 SCORING LOGIC"])

with tabs[0]:
    st.subheader("Official Tournament Standings")
    if not results_df.empty:
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
                    <span style="font-weight: bold; color: #57606a; width: 35px;">#{t_rank}</span>
                    <img src="{t_logo}" style="width: 28px; height: 28px; margin-right: 12px; object-fit: contain;">
                    <span style="font-weight: 600;">{t_name}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Awaiting tournament
