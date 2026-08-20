import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- PAGE CONFIG ---
st.set_page_config(page_title="The International Predictions", layout="wide")

# --- CSS STYLING (CLEAN SAAS / GITHUB LIGHT) ---
st.markdown("""
    <style>
    .main { background-color: #f6f8fa; color: #24292f; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        color: #57606a;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #0969da !important; 
        color: #ffffff !important; 
        border-color: #0969da !important;
    }
    .team-card {
        background: #ffffff;
        padding: 12px 20px;
        border-radius: 8px;
        border: 1px solid #d0d7de;
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .rank-badge {
        background: #f6f8fa;
        color: #24292f;
        font-weight: bold;
        min-width: 50px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        margin-right: 15px;
        border: 1px solid #d0d7de;
    }
    .status-completed { border-left: 5px solid #cf222e; } 
    .status-active { border-left: 5px solid #1a7f37; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
GITHUB_USER = "Goosontheloose"
REPO_NAME = "DotaPredictor"
BRANCH = "main"
GITHUB_BASE = f"https://cdn.jsdelivr.net/gh/{GITHUB_USER}/{REPO_NAME}@{BRANCH}/"

def get_logo_url(team_name):
    if team_name == "Header": return f"{GITHUB_BASE}Aegis.png"
    clean_name = team_name.replace(" ", "%20")
    return f"{GITHUB_BASE}{clean_name}.png"

# --- DATA ENGINE ---
@st.cache_data(ttl=30)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    res = conn.read(worksheet="Results", ttl=30)
    sub = conn.read(worksheet="Submissions", ttl=30)
    # Normalize Data
    res['Team'] = res['Team'].str.strip()
    res['Status'] = res['Status'].str.strip().str.lower()
    res['Rank'] = pd.to_numeric(res['Rank'])
    
    # Calculate Brackets for Tied Teams
    rank_counts = res['Rank'].value_counts().to_dict()
    brackets = {}
    for r, count in rank_counts.items():
        if r > 0:
            brackets[r] = {
                'min': int(r),
                'max': int(r + count - 1)
            }
    return res, sub, brackets

results_df, subs_df, brackets = load_data()

# --- HEADER ---
col_h1, col_h2 = st.columns([1, 5])
with col_h1:
    st.image(get_logo_url("Header"), width=100)
with col_h2:
    st.title("THE INTERNATIONAL PREDICTIONS 2026")

tab1, tab2, tab3, tab4 = st.tabs(["LIVE STANDINGS", "LEADERBOARD", "PREDICTIONS MATRIX", "SCORING LOGIC"])

# --- TAB 1: LIVE STANDINGS ---
with tab1:
    if not results_df.empty:
        display_df = results_df[results_df['Rank'] > 0].sort_values(by="Rank")
        for _, row in display_df.iterrows():
            b = brackets.get(row['Rank'], {'min': row['Rank'], 'max': row['Rank']})
            rank_display = f"{b['min']}-{b['max']}" if b['min'] != b['max'] else f"{int(b['min'])}"
            style = "status-completed" if row['Status'] == "completed" else "status-active"
            
            st.markdown(f"""
                <div class="team-card {style}">
                    <div class="rank-badge">#{rank_display}</div>
                    <img src="{get_logo_url(row['Team'])}" width="30" style="margin-right:15px">
                    <span style="font-weight:600;">{row['Team']}</span>
                    <span style="margin-left:auto; color:#57606a; font-size:0.8em;">{row['Status'].upper()}</span>
                </div>
            """, unsafe_allow_html=True)

# --- TAB 2: LEADERBOARD ---
with tab2:
    if not subs_df.empty and not results_df.empty:
        leaderboard = []
        results_map = results_df.set_index('Team').to_dict('index')
        
        for _, sub in subs_df.iterrows():
            oracle = sub['Oracle Name']
            ranks = [r.strip() for r in str(sub['Rankings']).split(',')]
            
            f_score = 0  # Points from completed teams
            active_penalties = 0  # Points from current standing of active teams
            f_perfect = 0
            p_perfect = 0
            
            for i, team in enumerate(ranks):
                pred_slot = i + 1
                if team in results_map:
                    actual = results_map[team]
                    if actual['Rank'] == 0: continue
                    
                    b = brackets.get(actual['Rank'])
                    
                    # TIER LOGIC: 0 penalty if within bracket
                    if b['min'] <= pred_slot <= b['max']:
                        dist = 0
                        is_bullseye = True
                    else:
                        dist = min(abs(pred_slot - b['min']), abs(pred_slot - b['max']))
                        is_bullseye = False
                    
                    # Multipliers
                    mult = 4 if pred_slot == 1 else 3 if pred_slot == 2 else 2 if pred_slot in [3, 4] else 1
                    penalty = (dist * mult)
                    if is_bullseye: penalty -= 1
                    
                    if actual['Status'] == "completed":
                        f_score += penalty
                        if is_bullseye: f_perfect += 1
                        p_perfect += 1
                    else:
                        active_penalties += penalty
                        if is_bullseye: p_perfect += 1
            
            projected_total = f_score + active_penalties
            
            leaderboard.append({
                "Oracle": oracle,
                "Finalised Score": f_score,
                "Perfect (F)": f_perfect,
                "Projected Score": projected_total,
                "Perfect (P)": p_perfect
            })
            
        ld_df = pd.DataFrame(leaderboard).sort_values(
            by=["Finalised Score", "Perfect (F)", "Projected Score"], 
            ascending=[True, False, True]
        ).reset_index(drop=True)
        
        ld_df.insert(0, "Rank", ld_df.index + 1)
        
        st.dataframe(ld_df, hide_index=True, use_container_width=True)
# --- TAB 3: MATRIX ---
with tab3:
    if not subs_df.empty:
        matrix_data = []
        for _, row in subs_df.iterrows():
            ranks = [r.strip() for r in str(row['Rankings']).split(',')]
            matrix_data.append([row['Oracle Name']] + ranks)
        
        m_cols = ["Oracle"] + [f"#{i+1}" for i in range(16)]
        m_df = pd.DataFrame(matrix_data, columns=m_cols)
        st.dataframe(m_df, hide_index=True)

# --- TAB 4: LOGIC ---
with tab4:
    st.markdown("""
    ### THE ORACLE PROTOCOL
    
    **1. Tiered Ranking (The Bracket Rule)**
    If teams are tied in a bracket (e.g., 5th-6th or 9th-12th), any prediction that falls **anywhere** within that range is considered a perfect prediction.
    *   **Distance:** 0
    *   **Penalty:** 0
    *   **Bonus:** -1 Prophetic Deduction
    
    **2. Distance Penalties**
    If your prediction falls outside the bracket, the distance is calculated from your slot to the **nearest edge** of the finished bracket.
    
    **3. Multipliers**
    The stakes are higher for your top picks:
    *   Predicted 1st: **4x Penalty** | 2nd: **3x Penalty** | 3rd-4th: **2x Penalty**
    
    **4. Projected Score**
    This is the sum of your **Finalised Score** plus the current penalties from **Active** teams. It shows where you will finish if the standings don't change.
    """)
