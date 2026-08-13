import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- APP CONFIG & CONSTANTS ---
st.set_page_config(page_title="Aegis Oracle: Shanghai 2026", layout="wide")

# CDN Base for Images
GITHUB_BASE = "https://cdn.jsdelivr.net/gh/Goosontheloose/DotaPredictor@main/"

# Fixed 16 Teams List
TEAMS = [
    "Xtreme Gaming", "Team Falcons", "Team Liquid", "Spirit", "Gaimin Gladiators",
    "Tundra", "Cloud9", "Aurora", "BetBoom Team", "Entity", "Vici",
    "Nigma", "PSG Quest", "Talon", "Iron Wing", "Huligani"
]

# --- LOGO HELPER ---
def get_logo_url(team_name):
    if not team_name:
        return f"{GITHUB_BASE}Aegis.png"
    file_name = f"{team_name}.png".replace(" ", "%20")
    return f"{GITHUB_BASE}{file_name}"

# --- DATABASE CONNECTION ---
@st.cache_data(ttl=60) # Reduced TTL to see sheet updates faster
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    results = conn.read(worksheet="Results")
    submissions = conn.read(worksheet="Submissions")
    
    # CLEAN HEADERS: Remove hidden spaces and normalize to lowercase for logic
    results.columns = [str(c).strip() for c in results.columns]
    submissions.columns = [str(c).strip() for c in submissions.columns]
    
    return results, submissions

# --- SCORING LOGIC ---
def calculate_score(predicted_rank, official_rank):
    if official_rank == 0:
        return 0, 0
    distance = abs(predicted_rank - official_rank)
    if predicted_rank == 1: multiplier = 4
    elif predicted_rank == 2: multiplier = 3
    elif predicted_rank in [3, 4]: multiplier = 2
    else: multiplier = 1
    penalty = distance * multiplier
    bonus = -1 if distance == 0 else 0
    return penalty, bonus

# --- STYLING ---
st.markdown(f"""
    <style>
    .main {{ background-color: #f8f9fa; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #ffffff;
        border-radius: 4px 4px 0px 0px;
        padding: 10px 20px;
        border: 1px solid #e1e4e8;
    }}
    .stTabs [aria-selected="true"] {{ background-color: #f1f8ff !important; border-bottom: 2px solid #0366d6 !important; }}
    .team-card {{
        background: white;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #e1e4e8;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .team-card.completed {{ border-left: 5px solid #d73a49; background-color: #fff5f5; }}
    .team-card.active {{ border-left: 5px solid #28a745; }}
    .rank-badge {{
        font-weight: bold;
        color: #0366d6;
        width: 35px;
        font-size: 1.1em;
    }}
    .team-logo {{ width: 30px; height: 30px; margin: 0 15px; object-fit: contain; }}
    .status-tag {{ margin-left: auto; font-size: 0.8em; padding: 2px 8px; border-radius: 10px; }}
    .status-completed {{ background: #ffdce0; color: #d73a49; }}
    .status-active {{ background: #dcffe4; color: #28a745; }}
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
col_h1, col_h2 = st.columns([1, 8])
with col_h1:
    st.image(get_logo_url(None), width=80)
with col_h2:
    st.title("Aegis Oracle: Shanghai 2026")
    st.subheader("Official Tournament Standings")

# --- MAIN APP ---
try:
    results_df, submissions_df = load_data()
    
    # Map normalized column names for reliability
    res_cols = {c.lower(): c for c in results_df.columns}
    sub_cols = {c.lower(): c for c in submissions_df.columns}
    
    # Column mapping logic
    COL_TEAM = res_cols.get('team', 'Team')
    COL_RANK = res_cols.get('rank', 'Rank')
    COL_ACTIVE = res_cols.get('active', 'Active')
    
    tab1, tab2, tab3, tab4 = st.tabs(["Standings", "Leaderboard", "Predictions", "Rules"])

    with tab1:
        st.markdown("### Current Rankings")
        # Ensure data is sorted by Rank
        standings = results_df.sort_values(by=COL_RANK)
        
        for _, row in standings.iterrows():
            val_active = str(row[COL_ACTIVE]).strip().lower()
            is_active = (val_active == 'active')
            
            status_class = "active" if is_active else "completed"
            status_text = "IN PLAY" if is_active else "FINAL"
            tag_class = "status-active" if is_active else "status-completed"
            
            st.markdown(f"""
                <div class="team-card {status_class}">
                    <div class="rank-badge">#{int(row[COL_RANK])}</div>
                    <img src="{get_logo_url(row[COL_TEAM])}" class="team-logo">
                    <div style="font-weight: 500;">{row[COL_TEAM]}</div>
                    <div class="status-tag {tag_class}">{status_text}</div>
                </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### The Oracle Leaderboard")
        if not submissions_df.empty:
            COL_TS = sub_cols.get('timestamp', 'Timestamp')
            COL_NAME = sub_cols.get('oracle name', 'Oracle Name')
            COL_PREDS = sub_cols.get('rankings', 'Rankings')
            
            submissions_df[COL_TS] = pd.to_datetime(submissions_df[COL_TS])
            latest_subs = submissions_df.sort_values(COL_TS).groupby(COL_NAME).last().reset_index()
            
            leaderboard_data = []
            results_dict = dict(zip(results_df[COL_TEAM], results_df[COL_RANK]))

            for _, sub in latest_subs.iterrows():
                pred_list = sub[COL_PREDS].split(', ')
                finalised_score = 0
                projected_score = 0
                perfect_picks = 0
                
                for i, team in enumerate(pred_list):
                    pred_rank = i + 1
                    actual_rank = results_dict.get(team, 0)
                    penalty, bonus = calculate_score(pred_rank, actual_rank)
                    
                    if actual_rank != 0:
                        team_status = results_df[results_df[COL_TEAM] == team][COL_ACTIVE].iloc[0].strip().lower()
                        if team_status != 'active':
                            finalised_score += (penalty + bonus)
                        else:
                            projected_score += (penalty + bonus)
                        if bonus == -1: perfect_picks += 1
                
                leaderboard_data.append({
                    "Oracle": sub[COL_NAME],
                    "Finalised Score": finalised_score,
                    "Projected Score": projected_score,
                    "Total Penalty": finalised_score + projected_score,
                    "Perfect Picks": perfect_picks
                })
            
            lb_df = pd.DataFrame(leaderboard_data).sort_values(by=["Finalised Score", "Perfect Picks", "Projected Score"], ascending=[True, False, True])
            st.table(lb_df)
        else:
            st.info("No prophecies have been locked in yet.")

    with tab3:
        st.markdown("### Prophecy Matrix")
        if not submissions_df.empty:
            COL_PREDS = sub_cols.get('rankings', 'Rankings')
            COL_NAME = sub_cols.get('oracle name', 'Oracle Name')
            matrix_df = latest_subs.copy()
            for i in range(16):
                matrix_df[f"#{i+1}"] = matrix_df[COL_PREDS].apply(lambda x: x.split(', ')[i] if len(x.split(', ')) > i else "")
            st.dataframe(matrix_df.drop(columns=[sub_cols.get('timestamp'), COL_PREDS]))

    with tab4:
        st.markdown("""
        ### The Oracle Protocol
        The Oracle system uses **Golf Scoring** (Lowest Penalty Wins). Mistake multipliers apply to the top of your bracket, and a **-1 bonus** is awarded for every exact rank match.
        """)

except Exception as e:
    st.error(f"System Error: {e}")
