import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items

# --- MOBILE-OPTIMIZED CONFIG & THEME ---
st.set_page_config(page_title="AEGIS ORACLE", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Mobile-First Typography */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #ffffff;
        color: #1f2328;
    }
    
    /* Increase font size for mobile readability */
    p, li, b, i, span, label {
        font-size: 1.1rem !important;
    }

    /* Stack everything vertically for narrow screens */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 calc(100% - 1rem) !important;
    }

    /* Professional Card Styling */
    .protocol-card { 
        background: #f6f8fa !important; 
        padding: 18px; 
        border-radius: 12px; 
        border: 1px solid #d0d7de;
        border-left: 8px solid #0969da !important; 
        margin-bottom: 15px;
    }
    
    /* Big Touch-Friendly Buttons */
    .stButton>button {
        width: 100% !important;
        height: 3.5rem !important;
        background-color: #2da44e !important;
        color: white !important;
        font-size: 1.2rem !important;
        border-radius: 10px !important;
        font-weight: 700;
        margin-top: 10px;
    }

    /* Team List Item Styling */
    .preview-row {
        padding: 12px;
        border-bottom: 1px solid #f0f0f0;
        display: flex;
        align-items: center;
        font-size: 1.1rem;
    }

    .multiplier-tag { background: #dafbe1; color: #1a7f37; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; font-weight: bold; }
    .bonus-tag { background: #fff8c5; color: #9a6700; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; font-weight: bold; }
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
        
        # Bullseye Logic (-1 base for perfect)
        if pr == ar:
            base = -1
            perfect_count += 1
        else:
            base = abs(pr - ar)
        
        mult = 4 if pr == 1 else 3 if pr == 2 else 2 if pr in [3, 4] else 1
        pts = base * mult
        p_score += pts
        if status_map.get(team) in ["Eliminated", "Winner"]: f_score += pts
        
    return f_score, p_score, perfect_count

# --- APP FLOW ---
res, subs, logo_map = load_oracle_data()
teams_list = ["Team Liquid", "Gaimin Gladiators", "Tundra Esports", "Team Falcons", "Xtreme Gaming", "Cloud9", "BetBoom Team", "Aurora", "Nouns", "Team Spirit", "HEROIC", "PSG Quest", "Team Zero", "1win", "MOUZ", "Talon Esports"]

st.title("🏆 AEGIS ORACLE 2026")
tabs = st.tabs(["🔮 PICK", "📊 RANKS", "📑 MATRIX", "📜 RULES"])

with tabs[0]:
    o_name = st.text_input("ORACLE NAME", placeholder="Enter Name")
    st.info("Drag teams to rank them (1 to 16)")
    sorted_ranks = sort_items(teams_list, direction='vertical')
    
    if st.button("LOCK IN PREDICTIONS"):
        if o_name and save_prediction(o_name, sorted_ranks):
            st.success("Prophecy Recorded!")
            st.balloons()
        else:
            st.error("Name required / Connection error.")

    st.subheader("Your Current Order")
    for i, t in enumerate(sorted_ranks):
        img = logo_map.get(t, "https://img.icons8.com/ios-filled/50/0969DA/shield.png")
        st.markdown(f"""<div class='preview-row'><b>{i+1}.</b> &nbsp; <img src='{img}' width='24' style='margin-right:10px;'> {t}</div>""", unsafe_allow_html=True)

with tabs[1]:
    if res is not None:
        st.subheader("Leaderboard")
        rows = []
        if subs is not None:
            for _, r in subs.iterrows():
                f, p, bull = get_score_metrics(r['Rankings'].split(','), res)
                rows.append({"Oracle": r['Oracle Name'], "Perfect": bull, "Fixed": f, "Projected": p})
            
            # Sorted by Projected (Lower is better)
            df_lb = pd.DataFrame(rows).sort_values("Projected")
            st.dataframe(df_lb, use_container_width=True, hide_index=True)

with tabs[2]:
    if subs is not None:
        m_data = {r['Oracle Name']: r['Rankings'].split(',') for _, r in subs.iterrows()}
        st.dataframe(pd.DataFrame(m_data, index=[f"Rank {i+1}" for i in range(16)]), use_container_width=True)

with tabs[3]:
    st.markdown(f"""
    <div class='protocol-card'>
        <h3>🎯 The Bullseye</h3>
        <p>Correct rank = <b>-1 base point</b>.</p>
        <p>Correct #1 Pick = <span class='bonus-tag'>-4 TOTAL</span></p>
    </div>
    <div class='protocol-card'>
        <h3>⛳ Golf Scoring</h3>
        <p>Misses = Distance × Multiplier.</p>
        <p>1st (4x), 2nd (3x), 3/4th (2x).</p>
        <p><b>Lowest Score Wins.</b></p>
    </div>
    """, unsafe_allow_html=True)
