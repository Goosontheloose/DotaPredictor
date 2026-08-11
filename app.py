import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
from datetime import datetime
import json

# --- CONFIG ---
st.set_page_config(page_title="AEGIS ORACLE: SHANGHAI 2026", layout="centered")

# EXACT 16 TEAMS
TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

GITHUB_BASE = "https://raw.githubusercontent.com/RubenFr87/DotaPredictor/main/"

# --- DB CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data():
    try:
        subs = conn.read(worksheet="Submissions", ttl=0)
        res = conn.read(worksheet="Results", ttl=0)
        return subs, res
    except:
        return pd.DataFrame(columns=["Timestamp", "Oracle Name", "Rankings"]), pd.DataFrame(columns=["Team", "Rank"])

subs_df, res_df = load_data()

# --- THE UNIFIED RANKER COMPONENT ---
def unified_ranker_component(team_list):
    items_html = ""
    for i, team in enumerate(team_list):
        logo_url = f"{GITHUB_BASE}{team.replace(' ', '%20')}.png"
        items_html += f"""
            <div class="card" data-id="{team}">
                <div class="rank-num">#<span class="idx">{i+1}</span></div>
                <img src="{logo_url}" onerror="this.src='{GITHUB_BASE}Aegis.png'">
                <div class="name">{team}</div>
                <div class="handle">☰</div>
            </div>
        """

    html_code = f"""
        <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
        <style>
            body {{ margin: 0; font-family: sans-serif; background: transparent; }}
            .container {{ padding: 5px; }}
            .card {{
                display: flex; align-items: center; padding: 12px 16px;
                background: white; border: 1px solid #d0d7de; border-radius: 8px;
                margin-bottom: 8px; cursor: grab; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }}
            .rank-num {{
                background: #f6f8fa; color: #57606a; font-weight: bold;
                padding: 4px 8px; border-radius: 4px; margin-right: 15px;
                min-width: 35px; text-align: center; border: 1px solid #d0d7de; font-size: 14px;
            }}
            img {{ width: 28px; height: 28px; margin-right: 15px; object-fit: contain; }}
            .name {{ font-weight: 600; color: #24292f; flex-grow: 1; font-size: 16px; }}
            .handle {{ color: #d0d7de; font-size: 18px; }}
            .sortable-ghost {{ opacity: 0.2; background: #f0f7ff; border: 1px dashed #0969da; }}
        </style>
        
        <div id="sortableList" class="container">
            {items_html}
        </div>

        <script>
            var el = document.getElementById('sortableList');
            var sortable = Sortable.create(el, {{
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: function () {{
                    var order = [];
                    var items = el.querySelectorAll('.card');
                    items.forEach(function(item, index) {{
                        order.append = item.getAttribute('data-id'); // Building the list
                        order.push(item.getAttribute('data-id'));
                        item.querySelector('.idx').innerText = index + 1;
                    }});
                    // IMMEDIATE SYNC TO PYTHON
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: order
                    }}, '*');
                }}
            }});
            // Initial Sync
            window.parent.postMessage({{type: 'streamlit:setComponentValue', value: {json.dumps(team_list)}}}, '*');
        </script>
    """
    return components.html(html_code, height=950)

# --- HEADER ---
st.markdown(f"""
    <div style="text-align: center; padding-top: 20px;">
        <img src="{GITHUB_BASE}Aegis.png" width="80">
        <h1 style="margin-top: 10px; color: #1a1a1a; letter-spacing: -1px;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["LOCK IN", "LEADERBOARD", "MATRIX", "PROTOCOL"])

with tab1:
    st.markdown("### 🔮 Forge Your Prophecy")
    st.caption("Drag and drop the cards to rank the teams. Your order is synced automatically.")
    
    # THE UNIFIED DRAGGABLE LIST
    user_order = unified_ranker_component(TEAMS)
    
    st.divider()
    oracle_name = st.text_input("Oracle Name", placeholder="e.g. Frederik")
    
    if st.button("LOCK IN PROPHECY"):
        if not oracle_name:
            st.error("Identity required to secure prophecy.")
        elif user_order is None:
            st.error("Please re-order at least one team to initialize the system.")
        else:
            # We have the list from the component!
            new_row = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Oracle Name": oracle_name,
                "Rankings": ", ".join(user_order)
            }])
            updated_df = pd.concat([subs_df, new_row], ignore_index=True)
            conn.update(worksheet="Submissions", data=updated_df)
            st.success(f"Prophecy Secure. Good luck, {oracle_name}!")
            st.cache_data.clear()

with tab2:
    st.header("🏆 Leaderboard")
    if not subs_df.empty:
        latest = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        lb_list = []
        for _, row in latest.iterrows():
            preds = row["Rankings"].split(", ")
            score, bullseyes = 0, 0
            if not res_df.empty:
                for rank, team in enumerate(preds, 1):
                    match = res_df[res_df["Team"] == team]
                    if not match.empty:
                        actual = int(match.iloc[0]["Rank"])
                        if actual > 0:
                            dist = abs(rank - actual)
                            mult = 4 if rank==1 else (3 if rank==2 else (2 if rank in [3,4] else 1))
                            score += (dist * mult)
                            if dist == 0: bullseyes += 1
            lb_list.append({"Oracle": row["Oracle Name"], "Penalty": score, "Bullseyes": bullseyes})
        st.table(pd.DataFrame(lb_list).sort_values(["Penalty", "Bullseyes"], ascending=[True, False]))

with tab3:
    st.header("📊 Matrix")
    if not subs_df.empty:
        m_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_rows = []
        for _, row in m_subs.iterrows():
            r = row["Rankings"].split(", ")
            e = {"Oracle": row["Oracle Name"]}
            for i, t in enumerate(r): e[f"#{i+1}"] = t
            m_rows.append(e)
        st.dataframe(pd.DataFrame(m_rows))

with tab4:
    st.header("📜 Scoring Protocol")
    st.markdown("""
    ### 1. High-Stakes Multipliers
    Your penalty points are multiplied based on how high you ranked the team:
    - **Predicted 1st:** 4x Multiplier
    - **Predicted 2nd:** 3x Multiplier
    - **Predicted 3rd - 4th:** 2x Multiplier
    - **Predicted 5th - 16th:** 1x Multiplier (Standard)
    
    ### 2. Fixed vs. Projected
    - **Fixed:** The team's final rank is set (they are eliminated).
    - **Projected:** While a team is alive, we calculate the *best possible outcome* (minimum penalty) they can currently achieve.
    
    ### 3. Tie-Breakers
    1. **Bullseyes:** Total number of exact rank matches.
    2. **Top Tier Accuracy:** Lowest penalty points within your predicted Top 4.
    """)
