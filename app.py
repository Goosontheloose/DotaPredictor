import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items
from datetime import datetime

# --- CONFIGURATION ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"

# Finalized 16-Team Roster for 2026
TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide")

# --- UI STYLING ---
st.markdown(f"""
    <style>
    .header-container {{ display: flex; align-items: center; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; margin-bottom: 25px; }}
    .preview-card {{ background: #fdfdfd; padding: 15px; border-radius: 10px; border: 1px solid #eee; position: sticky; top: 20px; }}
    .team-row-mini {{ display: flex; align-items: center; gap: 10px; padding: 5px; border-bottom: 1px solid #f0f0f0; font-size: 0.92em; }}
    .rank-num {{ font-weight: bold; color: #555; min-width: 25px; }}
    .rule-card {{ background: #ffffff; padding: 20px; border-radius: 8px; border-left: 5px solid #00FF9D; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    .multiplier-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    .multiplier-table th, .multiplier-table td {{ padding: 10px; border: 1px solid #eee; text-align: left; }}
    .multiplier-table th {{ background-color: #fafafa; }}
    </style>
""", unsafe_allow_html=True)

def get_logo_url(team_name):
    # Fix for Nigma Galaxy filename
    fn = "Nigma" if team_name == "Nigma Galaxy" else team_name
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{fn.replace(' ', '%20')}.png"

# --- DATA ENGINE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_data():
    try:
        res = conn.read(worksheet="Results").dropna(how='all')
        sub = conn.read(worksheet="Submissions").dropna(how='all')
        return res, sub
    except:
        return pd.DataFrame(), pd.DataFrame()

results_df, subs_df = load_data()

# --- HEADER ---
st.markdown(f"""
    <div class="header-container">
        <img src="{get_logo_url('Aegis')}" width="50" height="50" onerror="this.src='https://img.icons8.com/ios-filled/50/000000/shield.png'">
        <h1 style="margin:0;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔮 LOCK-IN", "📊 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

# --- TAB 1: LOCK-IN (FIXED TERMINOLOGY) ---
with tabs[0]:
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        st.subheader("Finalize Your Prophecy")
        oracle_name = st.text_input("Oracle Name", placeholder="Enter your name...")
        st.info("Drag and drop teams to set your 1-16 predicted ranking. Rank #1 is at the top.")
        
        # sort_items for the interactive drag-and-drop
        current_ranking = sort_items(TEAMS, direction="vertical", key="oracle_sort_v3")
        
        if st.button("LOCK IN PROPHECY", use_container_width=True, type="primary"):
            if not oracle_name:
                st.error("Identification required. Please enter an Oracle Name.")
            else:
                new_row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(current_ranking)
                }])
                # Append logic: concatenates new row to existing data
                updated_subs = pd.concat([subs_df, new_row], ignore_index=True)
                conn.create(worksheet="Submissions", data=updated_subs)
                st.success(f"Prophecy locked for {oracle_name}!")
                st.balloons()
                st.cache_data.clear()

    with col_preview:
        # Corrected title: Now reflects that these are predictions
        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
        st.subheader("Prophecy Preview")
        for i, team in enumerate(current_ranking):
            st.markdown(f"""
                <div class="team-row-mini">
                    <span class="rank-num">#{i+1}</span>
                    <img src="{get_logo_url(team)}" width="22" height="22" onerror="this.style.display='none'">
                    <span>{team}</span>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 2: LEADERBOARD ---
with tabs[1]:
    if results_df.empty or "Rank" not in results_df.columns:
        st.info("Awaiting official tournament results. Standings will update automatically.")
    elif subs_df.empty:
        st.warning("No prophecies found.")
    else:
        # Deduplicate: Keep only the latest submission for each name
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        leaderboard = []
        
        for _, row in clean_subs.iterrows():
            preds = row['Rankings'].split(',')
            score, perfect = 0, 0
            for i, team in enumerate(preds):
                p_rank = i + 1
                a_rank = actual_ranks.get(team, 0)
                if a_rank > 0:
                    mult = 4 if p_rank == 1 else 3 if p_rank == 2 else 2 if p_rank in [3,4] else 1
                    score += (abs(p_rank - a_rank) * mult)
                    if p_rank == a_rank: perfect += 1
            leaderboard.append({"Oracle": row['Oracle Name'], "Penalty Score": int(score), "Perfect Picks": perfect})
        
        lb_display = pd.DataFrame(leaderboard).sort_values(by=["Penalty Score", "Perfect Picks"], ascending=[True, False])
        st.table(lb_display)

# --- TAB 3: MATRIX ---
with tabs[2]:
    if not subs_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        matrix_list = []
        for _, row in clean_subs.iterrows():
            preds = row['Rankings'].split(',')
            entry = {"Oracle": row['Oracle Name']}
            for i, team in enumerate(preds):
                entry[f"#{i+1}"] = team
            matrix_list.append(entry)
        st.dataframe(pd.DataFrame(matrix_list), use_container_width=True, hide_index=True)

# --- TAB 4: PROTOCOL ---
with tabs[3]:
    st.markdown("### Aegis Oracle: The Scoring Protocol")
    
    st.markdown("""
    <div class="rule-card">
        <h4>1. The Core Logic</h4>
        <p>This is a <b>Golf Scoring</b> system: the lowest score wins. You earn "Penalty Points" based on how far your prediction is from the final tournament result.</p>
        <p><b>Formula:</b> <code>|Predicted Rank - Official Rank| × Multiplier = Penalty</code></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="rule-card">
        <h4>2. High-Stakes Multipliers</h4>
        <p>Incorrectly predicting the top of the bracket is more costly than missing the bottom. Multipliers are applied based on your <b>Predicted</b> rank.</p>
        <table class="multiplier-table">
            <tr><th>Predicted Rank</th><th>Multiplier</th><th>Risk Level</th></tr>
            <tr><td>#1 (Champion)</td><td>4x</td><td>EXTREME</td></tr>
            <tr><td>#2 (Runner-Up)</td><td>3x</td><td>HIGH</td></tr>
            <tr><td>#3 - #4</td><td>2x</td><td>MODERATE</td></tr>
            <tr><td>#5 - #16</td><td>1x</td><td>STANDARD</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="rule-card">
        <h4>3. Tied Rank Logic (Lowest Rank Wins)</h4>
        <p>Dota 2 tournaments often have shared tiers (e.g., 5th-6th or 9th-12th). For scoring, we use the <b>best possible rank</b> in that tier.</p>
        <ul>
            <li>If a team finishes 5th-6th, their official rank is <b>5</b>.</li>
            <li>If a team finishes 13th-16th, their official rank is <b>13</b>.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="rule-card">
        <h4>4. Fixed vs. Projected Scoring</h4>
        <p><b>Projected:</b> While the tournament is live, active teams are assigned a rank based on their current floor. Your score will fluctuate as teams are eliminated.</p>
        <p><b>Fixed:</b> Once a team is officially eliminated and their position is locked, their contribution to your score becomes permanent.</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("**Example Calculation:** You predict Team Liquid at #1 (4x multiplier). They finish #5. Penalty = |1 - 5| * 4 = 16 points.")
