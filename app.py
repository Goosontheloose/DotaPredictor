import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="AEGIS ORACLE: SHANGHAI 2026", layout="wide")

# THE EXACT 16 TEAMS
TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

GITHUB_BASE = "https://raw.githubusercontent.com/RubenFr87/DotaPredictor/main/"

def get_logo(team_name):
    return f"{GITHUB_BASE}{team_name.replace(' ', '%20')}.png"

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data():
    try:
        subs = conn.read(worksheet="Submissions", ttl=0)
        res = conn.read(worksheet="Results", ttl=0)
        return subs, res
    except:
        return pd.DataFrame(columns=["Timestamp", "Oracle Name", "Rankings"]), pd.DataFrame(columns=["Team", "Rank"])

subs_df, res_df = load_data()

# --- STYLING ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #fcfcfc; }}
    .main-header {{ text-align: center; padding: 10px; }}
    .stButton>button {{ 
        width: 100%; border-radius: 4px; height: 3.5em; 
        background-color: #2ea44f; color: white; font-weight: bold; border: none;
    }}
    .protocol-card {{
        background: white; padding: 20px; border-radius: 8px; 
        border: 1px solid #d0d7de; margin-bottom: 20px;
    }}
    </style>
    <div class="main-header">
        <img src="{GITHUB_BASE}Aegis.png" width="70">
        <h1 style="margin-top: 5px; color: #1a1a1a;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["LOCK IN", "LEADERBOARD", "MATRIX", "PROTOCOL"])

# --- TAB 1: LOCK IN ---
with tab1:
    st.caption("Step 1: Drag the teams below. Step 2: Enter your name. Step 3: Lock In.")
    
    # We use a tight 3-column layout to make it feel like ONE list
    # Col 1: Logos (Preview), Col 2: The interactive ranker, Col 3: Spacer
    col_pre, col_rank, col_spacer = st.columns([0.8, 1.2, 1], gap="small")
    
    with col_rank:
        st.subheader("Ranker")
        # The standard tool: Reliable, never returns None
        user_order = sort_items(TEAMS, direction="vertical", key="v10_final")
        
        st.divider()
        oracle_name = st.text_input("Oracle Name", placeholder="Enter your name...")
        
        if st.button("LOCK IN PROPHECY"):
            if not oracle_name:
                st.error("Name is required.")
            else:
                # Direct string join from the user_order list
                rankings_str = ", ".join(user_order)
                
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": rankings_str
                }])
                
                updated_subs = pd.concat([subs_df, new_entry], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_subs)
                
                st.success(f"Prophecy recorded for {oracle_name}!")
                st.cache_data.clear()

    with col_pre:
        st.subheader("Prophecy Preview")
        for i, team in enumerate(user_order):
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 12px; height: 42px;">
                    <span style="min-width: 35px; font-weight: bold; color: #57606a;">#{i+1}</span>
                    <img src="{get_logo(team)}" width="28" style="margin-right: 10px;" onerror="this.src='{GITHUB_BASE}Aegis.png'">
                    <span style="font-size: 15px; font-weight: 500;">{team}</span>
                </div>
            """, unsafe_allow_html=True)

# --- TAB 2: LEADERBOARD ---
with tab2:
    st.header("🏆 Leaderboard")
    if not subs_df.empty:
        latest = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        lb = []
        for _, row in latest.iterrows():
            p_list = row["Rankings"].split(", ")
            score, hits = 0, 0
            if not res_df.empty:
                for r, t in enumerate(p_list, 1):
                    match = res_df[res_df["Team"] == t]
                    if not match.empty:
                        act = int(match.iloc[0]["Rank"])
                        if act > 0:
                            dist = abs(r - act)
                            m = 4 if r==1 else (3 if r==2 else (2 if r in [3,4] else 1))
                            score += (dist * m)
                            if dist == 0: hits += 1
            lb.append({"Oracle": row["Oracle Name"], "Score": score, "Bullseyes": hits})
        st.dataframe(pd.DataFrame(lb).sort_values(["Score", "Bullseyes"], ascending=[True, False]), use_container_width=True)

# --- TAB 3: MATRIX ---
with tab3:
    st.header("📊 Comparison Matrix")
    if not subs_df.empty:
        m_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_rows = []
        for _, row in m_subs.iterrows():
            r = row["Rankings"].split(", ")
            entry = {"Oracle": row["Oracle Name"]}
            for i, t in enumerate(r): entry[f"#{i+1}"] = t
            m_rows.append(entry)
        st.dataframe(pd.DataFrame(m_rows), use_container_width=True)

# --- TAB 4: PROTOCOL ---
with tab4:
    st.header("📜 Scoring Protocol")
    st.markdown("""
    <div class="protocol-card">
        <h3>1. High-Stakes Multipliers</h3>
        <p>Your distance penalty is multiplied based on how high you ranked the team:</p>
        <ul>
            <li><b>Predicted 1st:</b> 4x Penalty</li>
            <li><b>Predicted 2nd:</b> 3x Penalty</li>
            <li><b>Predicted 3rd-4th:</b> 2x Penalty</li>
            <li><b>Predicted 5th-16th:</b> 1x Penalty</li>
        </ul>
    </div>
    <div class="protocol-card">
        <h3>2. Fixed vs. Projected</h3>
        <p><b>Fixed Scores:</b> Finalized when a team is officially eliminated.</p>
        <p><b>Projected Scores:</b> Calculates the minimum possible penalty while a team is still active in the bracket.</p>
    </div>
    <div class="protocol-card">
        <h3>3. Tie-Breaker Rules</h3>
        <ol>
            <li><b>Bullseyes:</b> Most exact rank matches.</li>
            <li><b>Top-Heavy Accuracy:</b> Lowest penalty count within the Top 4 predictions.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
