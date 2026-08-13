import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"
GITHUB_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/"

st.set_page_config(page_title="TI 2026", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data():
    try:
        # Pulling live data from your manual entries in Google Sheets
        res = conn.read(worksheet="Results", ttl=0).dropna(how='all')
        sub = conn.read(worksheet="Submissions", ttl=0).dropna(how='all')
        return res, sub
    except:
        return pd.DataFrame(), pd.DataFrame()

results_df, subs_df = load_data()

# --- LOGO HELPER ---
def get_logo_url(name):
    # Standardizing name for URL compatibility
    return f"{GITHUB_BASE}{name.replace(' ', '%20')}.png"

# --- HEADER ---
st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <img src="{GITHUB_BASE}aegis.png" width="80">
        <h1 style="margin-top: 10px; color: #1a1a1a; letter-spacing: -1px;">The International Predictions 2026</h1>
    </div>
""", unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs(["📊 LIVE STANDINGS", "🏆 LEADERBOARD", "🧬 PREDICTIONS", "📜 SCORING LOGIC"])

with tabs[0]:
    st.subheader("Tournament Standings")
    st.info("Rankings are updated manually by the Grand Arbiter.")
    if not results_df.empty:
        # Convert Rank to numeric to ensure correct sorting
        results_df['Rank'] = pd.to_numeric(results_df['Rank'], errors='coerce').fillna(0)
        # Sort so Rank 1 is at the top; 0 (unranked) goes to bottom
        sorted_results = results_df.sort_values("Rank", ascending=True)
        
        for _, row in sorted_results.iterrows():
            t_name = str(row['Team'])
            t_rank = int(row['Rank'])
            
            # Skip teams that haven't been assigned a rank yet if you prefer
            if t_rank == 0: continue 

            t_status = str(row.get('Status', 'Active')).strip().lower()
            t_logo = get_logo_url(t_name)
            
            # Visual feedback for eliminated/completed teams
            card_bg = "#fee2e2" if t_status == "completed" else "#ffffff"
            card_border = "#ef4444" if t_status == "completed" else "#eee"
            
            st.markdown(f"""
                <div style="display: flex; align-items: center; background: {card_bg}; 
                            margin-bottom: 8px; padding: 12px; border-radius: 8px; 
                            border: 1px solid {card_border}; shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <span style="font-weight: bold; color: #57606a; width: 35px; font-size: 1.1em;">#{t_rank}</span>
                    <img src="{t_logo}" style="width: 32px; height: 32px; margin-right: 15px; object-fit: contain;">
                    <span style="font-weight: 600; font-size: 1.1em; color: #1a1a1a;">{t_name}</span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("Waiting for the Grand Arbiter to enter results in the Google Sheet.")

with tabs[1]:
    st.subheader("Leaderboard Standings")
    if not subs_df.empty and not results_df.empty:
        # Deduplicate to show only the latest prophecy per user
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
                    # Apply Multipliers: 1st=4x, 2nd=3x, 3-4th=2x, rest=1x
                    m = 4 if p_rank == 1 else 3 if p_rank == 2 else 2 if p_rank in [3, 4] else 1
                    penalty = abs(p_rank - a_rank) * m
                    # Prophetic Deduction: -1 for exact match
                    bonus = -1 if p_rank == a_rank else 0
                    team_total = penalty + bonus
                    
                    p_score += team_total
                    if p_rank == a_rank: p_perfect += 1
                    
                    # Finalised Score only counts teams marked as 'completed'
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
        
        # Sort by Finalised Score (Asc), then Perfect Picks (Desc)
        df_lb = pd.DataFrame(lb).sort_values(["Finalised Score", "Perfect (Finalised)", "Projected Score"], ascending=[True, False, True])
        st.dataframe(df_lb, hide_index=True, use_container_width=True)

with tabs[2]:
    st.subheader("Predictions Matrix")
    if not subs_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_rows = []
        for _, row in clean_subs.iterrows():
            p = str(row['Rankings']).split(',')
            d = {"Oracle": row['Oracle Name']}
            for i, team in enumerate(p):
                d[f"#{i+1}"] = team.strip()
            m_rows.append(d)
        st.dataframe(pd.DataFrame(m_rows), hide_index=True, use_container_width=True)

with tabs[3]:
    st.subheader("Scoring Protocol")
    st.markdown("""
    ### How to read the scores:
    *   **Finalised Score:** Penalty points calculated only for teams whose tournament run is **Completed**.
    *   **Projected Score:** Penalty points calculated against the **Current Standings** (includes active teams).
    *   **The Goal:** Lowest score wins.

    ### The Math:
    1.  **Distance Penalty:** `ABS(Predicted Rank - Actual Rank)`
    2.  **Weight Multiplier:**
        *   Predicted 1st: **4x**
        *   Predicted 2nd: **3x**
        *   Predicted 3rd-4th: **2x**
        *   All others: **1x**
    3.  **Prophetic Deduction:** **-1 point** is deducted from your total score for every team you place in their exact final rank.
    """)
