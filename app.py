import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- CONFIGURATION (LOCKED) ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"
GITHUB_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/"
LIQUIPEDIA_URL = "https://liquipedia.net/dota2/The_International/2026/Group_Stage"

st.set_page_config(page_title="TI 2026", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- THE SILENT ARBITER (AUTOMATED SYNC) ---
def run_silent_arbiter():
    try:
        # 1. Check if we should sync (30 min throttle)
        meta = conn.read(worksheet="Metadata", ttl=0)
        last_update = datetime.strptime(meta.iloc[0, 0], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < last_update + timedelta(minutes=30):
            return # Skip sync
    except:
        pass # If Metadata fails, attempt one sync anyway

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(LIQUIPEDIA_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Scrape ranks from standard Liquipedia 'grouptable'
        live_ranks = {}
        tables = soup.find_all('table', class_='grouptable')
        for table in tables:
            rows = table.find_all('tr')[1:] # Skip header
            for row in rows:
                r_cell = row.find('td', class_='grouptable-rank')
                t_cell = row.find('span', class_='team-template-text')
                if r_cell and t_cell:
                    live_ranks[t_cell.text.strip()] = r_cell.text.strip()

        # 2. Update the Results Sheet
        res_df = conn.read(worksheet="Results", ttl=0)
        if not res_df.empty:
            updated = False
            for idx, row in res_df.iterrows():
                team_name = str(row['Team']).strip()
                if team_name in live_ranks:
                    res_df.at[idx, 'Rank'] = live_ranks[team_name]
                    updated = True
            
            if updated:
                conn.update(worksheet="Results", data=res_df)
                # Update the Timestamp in Metadata
                new_ts = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M:%S")]], columns=["LastUpdate"])
                conn.update(worksheet="Metadata", data=new_ts)
    except:
        pass # Fail silently to keep app running

# Execute the Arbiter
run_silent_arbiter()

@st.cache_data(ttl=10)
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
        <h1 style="margin-top: 10px; color: #1a1a1a; letter-spacing: -1px;">The International Predictions 2026</h1>
    </div>
""", unsafe_allow_html=True)

# TAB LAYOUT
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
            card_text = "#991b1b" if t_status == "completed" else "#24292f"
            st.markdown(f"""
                <div style="display: flex; align-items: center; background: {card_bg}; 
                            margin-bottom: 8px; padding: 12px; border-radius: 8px; 
                            border: 1px solid {card_border}; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <span style="font-weight: bold; color: #57606a; width: 35px; font-family: monospace; font-size: 14px;">#{t_rank}</span>
                    <img src="{t_logo}" style="width: 28px; height: 28px; margin-right: 12px; object-fit: contain;">
                    <span style="font-weight: 600; color: {card_text}; font-size: 16px;">{t_name}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Awaiting tournament data.")

with tabs[1](https://liquipedia.net/commons/Module:GroupTableLeague/next/downstream/doc "inline-citation"):
    st.subheader("Leaderboard Standings")
    if not subs_df.empty and not results_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        raw_statuses = dict(zip(results_df['Team'], results_df.get('Status', ['Active']*len(results_df))))
        
        lb = []
        for _, row in clean_subs.iterrows():
            preds = row['Rankings'].split(',')
            f_score, p_score = 0, 0
            f_perfect, p_perfect = 0, 0
            
            for i, team in enumerate(preds):
                p_rank = i + 1
                a_rank = int(actual_ranks.get(team.strip(), 0))
                status_val = str(raw_statuses.get(team.strip(), 'Active')).strip().lower()
                
                if a_rank > 0:
                    m = 4 if p_rank==1 else 3 if p_rank==2 else 2 if p_rank in [3](https://liquipedia.net/sideswipe/Template:GroupTableLeague "inline-citation")[4](https://liquipedia.net/counterstrike/Module:SwissTableLeague "inline-citation") else 1
                    penalty = abs(p_rank - a_rank) * m
                    
                    # PROPHETIC DEDUCTION
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
        
        df_lb = pd.DataFrame(lb).sort_values(
            ["Finalised Score", "Perfect (Finalised)", "Projected Score"], 
            ascending=[True, False, True]
        )
        st.dataframe(df_lb, hide_index=True, use_container_width=True)

with tabs[2](https://liquipedia.net/commons/Module:GroupTableLeague "inline-citation"):
    st.subheader("Predictions")
    if not subs_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_rows = []
        for _, row in clean_subs.iterrows():
            p = str(row['Rankings']).split(',')
            d = {"Oracle": row['Oracle Name']}
            for i, team in enumerate(p): d[f"#{i+1}"] = team
            m_rows.append(d)
        st.dataframe(pd.DataFrame(m_rows), hide_index=True, use_container_width=True)

with tabs[3](https://liquipedia.net/sideswipe/Template:GroupTableLeague "inline-citation"):
    st.subheader("The Rules (Scoring)")
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
