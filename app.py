import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import json

# --- CONFIGURATION (LOCKED) ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"
GITHUB_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/"

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

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
        <h1 style="margin-top: 10px; color: #1a1a1a; letter-spacing: -1px;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

# UPDATED TAB LAYOUT (LOCK-IN REMOVED)
tabs = st.tabs(["📊 LIVE STANDINGS", "🏆 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

with tabs[0]:
    st.subheader("Official Tournament Standings")
    if not results_df.empty:
        # Sort results by the Rank column you manage in the sheet
        sorted_results = results_df.sort_values("Rank")
        
        for _, row in sorted_results.iterrows():
            t_name = str(row['Team'])
            t_rank = int(row['Rank'])
            t_status = str(row.get('Status', 'Active')).strip().lower()
            t_logo = get_logo_url(t_name)
            
            # Formatting for Completed (Red) vs Active (White)
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
        st.info("Awaiting manual ranking data from the Arbiter in the 'Results' sheet.")

with tabs[1]:
    st.subheader("Leaderboard Standings")
    if not subs_df.empty and not results_df.empty:
        # Deduplicate submissions to show only the latest per person
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        raw_statuses = dict(zip(results_df['Team'], results_df.get('Status', ['Active']*len(results_df))))
        
        lb = []
        for _, row in clean_subs.iterrows():
            preds = row['Rankings'].split(',')
            f_score, p_score, perfect = 0, 0, 0
            for i, team in enumerate(preds):
                p_rank = i + 1
                a_rank = int(actual_ranks.get(team, 0))
                status_val = str(raw_statuses.get(team, 'Active')).strip().lower()
                
                if a_rank > 0:
                    # Multipliers based on prediction rank
                    m = 4 if p_rank==1 else 3 if p_rank==2 else 2 if p_rank in [3,4] else 1
                    penalty = abs(p_rank - a_rank) * m
                    
                    p_score += penalty
                    if status_val == 'completed':
                        f_score += penalty
                    if p_rank == a_rank:
                        perfect += 1
            
            lb.append({
                "Oracle": row['Oracle Name'], 
                "Finalised Score": int(f_score), 
                "Projected Score": int(p_score), 
                "Perfect Picks": perfect
            })
        
        df_lb = pd.DataFrame(lb).sort_values(["Projected Score", "Perfect Picks"], ascending=[True, False])
        st.dataframe(df_lb, hide_index=True, use_container_width=True)
    else:
        st.info("Awaiting tournament results and user submissions.")

with tabs[2]:
    st.subheader("Prediction Matrix")
    if not subs_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_rows = []
        for _, row in clean_subs.iterrows():
            p = row['Rankings'].split(',')
            d = {"Oracle": row['Oracle Name']}
            for i, team in enumerate(p): d[f"#{i+1}"] = team
            m_rows.append(d)
        st.dataframe(pd.DataFrame(m_rows), hide_index=True, use_container_width=True)

with tabs[3]:
    st.subheader("The Oracle Protocol")
    st.markdown("""
    ### ⛳ Golf Scoring Logic
    The goal is the **lowest penalty score**. The closer your prediction is to the actual result, the fewer points you receive.
    
    ### 🔢 Penalty Multipliers
    Accuracy at the top of the bracket is worth more. Penalties are multiplied based on where **you** predicted the team would finish:
    * **1st Place Pick:** 4x Penalty  
    * **2nd Place Pick:** 3x Penalty  
    * **3rd - 4th Place Pick:** 2x Penalty  
    * **5th - 16th Place Pick:** 1x Penalty
    
    ### 🧪 The Formula
    `|Predicted Rank - Actual Rank| × Multiplier = Penalty`
    
    ### 📊 Score Types
    * **Finalised Score:** Points from teams marked as **'Completed'** in the tournament results.
    * **Projected Score:** Your current total score including all teams currently **'Active'**.
    """)
