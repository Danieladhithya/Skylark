import os
import requests
import pandas as pd
import streamlit as st

API_URL = "https://api.monday.com/v2"

def get_monday_token():
    try:
        # Check streamlit secrets first
        return st.secrets["MONDAY_API_TOKEN"]
    except Exception:
        # Fallback to environment variable
        return os.environ.get("MONDAY_API_TOKEN", "")

def fetch_board_data(board_id):
    """
    Fetch all items and columns from a Monday.com board using GraphQL API.
    Handles pagination sequentially.
    """
    token = get_monday_token()
    if not token:
        st.error("Missing Monday.com API Token. Add it to .env or Streamlit Secrets.")
        return pd.DataFrame()

    headers = {
        "Authorization": token,
        "API-Version": "2024-01",
        "Content-Type": "application/json"
    }

    query = """
    query ($boardId: [ID!], $cursor: String) {
      boards(ids: $boardId) {
        name
        items_page(limit: 100, cursor: $cursor) {
          cursor
          items {
            id
            name
            column_values {
              id
              text
              type
              value
              column {
                title
              }
            }
          }
        }
      }
    }
    """

    all_items = []
    cursor = None

    try:
        while True:
            variables = {"boardId": [board_id]}
            if cursor:
                variables["cursor"] = cursor

            response = requests.post(API_URL, json={'query': query, 'variables': variables}, headers=headers)
            response.raise_for_status()
            data = response.json()

            if 'errors' in data:
                st.error(f"GraphQL Error: {data['errors']}")
                break

            boards = data.get('data', {}).get('boards', [])
            if not boards:
                break

            board = boards[0]
            items_page = board.get('items_page', {})
            items = items_page.get('items', [])

            for item in items:
                row = {'Item ID': item['id'], 'Item Name': item['name']}
                for cv in item['column_values']:
                    col_title = cv['column']['title']
                    row[col_title] = cv['text'] if cv['text'] else 'Unknown'
                all_items.append(row)

            cursor = items_page.get('cursor')
            if not cursor or len(items) == 0:
                break

        return pd.DataFrame(all_items)

    except requests.exceptions.RequestException as e:
        st.error(f"Network error while fetching board data: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error parsing Monday.com response: {str(e)}")
        return pd.DataFrame()
