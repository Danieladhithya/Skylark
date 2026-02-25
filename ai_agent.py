import os
import streamlit as st
from langchain_groq import ChatGroq

def get_ai_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.environ.get("GROQ_API_KEY", "")

def get_ai_agent(deals_df, wo_df):
    """
    Instead of passing the entire dataframe to a heavy Langchain agent (which burns through 
    Free Tier API token limits instantly), we pass the dataframes to be summarized dynamically.
    """
    return deals_df, wo_df

def ask_agent(agent_data, query):
    deals_df, wo_df = agent_data
    api_key = get_ai_key()
    
    if not api_key:
        return "⚠️ GROQ_API_KEY is missing or invalid. Please configure it in .env or Streamlit Secrets."

    try:
        llm = ChatGroq(
            temperature=0, 
            model_name="llama-3.1-8b-instant", 
            groq_api_key=api_key
        )
        
        # ⚡ DYNAMIC TOKEN-EFFICIENT DATA AGGREGATION ⚡
        # Instead of sending 100 rows of raw text (3000+ tokens), we calculate
        # the exact grouped pivots in pandas (using ~100 tokens), preventing rate limits!
        
        deals_summary = "Deals Board Stats:\n"
        if not deals_df.empty:
            val_col = [c for c in deals_df.columns if any(x in c.lower() for x in ['revenue', 'value', 'amount'])]
            val_col = val_col[0] if val_col else None
            stage_col = [c for c in deals_df.columns if 'stage' in c.lower() or 'status' in c.lower()]
            stage_col = stage_col[0] if stage_col else None
            sector_col = [c for c in deals_df.columns if 'sector' in c.lower() or 'industry' in c.lower()]
            sector_col = sector_col[0] if sector_col else None

            if val_col: 
                deals_summary += f"- Total Pipeline Sum: ${deals_df[val_col].sum():,.2f}\n\n"
                deals_summary += "Top 5 Deals (Highest Value):\n"
                top_deals = deals_df.nlargest(5, val_col)
                for _, row in top_deals.iterrows():
                    client = row.get('Item Name', 'Unknown')
                    val = row.get(val_col, 0)
                    stg = row.get(stage_col, 'Unknown') if stage_col else 'Unknown'
                    sect = row.get(sector_col, 'Unknown') if sector_col else 'Unknown'
                    deals_summary += f"- Client: {client} | Value: ${val:,.2f} | Stage: {stg} | Sector: {sect}\n"
                
            if val_col and stage_col:
                grouped_stage = deals_df.groupby(stage_col)[val_col].sum().apply(lambda x: f"${x:,.2f}")
                deals_summary += f"\n- Revenue grouped by Stage:\n{grouped_stage.to_string()}\n"
            if val_col and sector_col:
                grouped_sector = deals_df.groupby(sector_col)[val_col].sum().apply(lambda x: f"${x:,.2f}")
                deals_summary += f"- Revenue grouped by Sector:\n{grouped_sector.to_string()}\n"
        
        wo_summary = "Work Orders Stats:\n"
        if not wo_df.empty:
            status_col = [c for c in wo_df.columns if 'status' in c.lower()]
            status_col = status_col[0] if status_col else None
            if status_col:
                wo_summary += f"- Project Count grouped by Status:\n{wo_df[status_col].value_counts().to_string()}\n"
                
            sector_col = [c for c in wo_df.columns if 'sector' in c.lower() or 'industry' in c.lower()]
            sector_col = sector_col[0] if sector_col else None
            if sector_col:
                wo_summary += f"- Project Count grouped by Sector:\n{wo_df[sector_col].value_counts().to_string()}\n"

        prompt = f"""
You are an expert AI Business Intelligence Agent. Answer founder-level business questions using ONLY the following real-time aggregated data calculated from Monday.com boards.

{deals_summary}

{wo_summary}

User Question: {query}

Rules:
1. Provide a direct, factual answer first. Format clearly.
2. If asked to sum or show revenue across sectors, format the answer like this:
   Sector A = $#,###
   Sector B = $#,###
   -------------------
   Total Revenue = $#,###
3. Be extremely concise. Do not write long generic explanations.
4. Use a highly professional tone. No fluffy intros.
5. If asked about the "highest", "top", or a specific client, respond directly using the "Top 5 Deals" list provided above.
6. Do NOT do manual decimal math. Use the exact text/numbers provided in the summary above exactly as they appear.
"""
        response = llm.invoke(prompt)
        return response.content
        
    except Exception as e:
        return f"🚨 Analysis Error: {str(e)}"

def generate_executive_summary(metrics):
    """Generates an executive summary using minimal tokens."""
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
Work Order Completion Rate: {metrics.get('Work Order Completion Rate', '0%')}

Format clearly with emojis. Identify one hypothetical operational risk based on these metrics.
"""
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        return f"🚨 Generation Error: {str(e)}"
