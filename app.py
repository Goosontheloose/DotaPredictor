import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="AEGIS ORACLE: SHANGHAI 2026", layout="wide")

# THE EXACT 16 TEAMS FROM YOUR LIST
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

# --- CLEAN LIGHT UI STYLING ---
st.markdown("""
    <style>
    /* Main Layout */
    .stApp { background-color: #fcfcfc; color: #1a1a1a; }
    
    /* Buttons */
    .stButton>button { 
        width: 100%; border-radius: 4px; height: 3.5em; 
        background-color: #2ea44f; color: white; font-weight: bold; border: none;
    }
    .stButton>button:hover { background-color: #2c974b; }

    /* Team Cards (Light Style) */
    .team-card { 
        display: flex; align-items: center; padding: 10px 15px; 
        background: #ffffff; border: 1px solid #d0d7de; border-radius: 6px; 
        margin-bottom: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .rank-badge {
        background: #f0f2f5; color: #57606a; font-weight: bold;
        padding: 3px 10px; border-radius: 4px; margin-right: 15px; 
        min-width: 40px; text-align: center; border: 1px solid #d0d7de;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; color: #57606a; }
    .stTabs [aria-selected="true"] { color: #0969da !important; }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["LOCK IN", "LEADERBOARD", "MATRIX", "PROTOCOL"])

# --- TAB 1: LOCK IN ---
with tab1:
    st.header("🔮 Prophecy Lock-In")
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("1. Rank the Teams")
        st.caption("Drag and drop to set your predicted finishing order.")
        
        # Interactive Sortable
        current_order = sort_items(TEAMS, direction="vertical", key="clean_ranker_v1")
        
        st.divider()
        oracle_name = st.text_input("Your Oracle Name", placeholder="Enter handle...")
        
        if st.button("LOCK IN PREDICTIONS"):
            if not oracle_name:
                st.error("Please provide a name to identify your prophecy.")
            else:
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": ", ".join(current_order)
                }])
                updated_df = pd.concat([subs_df, new_entry], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                st.success(f"Prophecy saved for {oracle_name}!")
                st.cache_data.clear()

    with col2:
        st.subheader("2. Final Review")
        for i, team in enumerate(current_order):
            st.markdown(f"""
                <div class="team-card">
                    <span class="rank-badge">#{i+1}</span>
                    <img src="{get_logo(team)}" width="28" style="margin-right:15px;" onerror="this.src='https://raw.githubusercontent.com/RubenFr87/DotaPredictor/main/Aegis.png'">
                    <span style="font-weight:600; color:#24292f;">{team}</span>
                </div>
            """, unsafe_allow_html=True)

# --- TAB 2: LEADERBOARD ---
with tab2:
    st.header("🏆 Live Standings")
    if subs_df.empty or "Oracle Name" not in subs_df.columns:
        st.info("No prophecies locked in yet.")
    else:
        latest_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        lb_rows = []
        for _, row in latest_subs.iterrows():
            preds = row["Rankings"].split(", ")
            penalty = 0
            perfects = 0
            if not res_df.empty and "Team" in res_df.columns:
                for rank, team in enumerate(preds, 1):
                    res_row = res_df[res_df["Team"] == team]
                    if not res_row.empty:
                        actual = int(res_row.iloc[0]["Rank"])
                        if actual > 0:
                            dist = abs(rank - actual)
                            mult = 4 if rank == 1 else (3 if rank == 2 else (2 if rank in [3, 4] else 1))
                            penalty += (dist * mult)
                            if dist == 0: perfects += 1
            lb_rows.append({"Oracle": row["Oracle Name"], "Penalty Score": penalty, "Perfect Picks": perfects})
        
        st.dataframe(pd.DataFrame(lb_rows).sort_values(["Penalty Score", "Perfect Picks"], ascending=[True, False]), use_container_width=True)

# --- TAB 3: MATRIX ---
with tab3:
    st.header("📊 Comparison Matrix")
    if not subs_df.empty:
        m_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_data = []
        for _, row in m_subs.iterrows():
            r = row["Rankings"].split(", ")
            e = {"Oracle": row["Oracle Name"]}
            for i, t in enumerate(r): e[f"#{i+1}"] = t
            m_data.append(e)
        st.dataframe(pd.DataFrame(m_data), use_container_width=True)

# --- TAB 4: PROTOCOL ---
with tab4:
    st.header("📜 Scoring Protocol")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        **Golf Scoring:** Lowest total points wins.
        - **Penalty = Distance x Multiplier**
        - **Rank #1:** 4x Penalty
        - **Rank #2:** 3x Penalty
        - **Rank #3-4:** 2x Penalty
        - **All others:** 1x Penalty
        """)
    with c2:
        st.markdown("""
        **Tie-Breakers:**
        1. Total number of 'Perfect Picks' (exact rank match).
        2. Lowest total penalty in the Top 4 prediction bracket.
        """)
