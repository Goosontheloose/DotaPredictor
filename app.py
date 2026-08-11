import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="AEGIS ORACLE: SHANGHAI 2026", layout="centered")

# THE EXACT 16 TEAMS
TEAMS = [
    "Falcons", "LGD", "Iron Wing", "Nigma",
    "BoomBoys", "OG", "Team Vision", "Resilience",
    "Spirit", "Xtreme", "Liquid", "Vigi",
    "Aurora", "GamerLegion", "Yandex", "Huligani"
]

GITHUB_BASE = "https://raw.githubusercontent.com/RubenFr87/DotaPredictor/main/"

# --- DATABASE CONNECTION ---
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

# --- CUSTOM UNIFIED DRAGGABLE COMPONENT ---
def unified_oracle_ranker(team_list):
    items_html = ""
    for i, team in enumerate(team_list):
        logo_url = f"{GITHUB_BASE}{team.replace(' ', '%20')}.png"
        items_html += f"""
            <div class="oracle-card" data-id="{team}">
                <div class="rank-box">#<span class="num">{i+1}</span></div>
                <img src="{logo_url}" onerror="this.src='{GITHUB_BASE}Aegis.png'">
                <div class="team-label">{team}</div>
                <div class="handle">⋮⋮</div>
            </div>
        """

    html_code = f"""
        <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
        <style>
            body {{ margin: 0; font-family: -apple-system, system-ui, sans-serif; }}
            .container {{ padding: 10px; background: #fcfcfc; }}
            .oracle-card {{
                display: flex; align-items: center; padding: 12px 16px;
                background: white; border: 1px solid #d0d7de; border-radius: 8px;
                margin-bottom: 8px; cursor: grab; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }}
            .rank-box {{
                background: #f6f8fa; color: #57606a; font-weight: bold;
                padding: 4px 8px; border-radius: 4px; margin-right: 15px;
                min-width: 35px; text-align: center; border: 1px solid #d0d7de;
            }}
            img {{ width: 28px; height: 28px; margin-right: 15px; object-fit: contain; }}
            .team-label {{ font-weight: 600; color: #24292f; flex-grow: 1; }}
            .handle {{ color: #d0d7de; font-size: 18px; }}
            .sortable-ghost {{ opacity: 0.3; background: #f0f7ff; }}
        </style>
        
        <div id="oracleList" class="container">
            {items_html}
        </div>

        <script>
            var el = document.getElementById('oracleList');
            var sortable = Sortable.create(el, {{
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: function () {{
                    var order = [];
                    var items = el.querySelectorAll('.oracle-card');
                    items.forEach(function(item, index) {{
                        order.push(item.getAttribute('data-id'));
                        item.querySelector('.num').innerText = index + 1;
                    }});
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: order
                    }}, '*');
                }}
            }});
            // Initial send
            var initialOrder = {team_list};
            window.parent.postMessage({{type: 'streamlit:setComponentValue', value: initialOrder}}, '*');
        </script>
    """
    return components.html(html_code, height=900)

# --- UI LAYOUT ---
st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <img src="{GITHUB_BASE}Aegis.png" width="80">
        <h1 style="margin-top: 10px; color: #1a1a1a;">AEGIS ORACLE: SHANGHAI 2026</h1>
    </div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["LOCK IN", "LEADERBOARD", "MATRIX", "PROTOCOL"])

with tab1:
    st.markdown("### 🔮 Rank Your Prophecy")
    st.caption("Drag the teams to set your 1st through 16th place predictions.")
    
    # This single component replaces the two columns
    user_order = unified_oracle_ranker(TEAMS)
    
    st.divider()
    oracle_name = st.text_input("Oracle Name", placeholder="e.g. Frederik")
    
    if st.button("LOCK IN PROPHECY"):
        if not oracle_name:
            st.error("Please enter a name.")
        elif user_order is None:
            st.error("Please move one team to confirm the order.")
        else:
            new_row = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Oracle Name": oracle_name,
                "Rankings": ", ".join(user_order)
            }])
            updated_df = pd.concat([subs_df, new_row], ignore_index=True)
            conn.update(worksheet="Submissions", data=updated_df)
            st.success(f"Prophecy recorded for {oracle_name}!")
            st.cache_data.clear()

with tab2:
    st.header("🏆 Leaderboard")
    if not subs_df.empty:
        latest = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        lb = []
        for _, row in latest.iterrows():
            preds = row["Rankings"].split(", ")
            score, hits = 0, 0
            if not res_df.empty:
                for rank, team in enumerate(preds, 1):
                    match = res_df[res_df["Team"] == team]
                    if not match.empty:
                        act = int(match.iloc[0]["Rank"])
                        if act > 0:
                            dist = abs(rank - act)
                            m = 4 if rank==1 else (3 if rank==2 else (2 if rank in [3,4] else 1))
                            score += (dist * m)
                            if dist == 0: hits += 1
            lb.append({"Oracle": row["Oracle Name"], "Penalty": score, "Bullseyes": hits})
        st.table(pd.DataFrame(lb).sort_values(["Penalty", "Bullseyes"], ascending=[True, False]))

with tab3:
    st.header("📊 Matrix")
    if not subs_df.empty:
        m_subs = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        m_rows = []
        for _, row in m_subs.iterrows():
            r = row["Rankings"].split(", ")
            entry = {"Oracle": row["Oracle Name"]}
            for i, t in enumerate(r): entry[f"#{i+1}"] = t
            m_rows.append(entry)
        st.dataframe(pd.DataFrame(m_rows))

with tab4:
    st.header("📜 Scoring Protocol")
    st.markdown("""
    ### 1. The Multiplier Tiers
    - **Rank #1:** 4x Penalty
    - **Rank #2:** 3x Penalty
    - **Rank #3-4:** 2x Penalty
    - **Rank #5-16:** 1x Penalty
    
    ### 2. Fixed vs. Projected
    - **Fixed Scores:** Final rank for eliminated teams.
    - **Projected Scores:** Minimum possible penalty for active teams.
    """)
