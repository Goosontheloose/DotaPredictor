import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items

# --- MOBILE-OPTIMIZED CONFIG & THEME ---
st.set_page_config(page_title="AEGIS ORACLE", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #ffffff;
        color: #1f2328;
    }
    
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }

    /* Rules Styling */
    .rules-header { 
        color: #0969da; 
        border-bottom: 2px solid #eaecef; 
        padding-bottom: 10px; 
        margin-top: 25px;
        font-weight: 800;
    }
    .rules-card { 
        background: #f6f8fa; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #d0d7de; 
        margin-top: 10px;
    }
    .math-box {
        font-family: monospace;
        background: #fff8c5;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #f7e0a3;
        font-weight: bold;
    }
    .stButton>button {
        width: 100% !important;
        height: 3.5rem !important;
        background-color: #2da44e !important;
        color: white !important;
        font-size: 1.1rem !important;
        border-radius: 10px !important;
        font-weight: 700;
    }
    .preview-row {
        padding: 10px;
        border-bottom: 1px solid #f0f0f0;
        display: flex;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=300)
def load_oracle_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        results = conn.read(worksheet="Results", ttl=0)
        submissions = conn.read(worksheet="Submissions", ttl=0)
        try:
            logos = conn.read(worksheet="Logos", ttl=0)
            logo_map = dict(zip(logos['Team'], logos['LogoURL']))
        except: logo_map = {}
        return results, submissions, logo_map
    except: return None, None, {}

def save_prediction(name, rankings_list):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing = conn.read(worksheet="Submissions", ttl=0)
        new_row = pd.DataFrame([{"Timestamp": datetime.now().strftime("%y-%m-%d %H:%M"), "Oracle Name": name, "Rankings": ",".join(rankings_list)}])
        updated = pd.concat([existing, new_row], ignore_index=True)
        conn.update(worksheet="Submissions", data=updated)
        st.cache_data.clear()
        return True
    except: return False

def get_score_metrics(pred_list, res_df):
    if res_df is None or res_df.empty: return 0, 0, 0
    f_score, p_score, perfect_count = 0, 0, 0
    actual_map = dict(zip(res_df['Team'], res_df['Rank']))
    status_map = dict(zip(res_df['Team'], res_df.get('Status', ['In-Play']*len(res_df))))
    
    for i, team in enumerate(pred_list):
        pr = i + 1
        ar = actual_map.get(team, 0)
        if ar == 0: continue
        
        base = -1 if pr == ar else abs(pr - ar)
        if pr == ar: perfect_count += 1
        
        mult = 4 if pr == 1 else 3 if pr == 2 else 2 if pr in [3, 4] else 1
        pts = base * mult
        p_score += pts
        if status_map.get(team) in ["Eliminated", "Winner"]: f_score += pts
        
    return f_score, p_score, perfect_count

# --- APP LAYOUT ---
res, subs, logo_map = load_oracle_data()
teams_list = ["Team Liquid", "Gaimin Gladiators", "Tundra Esports", "Team Falcons", "Xtreme Gaming", "Cloud9", "BetBoom Team", "Aurora", "Nouns", "Team Spirit", "HEROIC", "PSG Quest", "Team Zero", "1win", "MOUZ", "Talon Esports"]

st.title("🏆 AEGIS ORACLE")
tabs = st.tabs(["🔮 PICK", "📊 RANKS", "📑 MATRIX", "📜 RULES"])

with tabs[0]:
    o_name = st.text_input("ORACLE NAME")
    sorted_ranks = sort_items(teams_list, direction='vertical')
    if st.button("LOCK IN PREDICTIONS"):
        if o_name and save_prediction(o_name, sorted_ranks):
            st.success("Locked!")
            st.balloons()

    st.subheader("Current Selection")
    for i, t in enumerate(sorted_ranks):
        img = logo_map.get(t, "https://img.icons8.com/ios-filled/50/0969DA/shield.png")
        st.markdown(f"""<div class='preview-row'><b>{i+1}.</b> &nbsp; <img src='{img}' width='24'> &nbsp; {t}</div>""", unsafe_allow_html=True)

with tabs[1]:
    if res is not None and subs is not None:
        rows = []
        for _, r in subs.iterrows():
            f, p, bull = get_score_metrics(r['Rankings'].split(','), res)
            rows.append({"Oracle": r['Oracle Name'], "Bullseyes": bull, "Fixed": f, "Projected": p})
        st.dataframe(pd.DataFrame(rows).sort_values("Projected"), use_container_width=True, hide_index=True)

with tabs[2]:
    if subs is not None:
        m_data = {r['Oracle Name']: r['Rankings'].split(',') for _, r in subs.iterrows()}
        st.dataframe(pd.DataFrame(m_data, index=[f"Rank {i+1}" for i in range(16)]), use_container_width=True)

with tabs[3]:
    st.markdown("<h2 class='rules-header'>1. SCORING SYSTEM</h2>", unsafe_allow_html=True)
    st.write("This is a **Golf-Style** tournament: The lower your score, the better your rank.")
    
    st.markdown("<div class='rules-card'><b>🎯 THE BULLSEYE:</b><br>If a team finishes exactly where you predicted, you receive <b>-1 Base Point</b>.</div>", unsafe_allow_html=True)
    st.markdown("<div class='rules-card'><b>⛳ THE PENALTY:</b><br>If a team finishes elsewhere, you receive points equal to the <b>Absolute Distance</b> between your prediction and reality.</div>", unsafe_allow_html=True)

    st.markdown("<h2 class='rules-header'>2. MULTIPLIERS</h2>", unsafe_allow_html=True)
    st.write("The higher the rank you predict, the higher the stakes.")
    st.table(pd.DataFrame({
        "Predicted Rank": ["1st", "2nd", "3rd - 4th", "5th - 16th"],
        "Multiplier": ["4x", "3x", "2x", "1x"]
    }))

    st.markdown("<h2 class='rules-header'>3. FIXED VS PROJECTED</h2>", unsafe_allow_html=True)
    st.markdown("""
    - **PROJECTED SCORE:** This is your 'Live' score. It treats every team's current standing as if the tournament ended right now.
    - **FIXED SCORE:** This only counts points from teams that have been **officially eliminated** or declared the **winner**. This score will not change once a team is out.
    - **BULLSEYES:** A count of how many teams you predicted perfectly.
    """)

    st.markdown("<h2 class='rules-header'>4. EXAMPLE CALCULATION</h2>", unsafe_allow_html=True)
    st.markdown("<div class='math-box'>Prediction: Team Spirit (1st) | Result: 3rd<br>Distance: 2 (1 to 3) | Multiplier: 4x<br>Total Penalty: 8 Points</div>", unsafe_allow_html=True)
