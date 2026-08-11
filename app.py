import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import json
from datetime import datetime

# --- CONFIGURATION (LOCKED) ---
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
    return f"{GITHUB_BASE}{name.replace(' ', '%20')}.png"

# --- THE UNIFIED INTERFACE (LOCKED) ---
def unified_prediction_ui(team_list):
    query_order = st.query_params.get("order", None)
    if query_order:
        current_list = query_order.split(",")
    else:
        current_list = team_list

    items_json = json.dumps([{"name": t, "logo": get_logo_url(t)} for t in current_list])
    
    html_code = f"""
    <div id="drag-container" style="font-family: sans-serif; background: #ffffff; padding: 10px;">
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
                Array.from(listElement.children).forEach((li, idx) => {{
                    li.querySelector('span').innerText = '#' + (idx + 1);
                }});
                const url = new URL(window.parent.location);
                url.searchParams.set('order', newOrder.join(','));
                window.parent.history.replaceState({{}}, '', url);
            }}
        }});
    </script>
    """
    return components.html(html_code, height=1250)

# --- HEADER ---
st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <img src="{GITHUB_BASE}Aegis.png" width="80">
        <h1 style="margin-top: 10px; color: #1a1a1a; letter-spacing: -1px;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🔮 LOCK-IN", "🏆 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

with tabs[0]:
    oracle_name = st.text_input("Oracle Name", placeholder="Enter your name to secure your prophecy...")
    unified_prediction_ui(TEAMS)
    
    if st.button("LOCK IN PROPHECY", type="primary", use_container_width=True):
        final_order_str = st.query_params.get("order", ",".join(TEAMS))
        if not oracle_name:
            st.error("Please enter your name.")
        else:
            try:
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": oracle_name,
                    "Rankings": final_order_str
                }])
                updated_df = pd.concat([subs_df, new_entry], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                st.success(f"Prophecy locked for {oracle_name}!")
                st.balloons()
                st.cache_data.clear()
                st.query_params.clear()
            except Exception as e:
                st.error(f"Write failed: {e}")

with tabs[1]:
    st.subheader("Leaderboard Standings")
    if not subs_df.empty and not results_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        raw_statuses = dict(zip(results_df['Team'], results_df.get('Status', ['Active']*len(results_df))))
        
        lb = []
        for _, row in clean_subs.iterrows():
            preds = row['Rankings'].split(',')
            f_score, p_score, perfect = 0, 0, 0
            for i, team in enumerate(preds):
                p_rank = i + 1
                a_rank = int(actual_ranks.get(team, 0))
                status_val = str(raw_statuses.get(team, 'Active')).strip().lower()
                
                if a_rank > 0:
                    m = 4 if p_rank==1 else 3 if p_rank==2 else 2 if p_rank in [3,4] else 1
                    penalty = abs(p_rank - a_rank) * m
                    p_score += penalty
                    if status_val == 'completed':
                        f_score += penalty
                    if p_rank == a_rank:
                        perfect += 1
            
            lb.append({
                "Oracle": row['Oracle Name'], 
                "Finalised Score": int(f_score), 
                "Projected Score": int(p_score), 
                "Perfect Picks": perfect
            })
        # Sorting by Projected Score (Ascending) and then Perfect Picks (Descending)
        df_lb = pd.DataFrame(lb).sort_values(["Projected Score", "Perfect Picks"], ascending=[True, False])
        st.dataframe(df_lb, hide_index=True, use_container_width=True)
    else:
        st.info("Awaiting tournament results.")

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
        st.dataframe(pd.DataFrame(m_rows), hide_index=True, use_container_width=True)

with tabs[3]:
    st.subheader("The Oracle Protocol")
    st.markdown("""
    ### ⛳ Golf Scoring Logic
    The goal is the **lowest penalty score**. The closer your prediction is to the actual result, the fewer points you receive.
    
    ### 🔢 Penalty Multipliers
    Accuracy at the top of the bracket is worth more. Penalties are multiplied based on where **you** predicted the team would finish:
    * **1st Place Pick:** 4x Penalty  
    * **2nd Place Pick:** 3x Penalty  
    * **3rd - 4th Place Pick:** 2x Penalty  
    * **5th - 16th Place Pick:** 1x Penalty
    
    ### 🧪 The Formula
    `|Predicted Rank - Actual Rank| × Multiplier = Penalty`
    
    **Example:**  
    If you pick **Liquid** for **1st Place** (4x multiplier), but they finish **3rd**:  
    `|1 - 3| = 2`  
    `2 × 4 = 8 Penalty Points`
    
    ### 📊 Score Types
    * **Finalised Score:** Points from teams marked as **'Completed'** in the tournament results.
    * **Projected Score:** Your current score including all teams currently **'Active'**.
    
    ### 🏁 Tie-Breakers
    1. **Perfect Picks:** Whoever guessed more exact rankings wins.
    2. **Top Heavy:** Lowest penalty within the Top 4 picks.
    """)
