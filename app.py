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

TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

st.set_page_config(page_title="AEGIS ORACLE 2026", layout="wide")

# --- DATABASE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10) # Reduced TTL for faster updates
def load_data():
    try:
        res = conn.read(worksheet="Results").dropna(how='all')
        sub = conn.read(worksheet="Submissions").dropna(how='all')
        return res, sub
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

results_df, subs_df = load_data()

# --- LOGO HELPER ---
def get_logo_url(name):
    return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{name.replace(' ', '%20')}.png"

# --- THE UNIFIED INTERFACE ---
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
        
        function sendToStreamlit(values) {{
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: values
            }}, '*');
        }}

        function render() {{
            listElement.innerHTML = '';
            teams.forEach((team, index) => {{
                const li = document.createElement('li');
                li.setAttribute('data-id', team.name);
                li.style = "display: flex; align-items: center; background: white; margin-bottom: 8px; padding: 10px; border-radius: 6px; border: 1px solid #eee; cursor: grab; box-shadow: 0 2px 4px rgba(0,0,0,0.05);";
                li.innerHTML = `
                    <span style="font-weight: bold; color: #00F5FF; width: 35px; font-family: monospace;">#${{index + 1}}</span>
                    <img src="${{team.logo}}" style="width: 28px; height: 28px; margin-right: 12px; object-fit: contain;" onerror="this.src='https://www.google.com/s2/favicons?sz=64&domain=dota2.com'">
                    <span style="font-weight: 600; color: #111;">${{team.name}}</span>
                `;
                listElement.appendChild(li);
            }});
        }}

        render();
        // Force initial sync
        sendToStreamlit(teams.map(t => t.name));

        new Sortable(listElement, {{
            animation: 150,
            onEnd: function() {{
                const newOrder = Array.from(listElement.children).map(li => li.getAttribute('data-id'));
                sendToStreamlit(newOrder);
                Array.from(listElement.children).forEach((li, idx) => {{
                    li.querySelector('span').innerText = '#' + (idx + 1);
                }});
            }}
        }});
    </script>
    """
    return components.html(html_code, height=750)

st.title("AEGIS ORACLE: SHANGHAI 2026")
tabs = st.tabs(["🔮 LOCK-IN", "📊 LEADERBOARD", "🧬 MATRIX", "📜 PROTOCOL"])

with tabs[0]:
    oracle_name = st.text_input("Oracle Name", placeholder="Your name...")
    current_order = unified_prediction_ui(TEAMS)
    
    if st.button("LOCK IN PROPHECY", type="primary", use_container_width=True):
        if not oracle_name:
            st.error("Missing Oracle Name.")
        elif not current_order:
            st.warning("Interface initializing... please wait a second or move a team.")
        else:
            try:
                new_entry = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Oracle Name": oracle_name,
                    "Rankings": ",".join(current_order)
                }])
                updated_df = pd.concat([subs_df, new_entry], ignore_index=True)
                conn.create(worksheet="Submissions", data=updated_df)
                st.success(f"Prophecy locked for {oracle_name}!")
                st.balloons()
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Write failed: {e}")

with tabs[1]:
    # FIXED: Strict check for empty sheet to prevent "Ghost" names
    if subs_df.empty or len(subs_df) == 0:
        st.info("The Oracle Vault is empty. Be the first to lock in a prophecy!")
    elif results_df.empty or "Rank" not in results_df.columns or (results_df['Rank'] == 0).all():
        st.warning("Tournament Standings are not yet live. Check back once the group stage begins.")
    else:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        actual_ranks = dict(zip(results_df['Team'], results_df['Rank']))
        lb = []
        for _, row in clean_subs.iterrows():
            preds = str(row['Rankings']).split(',')
            score, perf = 0, 0
            for i, team in enumerate(preds):
                p_rank, a_rank = i + 1, actual_ranks.get(team, 0)
                if a_rank > 0:
                    m = 4 if p_rank==1 else 3 if p_rank==2 else 2 if p_rank in [3,4] else 1
                    score += abs(p_rank - a_rank) * m
                    if p_rank == a_rank: perf += 1
            lb.append({"Oracle": row['Oracle Name'], "Penalty Score": int(score), "Perfect Picks": perf})
        st.table(pd.DataFrame(lb).sort_values(["Penalty Score", "Perfect Picks"], ascending=[True, False]))

with tabs[2]:
    if not subs_df.empty:
        clean_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_rows = []
        for _, row in clean_subs.iterrows():
            p = str(row['Rankings']).split(',')
            d = {"Oracle": row['Oracle Name']}
            for i, team in enumerate(p): d[f"#{i+1}"] = team
            m_rows.append(d)
        st.dataframe(pd.DataFrame(m_rows), hide_index=True)

with tabs[3]:
    # RESTORED FULL PROTOCOL
    st.markdown("### 📜 Aegis Oracle: The Scoring Protocol")
    st.markdown("""
    **1. The Calculation Logic**
    The competition uses a **Golf-Style Scoring** system. Your goal is to have the **lowest** penalty score possible.
    `|Predicted Rank - Official Rank| × Multiplier = Penalty Points`

    **2. High-Stakes Multipliers**
    Accuracy at the top of the bracket is weighted more heavily:
    - **1st Place (Champion):** 4x Multiplier
    - **2nd Place:** 3x Multiplier
    - **3rd - 4th Place:** 2x Multiplier
    - **5th - 16th Place:** 1x Multiplier

    **3. Tied Rank Handling**
    In tournament tiers (e.g., 5th-6th), the **best possible rank** for that tier is used for calculation. 
    *Example:* If a team finishes in the 5th-6th tier, their official rank is counted as **5**.

    **4. Tie-Breakers**
    If two Oracles have the same Penalty Score, the one with the most **Perfect Picks** (exact rank matches) wins.
    """)
