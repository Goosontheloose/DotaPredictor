import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
from datetime import datetime
import json

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

# --- CUSTOM UNIFIED SORTABLE COMPONENT ---
def unified_ranker(team_list):
    # Prepare the HTML for the draggable cards with logos
    items_html = ""
    for i, team in enumerate(team_list):
        logo_url = f"{GITHUB_BASE}{team.replace(' ', '%20')}.png"
        items_html += f"""
            <div class="sortable-item" data-id="{team}">
                <div class="rank-badge">#{i+1}</div>
                <img src="{logo_url}" onerror="this.src='{GITHUB_BASE}Aegis.png'">
                <div class="team-name">{team}</div>
                <div class="drag-handle">☰</div>
            </div>
        """

    component_html = f"""
        <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent; }}
            .sortable-list {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
            .sortable-item {{
                display: flex; align-items: center; padding: 12px 16px;
                background: white; border: 1px solid #d0d7de; border-radius: 8px;
                margin-bottom: 8px; cursor: grab; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                transition: border-color 0.2s;
            }}
            .sortable-item:hover {{ border-color: #0969da; }}
            .rank-badge {{
                background: #f6f8fa; color: #57606a; font-weight: bold;
                padding: 4px 8px; border-radius: 4px; margin-right: 15px;
                min-width: 35px; text-align: center; border: 1px solid #d0d7de; font-size: 14px;
            }}
            img {{ width: 28px; height: 28px; margin-right: 15px; object-fit: contain; }}
            .team-name {{ font-weight: 600; color: #24292f; flex-grow: 1; font-size: 16px; }}
            .drag-handle {{ color: #d0d7de; font-size: 18px; cursor: ns-resize; }}
            .sortable-ghost {{ opacity: 0.3; background: #f0f7ff; }}
        </style>
        
        <div id="simpleList" class="sortable-list">
            {items_html}
        </div>

        <script>
            var el = document.getElementById('simpleList');
            var sortable = Sortable.create(el, {{
                animation: 150,
                ghostClass: 'sortable-ghost',
                onEnd: function (evt) {{
                    var order = [];
                    var items = el.querySelectorAll('.sortable-item');
                    items.forEach(function(item, index) {{
                        order.push(item.getAttribute('data-id'));
                        item.querySelector('.rank-badge').innerText = '#' + (index + 1);
                    }});
                    // Send final order to Streamlit
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: order
                    }}, '*');
                }}
            }});
        </script>
    """
    # Use a tall enough container to show all 16 teams without scrolling issues
    return components.html(component_html, height=1000)

# --- APP LAYOUT ---
tab1, tab2, tab3, tab4 = st.tabs(["LOCK IN", "LEADERBOARD", "MATRIX", "PROTOCOL"])

with tab1:
    st.header("🔮 Prophecy Lock-In")
    st.caption("Drag and drop the cards to set your predicted finishing order.")
    
    # Render the unified draggable list with logos
    user_order = unified_ranker(TEAMS)
    
    # Capturing the state from the component
    # Since components.html is asynchronous, we provide a fallback name input
    st.divider()
    oracle_name = st.text_input("Oracle Name", placeholder="Enter your handle...")
    
    if st.button("LOCK IN PROPHECY"):
        if not oracle_name:
            st.error("Identification required.")
        elif user_order is None:
             st.error("Please move at least one team to initialize the order.")
        else:
            new_data = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Oracle Name": oracle_name,
                "Rankings": ", ".join(user_order)
            }])
            updated_df = pd.concat([subs_df, new_data], ignore_index=True)
            conn.update(worksheet="Submissions", data=updated_df)
            st.success(f"Prophecy Secured, {oracle_name}!")
            st.cache_data.clear()

with tab2:
    st.header("🏆 Live Standings")
    if subs_df.empty or "Oracle Name" not in subs_df.columns:
        st.info("The vault is empty.")
    else:
        latest = subs_df.sort_values("Timestamp").drop_duplicates("Oracle Name", keep="last")
        lb = []
        for _, row in latest.iterrows():
            p_list = row["Rankings"].split(", ")
            score, hits = 0, 0
            if not res_df.empty:
                for r, t in enumerate(p_list, 1):
                    match = res_df[res_df["Team"] == t]
                    if not match.empty:
                        act = int(match.iloc[0]["Rank"])
                        if act > 0:
                            dist = abs(r - act)
                            m = 4 if r==1 else (3 if r==2 else (2 if r in [3,4] else 1))
                            score += (dist * m)
                            if dist == 0: hits += 1
            lb.append({"Oracle": row["Oracle Name"], "Penalty": score, "Bullseyes": hits})
        st.table(pd.DataFrame(lb).sort_values(["Penalty", "Bullseyes"], ascending=[True, False]))

with tab3:
    st.header("📊 Comparison Matrix")
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
    - **Rank #1 Pick:** 4x Penalty (Highest Stakes)
    - **Rank #2 Pick:** 3x Penalty
    - **Rank #3-4 Pick:** 2x Penalty
    - **Rank #5-16 Pick:** 1x Penalty (Base Stakes)
    
    ### 2. Fixed vs. Projected Scoring
    - **Fixed Scores:** Finalized once a team is eliminated and their rank is locked.
    - **Projected Scores:** While teams are active, we calculate the minimum possible penalty based on their current upper-bracket potential.
    
    ### 3. Tie-Breakers
    1. **Perfect Picks:** Total exact rank matches (Bullseyes).
    2. **Top-Heavy Accuracy:** Lowest penalty within the Top 4 prediction.
    """)
