import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import json
from datetime import datetime

# --- CONFIGURATION (EXACT REVERT) ---
GITHUB_USER = "Goosontheloose" 
REPO_NAME = "DotaPredictor"
BRANCH = "main"

# These names match your GitHub filenames exactly.
TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide")

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

# --- LOGO HELPER ---
def get_logo_url(name):
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{name.replace(' ', '%20')}.png"

# --- UNIFIED DRAG-AND-DROP COMPONENT ---
def unified_prediction_ui(team_list):
    items_json = json.dumps([{"name": t, "logo": get_logo_url(t)} for t in team_list])
    
    html_code = f"""
    <div id="drag-container" style="font-family: sans-serif; max-width: 500px; background: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #ddd;">
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
                    <span style="font-weight: bold; color: #00F5FF; width: 30px; font-family: monospace;">#${{index + 1}}</span>
                    <img src="${{team.logo}}" style="width: 28px; height: 28px; margin-right: 12px; object-fit: contain;">
                    <span style="font-weight: 600; color: #111;">${{team.name}}</span>
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
                
                Array.from(listElement.children).forEach((li, idx) => {{
                    li.querySelector('span').innerText = '#' + (idx + 1);
                }});
            }}
        }});
        
        const initialOrder = teams.map(t => t.name);
        window.parent.postMessage({{type: 'streamlit:setComponentValue', value: initialOrder}}, '*');
    </script>
    """
    return components.html(html_code, height=950)

# --- HEADER ---
st.title("AEGIS ORACLE: SHANGHAI 2026")

# --- TABS ---
tabs = st.tabs(["🔮 LOCK-IN", "📊 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

with tabs[0]:
    oracle_name = st.text_input("Oracle Name", placeholder="Your name...")
    current_order = unified_prediction_ui(TEAMS)
    
    if st.button("LOCK IN PROPHECY", type="primary", use_container_width=True):
        if not oracle_name:
            st.error("Please enter an Oracle Name.")
        elif not isinstance(current_order, list):
            st.warning("Please interact with the list to confirm the order.")
        else:
            try:
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(current_order)
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
        # Filter latest prophecy per user
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        
        lb = []
        for _, row in clean_subs.iterrows():
            preds = row['Rankings'].split(',')
            score, perf = 0, 0
            for i, team in enumerate(preds):
                p_rank = i + 1
                a_rank = int(float(actual_ranks.get(team.strip(), 0)))
                
                if a_rank > 0:
                    # Multipliers: #1=4x, #2=3x, #3-4=2x, rest=1x
                    m = 4 if p_rank == 1 else 3 if p_rank == 2 else 2 if p_rank in [3, 4] else 1
                    penalty = abs(p_rank - a_rank) * m
                    
                    # Prophetic Deduction: -1 for exact match
                    bonus = -1 if p_rank == a_rank else 0
                    
                    score += (penalty + bonus)
                    if p_rank == a_rank:
                        perf += 1
            
            lb.append({
                "Oracle": row['Oracle Name'], 
                "Penalty Score": int(score), 
                "Perfect Picks": perf
            })
        
        st.dataframe(pd.DataFrame(lb).sort_values(["Penalty Score", "Perfect Picks"], ascending=[True, False]), hide_index=True, use_container_width=True)
    else:
        st.info("Leaderboard will update once manual results are entered in the sheet.")

with tabs[2]:
    st.subheader("Predictions Matrix")
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
    st.markdown("""
    ### ⛳ Golf Scoring Logic
    The goal is the **lowest penalty score**. The closer your prediction is to the actual result, the fewer points you receive.
    
    ### 🎯 Prophetic Deduction
    A perfect prediction (Bullseye) is rewarded with a point deduction. If your predicted rank matches the actual rank exactly:
    *   **Distance Penalty = 0**
    *   **Bonus Deduction = -1 point**
    
    ### 🔢 Penalty Multipliers
    Penalties are weighted based on **your** predicted rank:
    * **1st Place Pick:** 4x Multiplier  
    * **2nd Place Pick:** 3x Multiplier  
    * **3rd - 4th Place Pick:** 2x Multiplier  
    * **5th - 16th Place Pick:** 1x Multiplier
    
    ### 🧪 The Calculation
    `(|Predicted Rank - Actual Rank| × Multiplier) + Bonus = Team Score`
    """)
