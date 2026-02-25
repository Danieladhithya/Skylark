# 📊 AI Business Intelligence Agent integrated with Monday.com

A production-ready Enterprise AI Agent that connects live to Monday.com boards to dynamically answer founder-level business questions, calculate metrics, and provide executive summaries. Built with Streamlit, Pandas, LangChain, and OpenAI GPT-4o.

## 🌟 Key Features
- **Live Monday.com Integration:** Uses the GraphQL API to dynamically fetch Deals and Work Orders boards with real-time accuracy and pagination support.
- **Robust Data Cleaning Layer:** Normalizes text, dates, missing values, currencies, status labels, sector categories, and drops duplicates to ensure zero hallucinated numbers.
- **Natural Language BI Chat:** Ask any question across the datasets, such as *"What is our expected revenue this quarter?"* or *"What is our work order completion rate?"*
- **Executive Leadership Summaries:** One-click execution generates a 5-bullet holistic breakdown of firm performance, risk, and top sectors.
- **Production-Ready & Secure:** Secrets are managed via `.env` for local dev and Streamlit Secrets for cloud deployment.

---

## 🛠 Project Structure
- `app.py`: Streamlit frontend application, dashboard layout, and interaction logic.
- `monday_api.py`: GraphQL API integration with Monday.com, pagination handling, and robust network error recovery.
- `data_processing.py`: Advanced Pandas processing logic. Normalizes raw inputs, imputes missing fields, standardization, and core deterministic metric calculation.
- `ai_agent.py`: Instantiates a LangChain `create_pandas_dataframe_agent` wrapped around GPT-4o.
- `requirements.txt`: Python package dependencies.

---

## 🚀 Local Setup & Testing

**1. Clone the repository / Download files**
Place all 5 files in a directory.

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure Credentials**
Create a `.env` file in the root directory (or use Streamlit Secrets) with the following variables:
```env
MONDAY_API_TOKEN=your_monday_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

**4. Run locally**
```bash
streamlit run app.py
```

---

## ☁️ Streamlit Community Cloud Deployment

To host this publicly so your manager can access it immediately:

1. Push this entire folder to a public or private **GitHub Repository**.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **"New app"** and select your repository, branch, and `app.py` as the main file path.
4. Click on **Advanced Settings** (the gear icon or within the setup panel).
5. In the **Secrets** section, paste your environment variables format:
```toml
MONDAY_API_TOKEN="eyJhbGciOiJIUzI... (your token)"
OPENAI_API_KEY="sk-..."
```
6. Click **Deploy!**

**Deliverable URL:** *Once you click deploy in Step 6, Streamlit will instantly generate your Live App URL (e.g., `https://your-ai-bi-agent.streamlit.app`). Copy and share this link with your manager.*

---

## 🏗 Architecture Flow
`User ➔ Streamlit UI ➔ ai_agent.py (LangChain GPT-4o) ➔ query ➔ Processed Pandas DF ➔ monday_api.py (GraphQL)`

If an API call fails or there are empty datasets, the frontend catches the condition and gracefully alerts the user without crashing. Missing data correctly produces a "Data incomplete" message to guarantee non-hallucinated accuracy.
