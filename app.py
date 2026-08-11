import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items
from datetime import datetime

# --- CONFIGURATION ---
GITHUB_BASE = "https://raw.githubusercontent.com/Goosontheloose/DotaPredictor/main/"

TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

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

# --- HEADER ---
st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <img src="{GITHUB_BASE}Aegis.png" width="80">
        <h1 style="margin-top: 10px; color: #1a1a1a; letter-spacing: -1px;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔮 LOCK-IN", "🏆 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

with tabs[0]:
    st.markdown("### 1. Arrange Your Prophecy")
    st.caption("Drag the names to set your order. The visual preview below updates live.")
    
    # This is the functional part that writes to the sheet
    current_order = sort_items(TEAMS, direction="vertical", key="oracle_ranker_v1")
    
    st.divider()
    
    st.markdown("### 2. Visual Prophecy Preview")
    # This shows the logos in the order you just picked
    for i, team in enumerate(current_order):
        logo_url = f"{GITHUB_BASE}{team.replace(' ', '%20')}.png"
        st.markdown(f"""
            <div style="display: flex; align-items: center; background: white; margin-bottom: 5px; padding: 8px 15px; border-radius: 8px; border: 1px solid #eee;">
                <span style="font-weight: bold; color: #57606a; width: 30px;">#{i+1}</span>
                <img src="{logo_url}" onerror="this.src='{GITHUB_BASE}Aegis.png'" style="width: 24px; height: 24px; margin-right: 12px; object-fit: contain;">
                <span style="font-weight: 600; color: #24292f;">{team}</span>
            </div>
        """, unsafe_allow_html=True)

    st.divider()
    oracle_name = st.text_input("Oracle Name", placeholder="Who are you?")
    
    if st.button("LOCK IN PROPHECY", type="primary", use_container_width=True):
        if not oracle_name:
            st.error("Identification required.")
        else:
            try:
                # current_order is a standard list of strings, so .join() will work perfectly
                rank_string = ",".join(current_order)
                
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": oracle_name,
                    "Rankings": rank_string
                }])
                
                updated_df = pd.concat([subs_df, new_entry], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                
                st.success(f"Prophecy locked for {oracle_name}!")
                st.balloons()
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Write failed: {e}")

with tabs[1]:
    st.subheader("Leaderboard Standings")
    if not subs_df.empty and not results_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        lb = []
        for _, row in clean_subs.iterrows():
            preds = row['Rankings'].split(',')
            score, perf = 0, 0
            for i, team in enumerate(preds):
                p_rank = i + 1
                a_rank = int(actual_ranks.get(team, 0))
                if a_rank > 0:
                    m = 4 if p_rank==1 else 3 if p_rank==2 else 2 if p_rank in [3,4] else 1
                    score += abs(p_rank - a_rank) * m
                    if p_rank == a_rank: perf += 1
            lb.append({"Oracle": row['Oracle Name'], "Penalty Score": int(score), "Perfect Picks": perf})
        st.table(pd.DataFrame(lb).sort_values(["Penalty Score", "Perfect Picks"], ascending=[True, False]))
    else:
        st.info("Awaiting tournament results in the Google Sheet.")

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
        st.dataframe(pd.DataFrame(m_rows), hide_index=True)

with tabs[3]:
    st.subheader("The Oracle Protocol")
    st.markdown("""
    **Multiplier System:**
    * **1st Place:** 4x Penalty
    * **2nd Place:** 3x Penalty
    * **3rd-4th Place:** 2x Penalty
    * **Other:** 1x Penalty
    
    **Scoring:** Lowest Penalty Score wins. Tie-breaks decided by **Perfect Picks**.
    """)
