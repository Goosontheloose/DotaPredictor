import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items
from datetime import datetime

# --- CONFIGURATION ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"

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
    .protocol-card {{ background: #ffffff; padding: 25px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 20px; }}
    </style>
""", unsafe_allow_html=True)

def get_logo_url(file_name):
    fn = "Nigma" if file_name == "Nigma Galaxy" else file_name
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{fn.replace(' ', '%20')}.png"

# --- DATA ENGINE ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_data():
    try:
        res = conn.read(worksheet="Results")
        sub = conn.read(worksheet="Submissions")
        return res.dropna(how='all'), sub.dropna(how='all')
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

# --- TAB 1: LOCK-IN (DRAG & DROP RESTORED) ---
with tabs[0]:
    st.subheader("Finalize Your Prophecy")
    oracle_name = st.text_input("Enter Oracle Name", placeholder="e.g. Arteezy Fan #1")
    
    st.info("Drag and drop teams to set your 1-16 ranking.")
    
    # Drag and Drop Component
    sorted_teams = sort_items(TEAMS, direction="vertical")
    
    if st.button("LOCK IN RANKINGS", use_container_width=True):
        if not oracle_name:
            st.error("Please enter an Oracle Name before locking in.")
        else:
            # Prepare new entry
            new_entry = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Oracle Name": oracle_name,
                "Rankings": ",".join(sorted_teams)
            }])
            
            # Write ONLY the new entry to the sheet (prevents duplicate name bug)
            conn.create(worksheet="Submissions", data=pd.concat([subs_df, new_entry], ignore_index=True))
            st.success(f"Prophecy for {oracle_name} has been etched in the stars!")
            st.balloons()
            st.cache_data.clear() # Refresh data for the leaderboard

# --- TAB 2: LEADERBOARD ---
with tabs[1]:
    if results_df.empty or "Rank" not in results_df.columns:
        st.info("Leaderboard is offline until the Grand Arbiter updates official results.")
    elif subs_df.empty:
        st.warning("No prophecies found.")
    else:
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        leaderboard = []
        for _, row in subs_df.iterrows():
            preds = row['Rankings'].split(',')
            score, perfect = 0, 0
            for i, team in enumerate(preds):
                p_rank = i + 1
                a_rank = actual_ranks.get(team, 0)
                if a_rank > 0:
                    mult = 4 if p_rank == 1 else 3 if p_rank == 2 else 2 if p_rank in [3,4] else 1
                    score += (abs(p_rank - a_rank) * mult)
                    if p_rank == a_rank: perfect += 1
            leaderboard.append({"Oracle": row['Oracle Name'], "Score": int(score), "Perfect Picks": perfect})
        
        st.table(pd.DataFrame(leaderboard).sort_values(by=["Score", "Perfect Picks"], ascending=[True, False]))

# --- TAB 3: MATRIX ---
with tabs[2]:
    if not subs_df.empty:
        matrix_data = []
        for _, row in subs_df.iterrows():
            preds = row['Rankings'].split(',')
            entry = {"Oracle": row['Oracle Name']}
            for i, team in enumerate(preds):
                entry[f"#{i+1}"] = team
            matrix_data.append(entry)
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)

# --- TAB 4: PROTOCOL ---
with tabs[3]:
    st.markdown("""
    <div class="protocol-card">
        <h3>Scoring Protocol</h3>
        <p>Penalty = <code>|Predicted - Actual| × Multiplier</code></p>
        <ul>
            <li><b>Rank 1:</b> 4x Penalty</li>
            <li><b>Rank 2:</b> 3x Penalty</li>
            <li><b>Rank 3-4:</b> 2x Penalty</li>
            <li><b>Others:</b> 1x Penalty</li>
        </ul>
        <p><i>Note: Shared tiers (e.g., 5th-6th) are assigned the best rank (5).</i></p>
    </div>
    """, unsafe_allow_html=True)
