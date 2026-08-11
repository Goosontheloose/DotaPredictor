import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import json
from datetime import datetime

# --- CONFIGURATION ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"

# Your Exact Team List
TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide")

# --- DATABASE CONNECTION ---
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

# --- LOGO HELPER ---
def get_logo_url(name):
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{name.replace(' ', '%20')}.png"

# --- CUSTOM UNIFIED DRAGGABLE INTERFACE (HTML/JS) ---
def unified_prediction_ui(team_list):
    # Prepare data for JavaScript
    items_json = json.dumps([{"name": t, "logo": get_logo_url(t)} for t in team_list])
    
    html_code = f"""
    <div id="drag-container" style="font-family: sans-serif; max-width: 500px; background: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
        <ul id="sortable-list" style="list-style: none; padding: 0; margin: 0;"></ul>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
    <script>
        const teams = {items_json};
        const listElement = document.getElementById('sortable-list');

        function render() {{
            listElement.innerHTML = '';
            teams.forEach((team, index) => {{
                const li = document.createElement('li');
                li.setAttribute('data-id', team.name);
                li.style = "display: flex; align-items: center; background: white; margin-bottom: 8px; padding: 10px; border-radius: 6px; border: 1px solid #eee; cursor: grab; box-shadow: 0 2px 4px rgba(0,0,0,0.05);";
                li.innerHTML = `
                    <span style="font-weight: bold; color: #888; width: 30px;">#$#{{index + 1}}</span>
                    <img src="$#{{team.logo}}" style="width: 24px; height: 24px; margin-right: 12px; object-fit: contain;" onerror="this.style.visibility='hidden'">
                    <span style="font-weight: 500; color: #333;">$#{{team.name}}</span>
                `;
                listElement.appendChild(li);
            }});
        }}

        render();

        const sortable = new Sortable(listElement, {{
            animation: 150,
            ghostClass: 'sortable-ghost',
            onEnd: function() {{
                const newOrder = Array.from(listElement.children).map(li => li.getAttribute('data-id'));
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: newOrder
                }}, '*');
                
                // Update rank numbers visually immediately
                Array.from(listElement.children).forEach((li, idx) => {{
                    li.querySelector('span').innerText = '#' + (idx + 1);
                }});
            }}
        }});
    </script>
    <style>
        .sortable-ghost {{ opacity: 0.4; background: #e0e0e0; }}
    </style>
    """
    # Streamlit component to bridge JS and Python
    return components.html(html_code.replace('$#', '$'), height=750, scrolling=True)

# --- APP LAYOUT ---
st.title("AEGIS ORACLE: SHANGHAI 2026")

tabs = st.tabs(["🔮 LOCK-IN", "📊 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

# --- TAB 1: UNIFIED LOCK-IN ---
with tabs[0]:
    st.subheader("Your Prophecy")
    oracle_name = st.text_input("Oracle Name", placeholder="Enter your name to begin...")
    
    st.write("Drag teams to set your final 1-16 ranking:")
    # This renders the single unified column
    user_order = unified_prediction_ui(TEAMS)
    
    # Logic to handle the submission
    if st.button("LOCK IN PROPHECY", type="primary", use_container_width=True):
        if not oracle_name:
            st.error("Please enter your Oracle Name.")
        elif not user_order:
            st.warning("Move at least one team to initialize the order.")
        else:
            new_row = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Oracle Name": oracle_name,
                "Rankings": ",".join(user_order)
            }])
            updated_subs = pd.concat([subs_df, new_row], ignore_index=True)
            conn.create(worksheet="Submissions", data=updated_subs)
            st.success(f"Prophecy saved for {oracle_name}!")
            st.balloons()
            st.cache_data.clear()

# --- TAB 2: LEADERBOARD ---
with tabs[1]:
    if results_df.empty or "Rank" not in results_df.columns:
        st.info("Awaiting official results. Standings will update when the tournament begins.")
    elif subs_df.empty:
        st.warning("No prophecies found.")
    else:
        # Append-only deduplication
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
        matrix_data = []
        for _, row in clean_subs.iterrows():
            preds = row['Rankings'].split(',')
            entry = {"Oracle": row['Oracle Name']}
            for i, team in enumerate(preds):
                entry[f"#{i+1}"] = team
            matrix_data.append(entry)
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)

# --- TAB 4: PROTOCOL ---
with tabs[3]:
    st.markdown("### Aegis Oracle: The Scoring Protocol")
    st.markdown("""
    **1. The Core Logic**
    Golf Scoring: Lowest score wins. |Predicted Rank - Official Rank| × Multiplier = Penalty points.
    
    **2. High-Stakes Multipliers**
    - #1 (Champion): **4x** Multiplier
    - #2 (Runner-Up): **3x** Multiplier
    - #3 - #4: **2x** Multiplier
    - #5 - #16: **1x** Multiplier
    
    **3. Tied Rank Logic**
    Tied tiers (e.g., 5th-6th) use the best possible rank in that tier (Rank 5).
    """)
