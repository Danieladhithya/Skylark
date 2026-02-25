import os
import streamlit as st
from langchain_groq import ChatGroq
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

def get_ai_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")

def get_ai_agent(deals_df, wo_df):
    """
    Creates an intelligent Pandas Agent combining both boards using Groq.
    """
    api_key = get_ai_key()
    if not api_key:
        return None

    # Using a lighter, highly available model to avoid token limits.
    try:
        llm = ChatGroq(
            temperature=0, 
            model_name="llama-3.1-8b-instant", 
            groq_api_key=api_key
        )
    except Exception as e:
        return None

    prefix = """
You are an expert AI Business Intelligence Agent. Your goal is to answer founder-level business questions using real-time data from Monday.com boards.
You have access to two pandas dataframes:
df1: Deals Board Data (contains pipeline, expected revenue, stage, sector)
df2: Work Orders Board Data (contains project status, sector, timeline)

Rules for Accuracy:
- Only return answers backed by exact data available in these frames.
- Do NOT hallucinate numbers or make up data.
- Provide insights, merging contexts when asked about revenue vs execution.
- If data is too sparse or missing to calculate, say "Data incomplete for this analysis".
"""

    try:
        agent = create_pandas_dataframe_agent(
            llm,
            [deals_df, wo_df],
            verbose=False,
            allow_dangerous_code=True,
            prefix=prefix
        )
        return agent
    except Exception as e:
        return None

def ask_agent(agent, query):
    if not agent:
        return "⚠️ GROQ_API_KEY is missing or invalid. Please configure it in .env or Streamlit Secrets."
    try:
        response = agent.invoke({"input": query})
        return response['output']
    except Exception as e:
        return f"🚨 Analysis Error: {str(e)}"

def generate_executive_summary(metrics):
    """Generates an executive summary using minimal tokens, bypassing the pandas agent."""
    api_key = get_ai_key()
    if not api_key:
        return "⚠️ GROQ_API_KEY is missing or invalid. Please configure it in .env or Streamlit Secrets."
        
    try:
        llm = ChatGroq(
            temperature=0.2, 
            model_name="llama-3.1-8b-instant", 
            groq_api_key=api_key
        )
        
        prompt = f"""
        You are an AI Business Intelligence Analyst.
        Generate a very concise 5-bullet executive Leadership Summary using this exact data:
        Total Pipeline: {metrics.get('Total Pipeline Value', 0)}
        Expected Revenue: {metrics.get('Expected Revenue', 0)}
        Top Sector: {metrics.get('Top Sector', 'Unknown')}
        Work Order Completion: {metrics.get('Work Order Completion Rate', '0%')}
        
        Format clearly with emojis. Do not hallucinate numbers. Identify one hypothetical operational risk based on these metrics.
        """
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"🚨 Generation Error: {str(e)}"
