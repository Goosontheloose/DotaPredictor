import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from streamlit_sortables import sort_items
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Aegis Oracle: TI 2026", layout="wide")

# Shanghai Shadow-Tech Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesque:wght@700&family=JetBrains+Mono&display=swap');
    
    .main { background-color: #050507; color: #ffffff; }
    h1, h2 { font-family: 'Space Grotesque', sans-serif; color: #FF003C; text-transform: uppercase; letter-spacing: 2px; }
    .stMarkdown { font-family: 'JetBrains Mono', monospace; }
    
    /* Glassmorphism Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 245, 255, 0.3);
        border-radius: 10px;
        padding: 20px;
        backdrop-filter: blur(10px);
    }
    
    .stButton>button {
        background: linear-gradient(45deg, #FF003C, #00F5FF);
        color: white; border: none; font-weight: bold; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CORE DATA ---
TEAMS = [
    "Team Spirit", "Parivision", "Team Liquid", "Betboom Team", 
    "Team Falcons", "Tundra Esports", "Team Tidebound", "Aurora", 
    "Yakutou", "Nigma Galaxy", "Navi", "Xtreme Gaming", 
    "Heroic", "Wildcard Gaming", "Boom Esports", "Team Nemesis"
]

# --- GOOGLE SHEETS CONNECTION ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"⚠️ Connection Protocol Failed: {e}")
    st.stop()

# --- FUNCTIONS ---
def get_live_results():
    """Fetches the official standings from the 'Results' tab."""
    try:
        df = conn.read(worksheet="Results", ttl="1s")
        return dict(zip(df['Team Name'], df['Official Rank']))
    except:
        return {team: 0 for team in TEAMS} # Fallback if empty

def calculate_score(predictions, results):
    """Golf Scoring: ABS(Pred - Result) * Multiplier. Lower is better."""
    total = 0
    breakdown = []
    
    for i, team in enumerate(predictions):
        pred_rank = i + 1
        actual_rank = results.get(team, 0)
        
        # Multipliers for Top 3
        multiplier = 4 if pred_rank == 1 else (3 if pred_rank == 2 else (2 if pred_rank <= 4 else 1))
        
        # Only score if team has an official result (non-zero)
        if actual_rank > 0:
            gap = abs(pred_rank - actual_rank)
            weighted_gap = gap * multiplier
            total += weighted_gap
            breakdown.append({"Team": team, "Pred": pred_rank, "Actual": actual_rank, "Pts": weighted_gap})
        else:
            breakdown.append({"Team": team, "Pred": pred_rank, "Actual": "Active", "Pts": 0})
            
    return total, pd.DataFrame(breakdown)

# --- UI LAYOUT ---
st.title("🏮 Aegis Oracle: TI 2026 Shanghai")
tabs = st.tabs(["🏆 Leaderboard", "🔮 Lock Predictions", "🛠 Arbiter Console"])

# --- TAB 1: LEADERBOARD ---
with tabs[0]:
    st.subheader("Prophetic Hierarchy")
    official_results = get_live_results()
    
    try:
        submissions = conn.read(worksheet="Submissions", ttl="1s")
        if not submissions.empty:
            leaderboard_data = []
            for _, row in submissions.iterrows():
                pred_list = row['Rankings'].split(", ")
                score, _ = calculate_score(pred_list, official_results)
                leaderboard_data.append({"Oracle": row['Oracle Name'], "Total Points": score})
            
            lb_df = pd.DataFrame(leaderboard_data).sort_values("Total Points")
            st.table(lb_df)
            
            # Detailed View for specific Oracle
            selected_oracle = st.selectbox("Inspect Oracle Details", lb_df['Oracle'])
            user_preds = submissions[submissions['Oracle Name'] == selected_oracle]['Rankings'].iloc[0].split(", ")
            _, detail_df = calculate_score(user_preds, official_results)
            st.dataframe(detail_df, use_container_width=True)
    except:
        st.info("No prophecies recorded yet. Be the first to lock yours in.")

# --- TAB 2: PREDICTIONS ---
with tabs[1]:
    st.subheader("The Arena: Rank Your Teams")
    oracle_name = st.text_input("Enter your Oracle Name (e.g., Ruben, Stok, Frederik)")
    
    st.write("Drag and drop to rank (Top = 1st Place / 4x Multiplier)")
    ranked_list = sort_items(TEAMS, direction='vertical')
    
    if st.button("Lock in Predictions"):
        if not oracle_name:
            st.warning("You must provide an Oracle Name to bind your destiny.")
        else:
            # Prepare data
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rank_string = ", ".join(ranked_list)
            new_data = pd.DataFrame([[timestamp, oracle_name, rank_string]], 
                                    columns=["Timestamp", "Oracle Name", "Rankings"])
            
            try:
                # Append to Google Sheet
                existing_data = conn.read(worksheet="Submissions")
                updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                conn.update(worksheet="Submissions", data=updated_df)
                st.success(f"Prophecy Locked, {oracle_name}. Your fate is sealed.")
            except Exception as e:
                st.error(f"Transmission Failed: {e}")

# --- TAB 3: ADMIN ---
with tabs[2]:
    st.subheader("Grand Arbiter Terminal")
    st.write("Current Official Standings (Stored in 'Results' tab):")
    st.json(official_results)
    
    st.info("""
    **Arbiter Instructions:**
    1. Open the 'TI_2026' Google Sheet.
    2. In the 'Results' tab, enter the team name and their final rank.
    3. For ties (5th-6th), enter **5**. For (7th-8th), enter **7**.
    4. The leaderboard will update automatically on refresh.
    """)
