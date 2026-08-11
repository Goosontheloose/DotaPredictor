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
GITHUB_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/"

TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="centered")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def load_data():
    try:
        # ttl=0 ensures we don't get old data when we refresh
        res = conn.read(worksheet="Results", ttl=0).dropna(how='all')
        sub = conn.read(worksheet="Submissions", ttl=0).dropna(how='all')
        return res, sub
    except:
        return pd.DataFrame(), pd.DataFrame()

results_df, subs_df = load_data()

# --- LOGO HELPER ---
def get_logo_url(name):
    # Matches your exact GitHub folder structure
    return f"{GITHUB_BASE}{name.replace(' ', '%20')}.png"

# --- THE UNIFIED INTERFACE (Your Design) ---
def unified_prediction_ui(team_list):
    items_json = json.dumps([{"name": t, "logo": get_logo_url(t)} for t in team_list])
    
    html_code = f"""
    <div id="drag-container" style="font-family: sans-serif; background: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #ddd;">
        <ul id="sortable-list" style="list-style: none; padding: 0; margin: 0;"></ul>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
    <script>
        const teams = {items_json};
        const listElement = document.getElementById('sortable-list');
        const aegisFallback = "{GITHUB_BASE}Aegis.png";

        function render() {{
            listElement.innerHTML = '';
            teams.forEach((team, index) => {{
                const li = document.createElement('li');
                li.setAttribute('data-id', team.name);
                li.style = "display: flex; align-items: center; background: white; margin-bottom: 8px; padding: 12px; border-radius: 8px; border: 1px solid #eee; cursor: grab; box-shadow: 0 1px 3px rgba(0,0,0,0.05);";
                li.innerHTML = `
                    <span style="font-weight: bold; color: #57606a; width: 35px; font-family: monospace; font-size: 14px;">#${{index + 1}}</span>
                    <img src="${{team.logo}}" onerror="this.src='${{aegisFallback}}'" style="width: 28px; height: 28px; margin-right: 12px; object-fit: contain;">
                    <span style="font-weight: 600; color: #24292f; font-size: 16px;">${{team.name}}</span>
                `;
                listElement.appendChild(li);
            }});
        }}

        render();

        const sortable = new Sortable(listElement, {{
            animation: 150,
            onEnd: function() {{
                const newOrder = Array.from(listElement.children).map(li => li.getAttribute('data-id'));
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    value: newOrder
                }}, '*');
                
                // Update rank numbers visually
                Array.from(listElement.children).forEach((li, idx) => {{
                    li.querySelector('span').innerText = '#' + (idx + 1);
                }});
            }}
        }});
        
        // Initial send
        const initialOrder = teams.map(t => t.name);
        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: initialOrder}}, '*');
    </script>
    """
    return components.html(html_code, height=950)

# --- UI LAYOUT ---
st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <img src="{GITHUB_BASE}Aegis.png" width="80">
        <h1 style="margin-top: 10px; color: #1a1a1a; letter-spacing: -1px;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔮 LOCK-IN", "🏆 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

with tabs[0]:
    oracle_name = st.text_input("Oracle Name", placeholder="Your name...")
    # This captures the order from the Javascript ranker
    current_order = unified_prediction_ui(TEAMS)
    
    if st.button("LOCK IN PROPHECY", type="primary", use_container_width=True):
        if not oracle_name:
            st.error("Missing Oracle Name.")
        # SAFETY CHECK: Ensure current_order is a list and not None
        elif current_order is None or not isinstance(current_order, list):
            st.warning("Please move one team to confirm your rank order.")
        else:
            try:
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(current_order)
                }])
                
                # Append to existing data
                updated_df = pd.concat([subs_df, new_entry], ignore_index=True)
                
                # Use update (worksheet=Submissions) to write to your existing sheet
                conn.update(worksheet="Submissions", data=updated_df)
                
                st.success(f"Prophecy locked for {oracle_name}!")
                st.balloons()
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Write failed: {e}. Check if Service Account has 'Editor' access.")

with tabs[1]:
    st.subheader("Leaderboard Standings")
    if not subs_df.empty and not results_df.empty and "Rank" in results_df.columns:
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
                    # Multipliers based on your prediction rank
                    m = 4 if p_rank==1 else 3 if p_rank==2 else 2 if p_rank in [3,4] else 1
                    score += abs(p_rank - a_rank) * m
                    if p_rank == a_rank: perf += 1
            lb.append({"Oracle": row['Oracle Name'], "Penalty Score": int(score), "Perfect Picks": perf})
        st.table(pd.DataFrame(lb).sort_values(["Penalty Score", "Perfect Picks"], ascending=[True, False]))
    else:
        st.info("Leaderboard will populate once tournament results are entered in the 'Results' tab.")

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
    **Golf Scoring Logic:** The goal is the lowest possible penalty score.
    
    **1. Penalty Calculation:**  
    `|Predicted Rank - Actual Rank| × Multiplier`
    
    **2. High-Stakes Multipliers:**  
    If you predict a team will finish:
    * **1st:** 4x Penalty
    * **2nd:** 3x Penalty
    * **3rd - 4th:** 2x Penalty
    * **5th - 16th:** 1x Penalty
    
    **3. Tie-Breakers:**
    1. **Perfect Picks:** Highest number of exact rank matches.
    2. **Top Tier Accuracy:** Lowest penalty within your predicted Top 4.
    """)
