import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load Local Environment keys
load_dotenv()

from monday_api import fetch_board_data
from data_processing import process_data, calculate_metrics
from ai_agent import get_ai_agent, ask_agent, generate_executive_summary

# Monday.com Config
DEALS_BOARD_ID = "5026839660"
WO_BOARD_ID = "5026839625"

st.set_page_config(
    page_title="AI BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply sleek, premium dark-mode styling
st.markdown("""
    <style>
    /* Main Background & Text */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #1E212B, #161A22);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #30363D;
        border-left: 5px solid #00D2FF;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(0, 210, 255, 0.15);
    }
    div[data-testid="stMetric"] label {
        color: #8B949E !important;
        font-weight: 500;
        font-size: 15px;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div {
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 32px;
    }
    /* Headers */
    h1 {
        background: -webkit-linear-gradient(45deg, #00D2FF, #3A7BD5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        letter-spacing: -1px;
    }
    h2, h3 {
        color: #C9D1D9 !important;
        font-weight: 600;
    }
    /* Inputs */
    .stTextInput input {
        border-radius: 10px;
        border: 1px solid #30363D;
        background-color: #161A22;
        color: #FFFFFF;
        padding: 10px 15px;
    }
    .stTextInput input:focus {
        border-color: #00D2FF;
        box-shadow: 0 0 5px rgba(0, 210, 255, 0.5);
    }
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #FF4B2B 0%, #FF416C 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #FF416C 0%, #FF4B2B 100%);
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4);
        transform: scale(1.02);
    }
    /* Expanders & Dividers */
    .stExpander {
        background-color: #161A22;
        border: 1px solid #30363D;
        border-radius: 10px;
    }
    hr {
        border-color: #30363D;
    }
    /* Info / Success boxes */
    div.stAlert {
        border-radius: 10px;
        border: 1px solid #30363D;
        background-color: #1E212B;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 AI Business Intelligence Agent")
st.markdown("**Real-time Insights from Monday.com Work Orders & Deals**")

import concurrent.futures

@st.cache_data(ttl=300) # Cache for 5 mins to prevent API spamming
def load_and_clean_monday_data():
    with st.spinner("Fetching live data from Monday.com GraphQL API concurrently..."):
        # Fetch both boards simultaneously to cut loading time in half
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_deals = executor.submit(fetch_board_data, DEALS_BOARD_ID)
            future_wo = executor.submit(fetch_board_data, WO_BOARD_ID)
            
            deals_raw = future_deals.result()
            wo_raw = future_wo.result()

        deals_clean = process_data(deals_raw, board_type="deals")
        wo_clean = process_data(wo_raw, board_type="work_orders")

        metrics = calculate_metrics(deals_clean, wo_clean)

        return deals_clean, wo_clean, metrics

try:
    deals_df, wo_df, metrics = load_and_clean_monday_data()
except Exception as e:
    st.error(f"Critical error loading data: {str(e)}")
    deals_df, wo_df, metrics = pd.DataFrame(), pd.DataFrame(), {}

# Top Dashboard Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Pipeline Value", f"${metrics.get('Total Pipeline Value', 0):,.2f}")
col2.metric("🎯 Expected Revenue", f"${metrics.get('Expected Revenue', 0):,.2f}")
col3.metric("📋 Work Order Completion", metrics.get('Work Order Completion Rate', '0%'))
col4.metric("👑 Top Sector", metrics.get('Top Sector', 'Unknown'))

st.divider()

# Left Column (Chat) and Right Column (Summary & Data)
main_col, side_col = st.columns([2, 1])

# --- Chat Interface ---
with main_col:
    st.subheader("💬 Ask the AI BI Agent")
    st.markdown("Example questions: *'Which sector generates the highest revenue?'* or *'What is our work order completion rate?'*")
    
    query = st.text_input("Enter your business question:", placeholder="e.g. How is our pipeline looking this quarter?")
    
    if query:
        # Pre-filter large text columns to save huge amounts of tokens
        compact_deals = deals_df.drop(columns=[c for c in deals_df.columns if 'id' in c.lower()], errors='ignore').head(50)
        compact_wo = wo_df.drop(columns=[c for c in wo_df.columns if 'id' in c.lower()], errors='ignore').head(50)
        
        agent = get_ai_agent(compact_deals, compact_wo)
        if agent:
            with st.spinner("🧠 Analyzing Monday.com Data..."):
                answer = ask_agent(agent, query)
                st.info(answer)
        else:
            st.error("Missing Groq API Key. Add GROQ_API_KEY to your Streamlit secrets or local .env file.")

# --- Action Panel ---
with side_col:
    st.subheader("📑 Quick Actions")
    if st.button("🚀 Generate Leadership Summary", type="primary", use_container_width=True):
        st.write("**Executive Summary:**")
        if metrics:
            with st.spinner("Generating executive insights..."):
                summary = generate_executive_summary(metrics)
                if "⚠️" in summary or "🚨" in summary:
                    st.error(summary)
                else:
                    st.success(summary)
        else:
            st.warning("Insufficient data to generate summary.")

st.divider()

# --- Raw Data Review ---
with st.expander("🔍 View Live Processed Data"):
    st.write("### 💼 Deals Pipeline (Cleaned)")
    if not deals_df.empty:
        st.dataframe(deals_df, use_container_width=True)
    else:
        st.warning("No data retrieved from Deals Board.")
        
    st.write("### 🛠️ Work Orders (Cleaned)")
    if not wo_df.empty:
        st.dataframe(wo_df, use_container_width=True)
    else:
        st.warning("No data retrieved from Work Orders Board.")
