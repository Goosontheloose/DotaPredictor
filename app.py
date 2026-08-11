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
    "Team Falcons", "LGD Gaming", "Iron Wing", "Nigma Galaxy",
    "BoomBoys", "OG", "TEAM VISION", "Team Resilience",
    "Team Spirit", "Xtreme Gaming", "Team Liquid", "Vigi Gaming",
    "Aurora Gaming", "GamerLegion", "Team Yandex", "huligani"
]

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide")

# --- UI STYLING ---
st.markdown(f"""
    <style>
    .header-container {{ display: flex; align-items: center; gap: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; margin-bottom: 25px; }}
    /* Styling for the Rank Cards inside the Sortable List */
    .st-sortable-item {{ 
        background: #ffffff !important; 
        border: 1px solid #e0e0e0 !important; 
        border-radius: 8px !important; 
        padding: 10px !important; 
        margin-bottom: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }}
    .rank-card {{ display: flex; align-items: center; gap: 15px; }}
    .rank-badge {{ 
        background: #f0f2f6; 
        color: #31333F; 
        font-weight: bold; 
        padding: 4px 10px; 
        border-radius: 4px; 
        min-width: 40px; 
        text-align: center;
    }}
    .rule-card {{ background: #ffffff; padding: 20px; border-radius: 8px; border-left: 5px solid #00FF9D; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    .multiplier-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    .multiplier-table th, .multiplier-table td {{ padding: 10px; border: 1px solid #eee; text-align: left; }}
    .multiplier-table th {{ background-color: #fafafa; }}
    </style>
""", unsafe_allow_html=True)

def get_logo_url(team_name):
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

# --- TAB 1: LOCK-IN (UNIFIED VIEW) ---
with tabs[0]:
    st.subheader("Finalize Your Prophecy")
    oracle_name = st.text_input("Oracle Name", placeholder="Enter your name to be recorded...")
    
    st.info("Drag and drop to reorder. The list reflects your live 1-16 standings.")

    # Create the data for the sortable items including the HTML for logos
    # Note: sort_items only returns the labels, so we map the visual cards
    sortable_data = [
        {
            "id": team,
            "content": f"""
                <div class="rank-card">
                    <img src="{get_logo_url(team)}" width="30" height="30" style="object-fit: contain;">
                    <span style="font-weight: 500;">{team}</span>
                </div>
            """
        } for team in TEAMS
    ]

    # Render the drag-and-drop list
    # We use the list of dicts to show logos, returns the 'id' (team name)
    current_ranking = sort_items(sortable_data, direction="vertical", key="oracle_sort")
    
    st.markdown("---")
    if st.button("LOCK IN PROPHECY", use_container_width=True, type="primary"):
        if not oracle_name:
            st.error("Identification required. Please enter an Oracle Name.")
        else:
            new_row = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Oracle Name": oracle_name,
                "Rankings": ",".join(current_ranking)
            }])
            # APPEND ONLY: Safely adds to the end without resurrecting old data
            updated_subs = pd.concat([subs_df, new_row], ignore_index=True)
            conn.create(worksheet="Submissions", data=updated_subs)
            st.success(f"Prophecy locked for {oracle_name}!")
            st.balloons()
            st.cache_data.clear()

# --- TAB 2: LEADERBOARD (DEDUPLICATED) ---
with tabs[1]:
    if results_df.empty or "Rank" not in results_df.columns:
        st.info("Awaiting official tournament results. Standings will update automatically.")
    elif subs_df.empty:
        st.warning("No prophecies found in the archives.")
    else:
        # Deduplicate: Only calculate the LATEST entry for every unique name
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

# --- TAB 4: PROTOCOL (FULL RESTORATION) ---
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
