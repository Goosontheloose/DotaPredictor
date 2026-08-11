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

# --- SHANGHAI SHADOW-TECH UI STYLING ---
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        color: #c9d1d9;
    }}
    [data-testid="stHeader"] {{ background: rgba(0,0,0,0); }}
    
    /* Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 24px;
        background-color: transparent;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        background-color: transparent !important;
        border: none !important;
        color: #8b949e !important;
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        color: #00F5FF !important;
        border-bottom: 2px solid #00F5FF !important;
    }}

    /* Team Cards */
    .team-card {{ 
        display: flex; align-items: center; padding: 12px 16px; 
        background: rgba(255, 255, 255, 0.05); 
        border: 1px solid rgba(0, 245, 255, 0.1); 
        border-radius: 12px; margin-bottom: 8px;
        transition: transform 0.2s ease;
    }}
    .team-card:hover {{ border: 1px solid #00F5FF; transform: translateX(5px); }}
    
    .rank-badge {{
        background: linear-gradient(90deg, #00F5FF, #00D1FF);
        color: #0d1117; font-weight: 800;
        padding: 4px 10px; border-radius: 6px; margin-right: 20px; 
        min-width: 45px; text-align: center; font-family: monospace;
    }}
    
    .stButton>button {{
        background: linear-gradient(90deg, #FF4B4B, #D10000);
        color: white; border: none; font-weight: 800; border-radius: 8px;
        height: 3.5em; text-transform: uppercase; letter-spacing: 1px;
    }}
    </style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["LOCK IN", "LEADERBOARD", "MATRIX", "PROTOCOL"])

# --- TAB 1: LOCK IN ---
with tab1:
    st.markdown("<h1 style='text-align: center; color: #00F5FF; letter-spacing: 2px;'>🔮 SHANGHAI ORACLE PROTOCOL</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### <span style='color:#00F5FF'>01</span> REORDER BRACKET", unsafe_allow_html=True)
        st.caption("Drag teams to your predicted finishing positions (1-16).")
        
        # Bidirectional sortable list
        current_order = sort_items(TEAMS, direction="vertical", key="shanghai_v6_final")
        
        st.write("---")
        oracle_name = st.text_input("ORACLE IDENTIFIER", placeholder="Enter your name or handle...")
        
        if st.button("LOCK IN PROPHECY"):
            if not oracle_name:
                st.warning("Identity required to secure prophecy.")
            else:
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Oracle Name": oracle_name,
                    "Rankings": ", ".join(current_order)
                }])
                updated_df = pd.concat([subs_df, new_entry], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                st.success(f"Prophecy Encrypted. Welcome, {oracle_name}.")
                st.cache_data.clear()

    with col2:
        st.markdown("### <span style='color:#00F5FF'>02</span> PROPHECY RECEIPT", unsafe_allow_html=True)
        # Dynamic preview based on the current drag-and-drop state
        for i, team in enumerate(current_order):
            st.markdown(f"""
                <div class="team-card">
                    <span class="rank-badge">RANK {i+1}</span>
                    <img src="{get_logo(team)}" width="35" style="margin-right:18px;" onerror="this.src='https://raw.githubusercontent.com/RubenFr87/DotaPredictor/main/Aegis.png'">
                    <span style="font-weight:600; color:#e0e0e0; font-size:1.1em;">{team}</span>
                </div>
            """, unsafe_allow_html=True)

# --- TAB 2: LEADERBOARD ---
with tab2:
    st.markdown("<h2 style='color:#00F5FF'>🏆 GLOBAL LEADERBOARD</h2>", unsafe_allow_html=True)
    if subs_df.empty or "Oracle Name" not in subs_df.columns:
        st.info("The Oracle Vault is sealed. Be the first to submit.")
    else:
        # Business logic for scoring
        latest_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        leaderboard_rows = []
        for _, row in latest_subs.iterrows():
            pred_list = row["Rankings"].split(", ")
            penalty = 0
            perfects = 0
            if not res_df.empty and "Team" in res_df.columns:
                for rank, team in enumerate(pred_list, 1):
                    off_row = res_df[res_df["Team"] == team]
                    if not off_row.empty:
                        off_rank = int(off_row.iloc[0]["Rank"])
                        if off_rank > 0:
                            dist = abs(rank - off_rank)
                            mult = 4 if rank == 1 else (3 if rank == 2 else (2 if rank in [3, 4] else 1))
                            penalty += (dist * mult)
                            if dist == 0: perfects += 1
            leaderboard_rows.append({"Oracle": row["Oracle Name"], "Penalty": penalty, "Bullseyes": perfects})
        
        lb_final = pd.DataFrame(leaderboard_rows).sort_values(["Penalty", "Bullseyes"], ascending=[True, False])
        st.dataframe(lb_final, use_container_width=True)

# --- TAB 3: MATRIX ---
with tab3:
    st.markdown("<h2 style='color:#00F5FF'>📊 COMPARISON MATRIX</h2>", unsafe_allow_html=True)
    if not subs_df.empty:
        matrix_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        matrix_data = []
        for _, row in matrix_subs.iterrows():
            ranks = row["Rankings"].split(", ")
            entry = {"Oracle": row["Oracle Name"]}
            for i, t in enumerate(ranks): entry[f"#{i+1}"] = t
            matrix_data.append(entry)
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True)

# --- TAB 4: PROTOCOL ---
with tab4:
    st.markdown("<h2 style='color:#00F5FF'>📜 ORACLE CALCULATION RULES</h2>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.info("**SCORING:** Lower points = Higher rank.")
        st.markdown("""
        **Penalty Calculation:**
        - Distance from Actual x Multiplier.
        - **1st Place Pick:** 4x Penalty
        - **2nd Place Pick:** 3x Penalty
        - **3rd/4th Place Pick:** 2x Penalty
        - **All Others:** 1x Penalty
        """)
    with c2:
        st.info("**TIES:** Resolved by 'Bullseyes'.")
        st.markdown("""
        **Tie-Breaking Priority:**
        1. Total exact rank matches (Bullseyes).
        2. Lowest penalty in the Top 4 bracket.
        """)
