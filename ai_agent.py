import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

def get_openai_key():
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return os.environ.get("OPENAI_API_KEY", "")

def get_ai_agent(deals_df, wo_df):
    """
    Creates an intelligent Pandas Agent combining both boards.
    """
    api_key = get_openai_key()
    if not api_key:
        return None

    # Using GPT-4o for best reasoning
    llm = ChatOpenAI(temperature=0, model="gpt-4o", openai_api_key=api_key)

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

    agent = create_pandas_dataframe_agent(
        llm,
        [deals_df, wo_df],
        verbose=False,
        agent_type="openai-tools",
        allow_dangerous_code=True,
        prefix=prefix
    )

    return agent

def ask_agent(agent, query):
    if not agent:
        return "⚠️ OpenAI API Key is missing. Please configure it in .env or Streamlit Secrets."
    try:
        response = agent.invoke({"input": query})
        return response['output']
    except Exception as e:
        return f"🚨 Analysis Error: {str(e)}"
