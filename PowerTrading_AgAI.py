import streamlit as st
import yfinance as yf
from openai import OpenAI
from typing import TypedDict
from langgraph.graph import StateGraph, END
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Energy Market AI Agent", page_icon="⚡", layout="wide")

# --- CSS FOR STYLING ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
    }
    .report-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        border: 1px solid #d6d6d6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. SETUP & STATE ---
 
class AgentState(TypedDict):
    company_symbol: str
    company_name: str
    price_data: str
    news_summary: str
    final_recommendation: str

# --- 2. DEFINE AGENT FUNCTIONS (BACKEND) ---

def market_data_agent(state: AgentState):
    """Fetches numerical stock data"""
    ticker = yf.Ticker(state['company_symbol'])
    try:
        hist = ticker.history(period="5d")
        current_price = hist['Close'].iloc[-1]
        start_price = hist['Close'].iloc[0]
        change = ((current_price - start_price) / start_price) * 100
        data_str = f"Price: ₹{current_price:.2f} | 5-Day Change: {change:.2f}%"
        return {"price_data": data_str}
    except:
        return {"price_data": "Error fetching data (Check Ticker Symbol)"}

def research_agent(state: AgentState, client):
    """Uses Perplexity to find news"""
    query = f"Latest news affecting {state['company_name']} share price in India. Focus on coal supply, government energy policy, and renewable projects. Be concise."
    messages = [
        {"role": "system", "content": "You are a senior energy market researcher. Summarize key drivers in 3 bullet points."},
        {"role": "user", "content": query}
    ]
    response = client.chat.completions.create(model="sonar-pro", messages=messages)
    return {"news_summary": response.choices[0].message.content}

def trader_agent(state: AgentState, client):
    """The Boss: Decides Strategy"""
    prompt = f"""
    You are an AI Operator for a Grid-Connected Battery Storage System.
    
    ASSET: {state['company_name']}
    MARKET DATA: {state['price_data']}
    NEWS INTEL: {state['news_summary']}
    
    DECISION RULES:
    1. CHARGE: Low price/stable supply.
    2. DISCHARGE: High price/supply crunch.
    3. HOLD: Uncertain/Wait for event.
    
    Task: Decide CHARGE, DISCHARGE, or HOLD.
    Start with the decision in BOLD (e.g., **CHARGE**). Then explain in 1 short paragraph.
    """
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(model="sonar-pro", messages=messages)
    return {"final_recommendation": response.choices[0].message.content}

# --- 3. STREAMLIT FRONTEND ---

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Perplexity API Key", type="password", placeholder="pplx-...")
    st.info("Get key from perplexity.ai/settings/api")
    st.markdown("---")
    st.markdown("**Role:** Energy Analyst Agent")
    st.markdown("**Tech:** LangGraph + Perplexity")

# Main Title
st.title("⚡ Autonomous Energy Trading Desk")
st.markdown("### AI-Powered Market Surveillance System")

# Input Section
col1, col2 = st.columns([3, 1])
with col1:
    company_name = st.text_input("Company Name", value="Tata Power")
with col2:
    ticker_symbol = st.text_input("Ticker (NSE)", value="TATAPOWER.NS")

run_btn = st.button("🚀 Initialize Trading Agent")

# --- 4. EXECUTION LOGIC ---

if run_btn:
    if not api_key:
        st.error("Please enter your API Key in the sidebar!")
    else:
        # Initialize Client
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        
        state = {"company_symbol": ticker_symbol, "company_name": company_name}
        
        # UI Container for the Process
        with st.status("🤖 AI Agents Active...", expanded=True) as status:
            
            # Step 1: Market Data
            st.write("Fetching Market Data...")
            data_result = market_data_agent(state)
            state.update(data_result)
            st.success(f"Market Data Acquired: {state['price_data']}")
            time.sleep(1) # Fake delay for dramatic effect
            
            # Step 2: Research
            st.write("running Semantic Search on News (Perplexity)...")
            news_result = research_agent(state, client)
            state.update(news_result)
            st.info("News Context Indexed.")
            
            # Step 3: Decision
            st.write("Generating Trading Strategy...")
            trade_result = trader_agent(state, client)
            state.update(trade_result)
            
            status.update(label="Analysis Complete!", state="complete", expanded=False)

        # --- 5. FINAL REPORT DISPLAY ---
        
        st.divider()
        
        # 3-Column Layout for Data
        m1, m2, m3 = st.columns(3)
        m1.metric("Asset", state['company_name'])
        # Extract price number for metric (simple string split)
        try:
            price_val = state['price_data'].split("₹")[1].split(" ")[0]
            m2.metric("Current Price", f"₹{price_val}")
        except:
            m2.metric("Current Price", "N/A")
            
        # Color Code the Decision
        rec = state['final_recommendation']
        if "CHARGE" in rec.upper() or "BUY" in rec.upper():
            color = "green"
        elif "DISCHARGE" in rec.upper() or "SELL" in rec.upper():
            color = "red"
        else:
            color = "orange"
            
        st.markdown(f"### 🎯 Final Signal: :{color}[{rec.split('.')[0]}]")
        
        with st.container():
            st.markdown(f"""
            <div class="report-box">
            <h4>Analyst Reasoning:</h4>
            {rec}
            </div>
            """, unsafe_allow_html=True)
            
        with st.expander("See Raw News Source"):
            st.write(state['news_summary'])





