import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="AEGIS ORACLE: SHANGHAI 2026", layout="centered")

# THE EXACT 16 TEAMS
TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

GITHUB_BASE = "https://raw.githubusercontent.com/RubenFr87/DotaPredictor/main/"

def get_logo(team_name):
    # Precise pathing for your GitHub repo
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

# --- CLEAN UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .stButton>button { 
        width: 100%; border-radius: 4px; height: 3.5em; 
        background-color: #2ea44f; color: white; font-weight: bold; border: none;
    }
    .protocol-card {
        background: white; padding: 20px; border-radius: 8px; 
        border: 1px solid #d0d7de; margin-bottom: 20px;
    }
    /* Draggable Item Styling */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div[style*="border: 1px solid"] {
        background: white !important;
        border: 1px solid #d0d7de !important;
        border-radius: 8px !important;
        padding: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["LOCK IN", "LEADERBOARD", "MATRIX", "PROTOCOL"])

# --- TAB 1: LOCK IN ---
with tab1:
    st.header("🔮 Prophecy Lock-In")
    st.caption("Drag and drop to set your prediction. Ranks are assigned 1 to 16 from top to bottom.")
    
    # We use a custom formatted list to include logos in the sortable interface
    # Streamlit-sortables can't render HTML, so we show the name and preview logos below
    
    col_main, col_spacer = st.columns([2, 1])
    
    with col_main:
        user_order = sort_items(TEAMS, direction="vertical", key="v9_final_stable")
        
        st.divider()
        oracle_name = st.text_input("Oracle Name", placeholder="e.g. Frederik")
        
        if st.button("LOCK IN PROPHECY"):
            if not oracle_name:
                st.error("Please enter your name.")
            elif not user_order:
                st.error("Error capturing team order. Please refresh and try again.")
            else:
                # Format the data for the sheet
                new_row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": ", ".join(user_order)
                }])
                
                # Append and Update
                updated_subs = pd.concat([subs_df, new_row], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_subs)
                
                st.success(f"Prophecy locked for {oracle_name}!")
                st.cache_data.clear()

    # The Visual Preview (The Logos you wanted)
    with col_spacer:
        st.subheader("Live Preview")
        for i, team in enumerate(user_order):
            st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="min-width: 30px; font-weight: bold; color: #57606a;">#{i+1}</span>
                    <img src="{get_logo(team)}" width="24" style="margin-right: 10px;" onerror="this.src='{GITHUB_BASE}Aegis.png'">
                    <span style="font-size: 14px;">{team}</span>
                </div>
            """, unsafe_allow_html=True)

# --- TAB 2: LEADERBOARD ---
with tab2:
    st.header("🏆 Leaderboard")
    if subs_df.empty or "Oracle Name" not in subs_df.columns:
        st.info("No submissions yet.")
    else:
        # Scoring Logic
        latest = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        lb_data = []
        for _, row in latest.iterrows():
            preds = row["Rankings"].split(", ")
            penalty, perfects = 0, 0
            if not res_df.empty:
                for rank, team in enumerate(preds, 1):
                    match = res_df[res_df["Team"] == team]
                    if not match.empty:
                        actual = int(match.iloc[0]["Rank"])
                        if actual > 0:
                            dist = abs(rank - actual)
                            m = 4 if rank == 1 else (3 if rank == 2 else (2 if rank in [3,4] else 1))
                            penalty += (dist * m)
                            if dist == 0: perfects += 1
            lb_data.append({"Oracle": row["Oracle Name"], "Score": penalty, "Bullseyes": perfects})
        
        st.dataframe(pd.DataFrame(lb_data).sort_values(["Score", "Bullseyes"], ascending=[True, False]), use_container_width=True)

# --- TAB 3: MATRIX ---
with tab3:
    st.header("📊 Matrix")
    if not subs_df.empty:
        m_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_list = []
        for _, row in m_subs.iterrows():
            r = row["Rankings"].split(", ")
            e = {"Oracle": row["Oracle Name"]}
            for i, t in enumerate(r): e[f"#{i+1}"] = t
            m_list.append(e)
        st.dataframe(pd.DataFrame(m_list), use_container_width=True)

# --- TAB 4: PROTOCOL ---
with tab4:
    st.header("📜 Scoring Protocol")
    st.markdown("""
    <div class="protocol-card">
        <h3>1. The Multiplier Tiers</h3>
        <ul>
            <li><b>1st Place Prediction:</b> 4x Multiplier (High Stakes)</li>
            <li><b>2nd Place Prediction:</b> 3x Multiplier</li>
            <li><b>3rd - 4th Place Prediction:</b> 2x Multiplier</li>
            <li><b>5th - 16th Place Prediction:</b> 1x Multiplier</li>
        </ul>
    </div>
    <div class="protocol-card">
        <h3>2. Fixed vs. Projected</h3>
        <p><b>Fixed:</b> Final rank for eliminated teams.</p>
        <p><b>Projected:</b> Minimum possible penalty for active teams.</p>
    </div>
    <div class="protocol-card">
        <h3>3. Tie-Breakers</h3>
        <p>1. Most 'Bullseyes' (Exact rank matches).</p>
        <p>2. Lowest penalty in the Top 4 prediction bracket.</p>
    </div>
    """, unsafe_allow_html=True)
