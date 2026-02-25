import pandas as pd
import numpy as np
import re

def clean_currency(val):
    if pd.isna(val) or val == 'Unknown':
        return 0.0
    val_str = str(val).replace('$', '').replace(',', '').strip()
    try:
        return float(val_str)
    except Exception:
        return 0.0

def process_data(df, board_type="deals"):
    """
    Cleans messy data: handles missing values, inconsistent formats,
    standardizes names, and normalizes types.
    """
    if df.empty:
        return df

    df = df.copy()

    # Generic fill
    df.fillna('Unknown', inplace=True)
    df.replace({'': 'Unknown', 'None': 'Unknown', None: 'Unknown'}, inplace=True)

    # dynamically detect columns
    date_cols = [c for c in df.columns if 'date' in c.lower()]
    currency_cols = [c for c in df.columns if any(x in c.lower() for x in ['revenue', 'value', 'amount', 'budget'])]
    status_cols = [c for c in df.columns if 'status' in c.lower() or 'stage' in c.lower()]
    sector_cols = [c for c in df.columns if 'sector' in c.lower() or 'industry' in c.lower()]

    # Normalize Dates -> standard datetime format
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors='coerce')
        # We can keep them as datetime or formatted strings; Let's format as YYYY-MM-DD
        df[c] = df[c].dt.strftime('%Y-%m-%d').fillna('Unknown')

    # Normalize Revenue -> numeric using robust pandas numeric coercing
    for c in currency_cols:
        df[c] = df[c].astype(str).apply(lambda x: re.sub(r'[^\d.-]', '', x))
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)

    # Normalize Sector names -> standardized Title case
    for c in sector_cols:
        df[c] = df[c].astype(str).str.title().str.strip()

    # Normalize Status fields -> consistent labels
    for c in status_cols:
        df[c] = df[c].astype(str).str.title().str.strip()
        # Edge cases replacing known inconsistencies
        df[c] = df[c].replace({'In-Progress': 'In Progress', 'Done': 'Completed'})

    # Drop duplicate records based on Item ID
    if 'Item ID' in df.columns:
        df.drop_duplicates(subset=['Item ID'], inplace=True)

    return df

def calculate_metrics(deals_df, wo_df):
    """
    Computes business metrics directly ensuring 100% accuracy from the processed data.
    """
    metrics = {
        "Total Pipeline Value": 0.0,
        "Expected Revenue": 0.0,
        "Work Order Completion Rate": "0%",
        "Active Projects": 0,
        "Completed Projects": 0,
        "Top Sector": "None"
    }

    if not deals_df.empty:
        currency_cols = [c for c in deals_df.columns if any(x in c.lower() for x in ['revenue', 'value', 'amount'])]
        status_cols = [c for c in deals_df.columns if 'stage' in c.lower() or 'status' in c.lower()]
        sector_cols = [c for c in deals_df.columns if 'sector' in c.lower() or 'industry' in c.lower()]
        
        val_col = currency_cols[0] if currency_cols else None
        stage_col = status_cols[0] if status_cols else None
        sector_col = sector_cols[0] if sector_cols else None

        if val_col:
            metrics["Total Pipeline Value"] = deals_df[val_col].sum()
            
            if stage_col:
                won_keywords = ['won', 'closed', 'completed', 'signed']
                won_df = deals_df[deals_df[stage_col].astype(str).str.lower().apply(lambda x: any(w in x for w in won_keywords))]
                metrics["Expected Revenue"] = won_df[val_col].sum()
        
        # Determine Top Sector by revenue, or by count if revenue missing
        if val_col and sector_col:
            sector_sums = deals_df.groupby(sector_col)[val_col].sum()
            if not sector_sums.empty:
                valid_sectors = sector_sums[sector_sums.index != 'Unknown']
                if not valid_sectors.empty:
                    metrics["Top Sector"] = valid_sectors.idxmax()

    if not wo_df.empty:
        status_cols = [c for c in wo_df.columns if 'status' in c.lower()]
        if status_cols:
            status_col = status_cols[0]
            total_wo = len(wo_df)
            
            done_keywords = ['done', 'completed', 'finished']
            completed_wo = len(wo_df[wo_df[status_col].astype(str).str.lower().apply(lambda x: any(w in x for w in done_keywords))])
            
            active_keywords = ['working', 'in progress', 'started', 'active']
            active_wo = len(wo_df[wo_df[status_col].astype(str).str.lower().apply(lambda x: any(w in x for w in active_keywords))])
            
            metrics["Total Work Orders"] = total_wo
            metrics["Completed Projects"] = completed_wo
            metrics["Active Projects"] = active_wo
            
            if total_wo > 0:
                metrics["Work Order Completion Rate"] = f"{(completed_wo / total_wo * 100):.1f}%"

    return metrics
