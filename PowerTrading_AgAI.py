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

# Hardcode your key here OR use the Sidebar input (easier for demos)
# PERPLEXITY_API_KEY = "pplx-xxxxxxxx" 

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
        
        # Build Graph (We rebuild it inside to pass the client if needed, or just keep it simple)
        # For simplicity, we call functions directly here to show progress bars clearly
        # (In a huge app, you'd use LangGraph invoke, but for Streamlit demo, explicit steps look cooler)
        
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





# import os
# import yfinance as yf
# from openai import OpenAI
# from typing import TypedDict
# from langgraph.graph import StateGraph, END

# # --- CONFIGURATION ---
# # Replace with your actual Perplexity API Key
# PERPLEXITY_API_KEY = 

# # Initialize the Client (We use OpenAI SDK but point it to Perplexity)
# client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

# # --- 1. DEFINE THE STATE ---
# # This dictionary is the "Folder" that gets passed between agents
# class AgentState(TypedDict):
#     company_symbol: str
#     company_name: str
#     price_data: str
#     news_summary: str
#     final_recommendation: str

# # --- 2. DEFINE THE TOOLS (AGENTS) ---

# def market_data_agent(state: AgentState):
#     """Fetches numerical stock data from Yahoo Finance"""
#     print(f"\n[1] Market Agent: Fetching data for {state['company_name']}...")
    
#     try:
#         ticker = yf.Ticker(state['company_symbol'])
#         # Get last 5 days of data
#         hist = ticker.history(period="5d")
#         current_price = hist['Close'].iloc[-1]
#         start_price = hist['Close'].iloc[0]
#         change = ((current_price - start_price) / start_price) * 100
        
#         data_str = f"Current Price: {current_price:.2f} INR. 5-Day Change: {change:.2f}%"
#         print(f"    -> Data Found: {data_str}")
#         return {"price_data": data_str}
        
#     except Exception as e:
#         return {"price_data": "Error fetching price data."}

# def research_agent(state: AgentState):
#     """Uses Perplexity to find reasons BEHIND the price"""
#     print(f"\n[2] Research Agent: Reading news via Perplexity...")
    
#     # We ask Perplexity specifically about Energy Market drivers
#     query = f"Latest news affecting {state['company_name']} share price in India. Focus on coal supply, government energy policy, and renewable projects. Be concise."
    
#     messages = [
#         {"role": "system", "content": "You are a senior energy market researcher. Summarize key drivers in 3 bullet points."},
#         {"role": "user", "content": query}
#     ]
    
#     # Call Perplexity API (sonar-pro is excellent for searching)
#     response = client.chat.completions.create(
#         model="sonar-pro", 
#         messages=messages,
#     )
    
#     news = response.choices[0].message.content
#     print(f"    -> News Found: {news[:100]}...") # Print first 100 chars
#     return {"news_summary": news}

# def trader_agent(state: AgentState):
#     """The Boss: Decides Charge/Discharge based on Grid Price + News"""
#     print(f"\n[3] Energy Dispatcher: Optimizing Battery Strategy...")
    
#     # We pretend the 'price_data' is the Electricity Spot Price (₹/kWh)
#     # And we assume we have a Battery System.
    
#     prompt = f"""
#     You are an AI Operator for a Grid-Connected Battery Storage System (BESS).
    
#     CURRENT GRID SCENARIO:
#     - Market Price Data: {state['price_data']} (Treat this as ₹/kWh if using simulated data, or general trend)
#     - Grid News/Context: {state['news_summary']}
    
#     DECISION RULES:
#     1. CHARGE: If prices are low and supply is stable.
#     2. DISCHARGE (SELL): If prices are peaking or news indicates supply crunch (Coal shortage/Heatwave).
#     3. HOLD: If markets are flat or uncertain.
    
#     Task: Decide CHARGE, DISCHARGE, or HOLD.
#     Explain WHY based on the news (e.g., "Heatwave incoming, expect peak prices later, so HOLD charge now").
#     """
    
#     messages = [{"role": "user", "content": prompt}]
    
#     response = client.chat.completions.create(
#         model="sonar-pro", 
#         messages=messages,
#     )
    
#     decision = response.choices[0].message.content
#     return {"final_recommendation": decision}
# # def trader_agent(state: AgentState):
# #     """The Boss: Decides Buy/Sell/Hold based on Data + News"""
# #     print(f"\n[3] Trader Agent: Analyzing signals...")
    
# #     prompt = f"""
# #     You are a Power Trader at a top firm like Trafigura.
    
# #     ASSET: {state['company_name']}
# #     MARKET DATA: {state['price_data']}
# #     NEWS INTEL: {state['news_summary']}
    
# #     Task: Decide BUY, SELL, or HOLD.
# #     Provide a professional reasoning (max 50 words) linking the News to the Price.
# #     """
    
# #     messages = [{"role": "user", "content": prompt}]
    
# #     # --- CHANGED MODEL HERE ---
# #     response = client.chat.completions.create(
# #         model="sonar-pro",  # Changed from 'sonar-reasoning' to 'sonar-pro'
# #         messages=messages,
# #     )
    
# #     decision = response.choices[0].message.content
# #     return {"final_recommendation": decision}

# # --- 3. BUILD THE GRAPH ---
# workflow = StateGraph(AgentState)

# # Add Nodes
# workflow.add_node("get_data", market_data_agent)
# workflow.add_node("get_news", research_agent)
# workflow.add_node("make_trade", trader_agent)

# # Add Edges (Linear Logic)
# workflow.set_entry_point("get_data")
# workflow.add_edge("get_data", "get_news")
# workflow.add_edge("get_news", "make_trade")
# workflow.add_edge("make_trade", END)

# # Compile
# app = workflow.compile()

# # --- 4. RUN THE SYSTEM ---
# if __name__ == "__main__":
#     # Test with Tata Power (Use .NS for NSE)
#     inputs = {"company_symbol": "TATAPOWER.NS", "company_name": "Tata Power"}
    
#     result = app.invoke(inputs)
    
#     print("\n" + "="*50)
#     print("FINAL TRADING SIGNAL")
#     print("="*50)
#     print(result['final_recommendation'])
#     print("="*50)