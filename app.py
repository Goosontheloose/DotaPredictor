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
        return pd.DataFrame(), pd.DataFrame()

subs_df, res_df = load_data()

# --- UI STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; font-weight: bold; }
    .team-card { 
        display: flex; align-items: center; padding: 10px; 
        background: white; border: 1px solid #eee; border-radius: 8px; margin-bottom: 5px;
    }
    .rank-badge {
        background: #00F5FF; color: black; font-weight: bold;
        padding: 2px 8px; border-radius: 4px; margin-right: 15px; min-width: 35px; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["LOCK IN", "LEADERBOARD", "MATRIX", "PROTOCOL"])

# --- TAB 1: LOCK IN ---
with tab1:
    st.title("🔮 THE SHANGHAI PROPHECY")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Arrange Your Ranks")
        st.caption("Drag and drop teams from 1st (Top) to 16th (Bottom).")
        sorted_list = sort_items(TEAMS, direction="vertical", key="prophecy_ranker_final_v5")
        
        oracle_name = st.text_input("Oracle Name", placeholder="Enter your handle...")
        
        if st.button("LOCK IN PROPHECY"):
            if not oracle_name:
                st.error("Please enter an Oracle Name.")
            else:
                new_data = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": ", ".join(sorted_list)
                }])
                updated_df = pd.concat([subs_df, new_data], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                st.success(f"Prophecy Recorded, {oracle_name}!")
                st.cache_data.clear()

    with col2:
        st.subheader("2. Prophecy Preview")
        for i, team in enumerate(sorted_list):
            st.markdown(f"""
                <div class="team-card">
                    <span class="rank-badge">#{i+1}</span>
                    <img src="{get_logo(team)}" width="30" style="margin-right:15px;" onerror="this.src='https://raw.githubusercontent.com/RubenFr87/DotaPredictor/main/Aegis.png'">
                    <span style="font-weight:600; color:#1f2937;">{team}</span>
                </div>
            """, unsafe_allow_html=True)

# --- TAB 2: LEADERBOARD ---
with tab2:
    st.header("🏆 ORACLE STANDINGS")
    if subs_df.empty or "Oracle Name" not in subs_df.columns:
        st.info("The Vault is empty.")
    else:
        latest_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        leaderboard = []
        for _, row in latest_subs.iterrows():
            pred_list = row["Rankings"].split(", ")
            total_penalty = 0
            perfect_picks = 0
            if not res_df.empty and "Team" in res_df.columns:
                for rank, team in enumerate(pred_list, 1):
                    off_row = res_df[res_df["Team"] == team]
                    if not off_row.empty:
                        off_rank = int(off_row.iloc[0]["Rank"])
                        if off_rank > 0:
                            dist = abs(rank - off_rank)
                            mult = 4 if rank == 1 else (3 if rank == 2 else (2 if rank in [3, 4] else 1))
                            total_penalty += (dist * mult)
                            if dist == 0: perfect_picks += 1
            leaderboard.append({"Oracle": row["Oracle Name"], "Penalty Score": total_penalty, "Perfect Picks": perfect_picks})
        
        st.table(pd.DataFrame(leaderboard).sort_values(["Penalty Score", "Perfect Picks"], ascending=[True, False]))

# --- TAB 3: MATRIX ---
with tab3:
    st.header("📊 PREDICTION MATRIX")
    if not subs_df.empty:
        matrix_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        matrix_rows = []
        for _, row in matrix_subs.iterrows():
            ranks = row["Rankings"].split(", ")
            entry = {"Oracle": row["Oracle Name"]}
            for i, t in enumerate(ranks): entry[f"#{i+1}"] = t
            matrix_rows.append(entry)
        st.dataframe(pd.DataFrame(matrix_rows))

# --- TAB 4: PROTOCOL ---
with tab4:
    st.header("📜 THE ORACLE PROTOCOL")
    st.markdown("""
    **The Penalty:** `ABS(Predicted - Actual) x Multiplier`
    - **1st:** 4x | **2nd:** 3x | **3rd/4th:** 2x | **Others:** 1x
    - **Tie-Breaker:** Most Perfect Picks wins.
    """)
