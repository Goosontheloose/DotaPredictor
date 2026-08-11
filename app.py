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

# --- HEADER ---
st.markdown(f"""
    <div style="text-align: center; padding-bottom: 20px;">
        <img src="{GITHUB_BASE}Aegis.png" width="80">
        <h1 style="margin-top: 10px; color: #1a1a1a;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["LOCK IN", "LEADERBOARD", "MATRIX", "PROTOCOL"])

# --- TAB 1: LOCK IN (The logic that works) ---
with tab1:
    st.markdown("### 🔮 Forge Your Prophecy")
    
    # 2-Column Layout: Left for the Draggable Names, Right for the Logos
    col_rank, col_preview = st.columns([1, 1])
    
    with col_rank:
        st.subheader("1. Reorder Names")
        # This component is reliable and will NOT cause a TypeError
        user_order = sort_items(TEAMS, direction="vertical", key="stable_ranker_v1")
        
        st.divider()
        oracle_name = st.text_input("Oracle Name", placeholder="e.g. Frederik")
        
        if st.button("LOCK IN PROPHECY"):
            if not oracle_name:
                st.error("Please enter a name to secure your prophecy.")
            else:
                # This direct join is safe because user_order is a standard list
                rank_string = ", ".join(user_order)
                
                new_data = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": rank_string
                }])
                
                updated_df = pd.concat([subs_df, new_data], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                
                st.success(f"Prophecy recorded for {oracle_name}!")
                st.cache_data.clear()

    with col_preview:
        st.subheader("2. Live Preview")
        for i, team in enumerate(user_order):
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 10px; padding: 5px; border-bottom: 1px solid #eee;">
                    <span style="width: 35px; font-weight: bold; color: #666;">#{i+1}</span>
                    <img src="{get_logo(team)}" width="28" style="margin-right: 15px;" onerror="this.src='{GITHUB_BASE}Aegis.png'">
                    <span style="font-weight: 500;">{team}</span>
                </div>
            """, unsafe_allow_html=True)

# --- TAB 2: LEADERBOARD ---
with tab2:
    st.header("🏆 Leaderboard")
    if not subs_df.empty:
        latest = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        lb = []
        for _, row in latest.iterrows():
            preds = row["Rankings"].split(", ")
            score, hits = 0, 0
            if not res_df.empty:
                for rank, team in enumerate(preds, 1):
                    match = res_df[res_df["Team"] == team]
                    if not match.empty:
                        actual = int(match.iloc[0]["Rank"])
                        if actual > 0:
                            dist = abs(rank - actual)
                            m = 4 if rank==1 else (3 if rank==2 else (2 if rank in [3,4] else 1))
                            score += (dist * m)
                            if dist == 0: hits += 1
            lb.append({"Oracle": row["Oracle Name"], "Penalty": score, "Bullseyes": hits})
        st.table(pd.DataFrame(lb).sort_values(["Penalty", "Bullseyes"], ascending=[True, False]))

# --- TAB 3: MATRIX ---
with tab3:
    st.header("📊 Matrix")
    if not subs_df.empty:
        m_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_rows = []
        for _, row in m_subs.iterrows():
            r = row["Rankings"].split(", ")
            entry = {"Oracle": row["Oracle Name"]}
            for i, t in enumerate(r): entry[f"#{i+1}"] = t
            m_rows.append(entry)
        st.dataframe(pd.DataFrame(m_rows))

# --- TAB 4: PROTOCOL ---
with tab4:
    st.header("📜 Scoring Protocol")
    st.markdown("""
    ### 1. High-Stakes Multipliers
    Penalty points (distance from actual rank) are multiplied based on your prediction:
    - **Rank #1:** 4x Multiplier
    - **Rank #2:** 3x Multiplier
    - **Rank #3-4:** 2x Multiplier
    - **Rank #5-16:** 1x Multiplier (Base)
    
    ### 2. Fixed vs. Projected
    - **Fixed:** The team has been eliminated and their rank is final.
    - **Projected:** While a team is still playing, we calculate the minimum possible penalty they can receive.
    
    ### 3. Tie-Breakers
    1. **Bullseyes:** Total number of exact rank matches.
    2. **Top Tier Accuracy:** Lowest penalty within your predicted Top 4.
    """)
