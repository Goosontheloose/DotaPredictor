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
def get_logo_url(name):
    return f"{GITHUB_BASE}{name.replace(' ', '%20')}.png"

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
        st.info("Awaiting tournament data.")

with tabs[1]:
    st.subheader("Leaderboard Standings")
    if not subs_df.empty and not results_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        raw_statuses = dict(zip(results_df['Team'], results_df.get('Status', ['Active']*len(results_df))))
        
        lb = []
        for _, row in clean_subs.iterrows():
            preds = str(row['Rankings']).split(',')
            f_score, p_score = 0, 0
            f_perfect, p_perfect = 0, 0
            for i, team in enumerate(preds):
                p_rank = i + 1
                t_name = team.strip()
                a_rank = int(float(actual_ranks.get(t_name, 0)))
                status_val = str(raw_statuses.get(t_name, 'Active')).strip().lower()
                if a_rank > 0:
                    m = 4 if p_rank==1 else 3 if p_rank==2 else 2 if p_rank in [3,4] else 1
                    penalty = abs(p_rank - a_rank) * m
                    bonus = -1 if p_rank == a_rank else 0
                    team_total = penalty + bonus
                    p_score += team_total
                    if p_rank == a_rank: p_perfect += 1
                    if status_val == 'completed':
                        f_score += team_total
                        if p_rank == a_rank: f_perfect += 1
            
            lb.append({
                "Oracle": row['Oracle Name'], 
                "Finalised Score": int(f_score),
                "Perfect (Finalised)": f_perfect,
                "Projected Score": int(p_score),
                "Perfect (Projected)": p_perfect
            })
        
        df_lb = pd.DataFrame(lb).sort_values(["Finalised Score", "Perfect (Finalised)", "Projected Score"])
        st.dataframe(df_lb, hide_index=True, use_container_width=True)

with tabs[2]:
    st.subheader("Predictions Matrix")
    if not subs_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_rows = []
        for _, row in clean_subs.iterrows():
            p = str(row['Rankings']).split(',')
            d = {"Oracle": row['Oracle Name']}
            for i, team in enumerate(p): d[f"#{i+1}"] = team
            m_rows.append(d)
        st.dataframe(pd.DataFrame(m_rows), hide_index=True, use_container_width=True)

with tabs[3]:
    st.subheader("Scoring Protocol")
    st.markdown("""
    ### ⛳ Golf Scoring Logic
    The goal is the **lowest penalty score**. The closer your prediction is to the actual result, the fewer points you receive.
    
    ### 🎯 Prophetic Deduction
    A perfect prediction (Bullseye) is rewarded with a point deduction. If your predicted rank matches the actual rank exactly:
    *   **Distance Penalty = 0**
    *   **Bonus Deduction = -1 point**
    
    ### 🔢 Penalty Multipliers
    Accuracy at the top of the bracket is critical. Penalties are weighted based on **your** predicted rank:
    * **1st Place Pick:** 4x Multiplier  
    * **2nd Place Pick:** 3x Multiplier  
    * **3rd - 4th Place Pick:** 2x Multiplier  
    * **5th - 16th Place Pick:** 1x Multiplier
    
    ### 🧪 The Calculation
    `(|Predicted Rank - Actual Rank| × Multiplier) + Bonus = Team Score`
    """)
