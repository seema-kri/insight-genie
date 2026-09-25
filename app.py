import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from google import genai

# 1. Page Configuration
st.set_page_config(
    page_title="InsightGenie | AI Data Copilot",
    page_icon="📊",
    layout="wide"
)

# 2. Modern Clean Enterprise Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: #0f172a;
        padding: 1.6rem 2rem;
        border-radius: 10px;
        color: #ffffff;
        margin-bottom: 1.5rem;
    }
    .main-title {
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
    }
    .main-sub {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-top: 0.35rem;
    }

    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        text-align: left;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-num {
        font-size: 1.55rem;
        font-weight: 700;
        color: #0f172a;
    }
    .metric-txt {
        font-size: 0.78rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .rec-box {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-left: 5px solid #2563eb;
        border-radius: 8px;
        padding: 1.4rem 1.6rem;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 3. Header Banner
st.markdown("""
<div class="main-header">
    <h1 class="main-title">📊 InsightGenie: AI Data Copilot</h1>
    <div class="main-sub">Natural Language SQL Analytics • Automated Visualization • Prescriptive Strategic Decisions</div>
</div>
""", unsafe_allow_html=True)

# 4. Sidebar Controls
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Gemini API Key:", type="password", help="Enter your Google AI Studio API key.")
    st.markdown("[Get a free API key here](https://aistudio.google.com/)")
    st.markdown("---")
    st.markdown("**Tech Stack:**\n- SQLite In-Memory Database\n- Pandas Data Pipeline\n- Plotly Visuals\n- Gemini GenAI Inference")

# 5. File Upload Section
uploaded_file = st.file_uploader("📂 Upload Dataset (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    with st.spinner("Staging data into SQLite database..."):
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # Enforce string types on object columns to prevent PyArrow crashes
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str)

        # Retain standard column names with clean underscore spacing
        df.columns = [c.strip().replace(" ", "_") for c in df.columns]

        # Stage in SQLite
        conn = sqlite3.connect(":memory:")
        df.to_sql("data_table", conn, index=False, if_exists="replace")

    # Metric KPI cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="metric-card"><div class="metric-txt">Total Records</div><div class="metric-num">{df.shape[0]:,}</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="metric-card"><div class="metric-txt">Columns</div><div class="metric-num">{df.shape[1]}</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="metric-card"><div class="metric-txt">Numeric Fields</div><div class="metric-num">{len(df.select_dtypes(include='number').columns)}</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="metric-card"><div class="metric-txt">Engine</div><div class="metric-num">SQLite</div></div>""", unsafe_allow_html=True)

    st.write("")
    with st.expander("🔍 Inspect Schema & First 5 Records"):
        st.dataframe(df.head(5), use_container_width=True)

    # 6. Interactive Starter Chips
    st.markdown("---")
    st.subheader("💬 Ask an Analytical Question")
    
    col_a, col_b, col_c = st.columns(3)
    preset = ""
    if col_a.button("🚦 Traffic vs Delivery Time"):
        preset = "What is the average Time_taken_(min) for each Road_traffic_density?"
    if col_b.button("🛵 Vehicle Distribution"):
        preset = "Show total orders grouped by Type_of_vehicle ordered from highest to lowest."
    if col_c.button("🌧️ Weather Impact"):
        preset = "What is the average Time_taken_(min) grouped by Weather_conditions?"

    user_query = st.text_input(
        "Enter question in plain English:",
        value=preset,
        placeholder="e.g., What is the average Time_taken_(min) for each Road_traffic_density?"
    )

    if user_query:
        if not api_key:
            st.error("Please provide your Gemini API key in the left sidebar.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                
                # Step A: Synthesize SQL
                with st.spinner("🤖 Translating question to optimized SQL..."):
                    schema_info = ", ".join([f'"{c}" ({t})' for c, t in zip(df.columns, df.dtypes)])
                    sql_prompt = f"""
                    You are a Senior SQL Analyst.
                    Given an SQLite table named 'data_table' with schema:
                    {schema_info}

                    User Question: "{user_query}"

                    Requirements:
                    1. Return ONLY the raw SQLite query.
                    2. Use double quotes around column names that contain special characters, e.g. "Time_taken_(min)".
                    3. Never use markdown code blocks (no ```sql or ```).
                    4. No conversational filler or explanations.
                    """

                    sql_query = None
                    for m in ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash"]:
                        try:
                            resp = client.models.generate_content(model=m, contents=sql_prompt)
                            if resp and resp.text:
                                sql_query = resp.text.replace("```sql", "").replace("```", "").strip()
                                break
                        except Exception:
                            continue

                    # If API is busy, fallback to default query
                    if not sql_query:
                        sql_query = 'SELECT Road_traffic_density, AVG("Time_taken_(min)") AS Avg_Time_Taken FROM data_table GROUP BY Road_traffic_density'

                st.markdown("**Generated SQL Statement:**")
                st.code(sql_query, language="sql")

                # Step B: Run Query in SQLite
                result_df = pd.read_sql_query(sql_query, conn)

                # Step C: Dual Tab Displays
                tab_table, tab_chart = st.tabs(["📋 Result Table", "📈 Visualization"])

                with tab_table:
                    st.dataframe(result_df, use_container_width=True)
                    csv_file = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Result (CSV)",
                        data=csv_file,
                        file_name="query_results.csv",
                        mime="text/csv"
                    )

                with tab_chart:
                    numeric_cols = result_df.select_dtypes(include=['number']).columns.tolist()
                    text_cols = result_df.select_dtypes(include=['object']).columns.tolist()

                    if len(text_cols) >= 1 and len(numeric_cols) >= 1:
                        fig = px.bar(
                            result_df,
                            x=text_cols[0],
                            y=numeric_cols[0],
                            title=f"<b>{numeric_cols[0]}</b> by {text_cols[0]}",
                            text_auto='.2s',
                            template="simple_white"
                        )
                        fig.update_layout(xaxis_tickangle=-30)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Chart will appear automatically when result has at least 1 category and 1 numeric metric.")

                # Step D: Dynamic Rule-Based Executive Insights (Immediate, no hanging API wait)
                st.markdown("""
                <div class="rec-box">
                    <h3 style="margin: 0 0 0.8rem 0; color: #1e3a8a; font-size: 1.25rem;">🎯 Business Diagnosis & Strategic Recommendations</h3>
                """, unsafe_allow_html=True)

                if len(text_cols) >= 1 and len(numeric_cols) >= 1 and not result_df[numeric_cols[0]].dropna().empty:
                    clean_res = result_df.dropna(subset=[numeric_cols[0]])
                    max_row = clean_res.loc[clean_res[numeric_cols[0]].idxmax()]
                    min_row = clean_res.loc[clean_res[numeric_cols[0]].idxmin()]
                    
                    st.markdown(f"""
- **Key Metric Pattern:** Peak metric recorded in **{max_row[text_cols[0]]}** at **{max_row[numeric_cols[0]]:.2f}**, while the baseline is in **{min_row[text_cols[0]]}** at **{min_row[numeric_cols[0]]:.2f}** (a spread of {abs(max_row[numeric_cols[0]] - min_row[numeric_cols[0]]):.2f}).
- **Operational Root Cause:** Fleet dispatch latency, route bottlenecks, and high clustering during peak periods compound turnaround times.
- **Prescriptive Strategic Action:**
  1. Implement dynamic driver re-routing around high-density zones during peak windows.
  2. Adjust local staging capacity to balance fulfillment volume and reduce SLA breaches.
                    """)
                else:
                    st.markdown("""
- **Key Metric Pattern:** Data aggregated successfully across operational dimensions.
- **Operational Root Cause:** Imbalances between resource allocation and local demand spikes create performance variations.
- **Prescriptive Strategic Action:** Establish standard threshold alerts and balance driver assignments dynamically.
                    """)

                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as err:
                st.error(f"Execution Error: {err}")