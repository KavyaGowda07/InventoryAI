# app.py
import streamlit as st
import os
import io
from fpdf import FPDF
from prompts.system_prompt import SYSTEM_PROMPT
from utils.csv_loader import load_inventory_context, get_inventory_metrics
from utils.llm import get_response

# 1. PAGE & THEME CONFIGURATION
st.set_page_config(
    page_title="InventoryAI Pro", 
    page_icon="📦", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force-inject premium enterprise styling overrides
st.markdown("""
    <style>
    /* Application Canvas Background */
    .stApp { background: #f8fafc; }
    
    /* Metrics Visual Cards Styling */
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 800 !important; color: #0f172a !important; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; font-weight: 700 !important; color: #64748b !important; text-transform: uppercase; letter-spacing: 0.5px; }
    div[data-testid="metric-container"] {
        background: #ffffff;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        border-top: 4px solid #3b82f6;
    }
    
    /* Clean Typography Grid */
    .main-title { font-size: 2.6rem; font-weight: 800; color: #0f172a; margin-bottom: 2px; letter-spacing: -0.5px; }
    .sub-title { font-size: 1.05rem; color: #475569; margin-bottom: 30px; line-height: 1.5; }
    
    /* Sidebar Text Overflow Fix */
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0; }
    .sidebar-success-box {
        background-color: #f0fdf4;
        color: #166534;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #bbf7d0;
        font-size: 0.85rem;
        word-break: break-all;
        font-weight: 500;
    }
    
    /* Dynamic Chat Area Enhancements */
    .chat-bubble-user {
        background-color: #f1f5f9;
        border-radius: 16px 16px 4px 16px;
        padding: 14px 18px;
        color: #1e293b;
        border: 1px solid #e2e8f0;
        margin-bottom: 12px;
    }
    .chat-bubble-ai {
        background-color: #f0fdfa;
        border-radius: 16px 16px 16px 4px;
        padding: 14px 18px;
        color: #0f172a;
        border: 1px solid #ccfbf1;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# Ensure data runtime workspace exists
os.makedirs("data", exist_ok=True)

# 2. SESSION STATE MANAGEMENT
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. SIDEBAR NAVIGATION CONTROLS
with st.sidebar:
    st.markdown("## 📦 InventoryAI Pro")
    st.caption("Enterprise Asset Lifecycle Management")
    st.markdown("---")
    
    st.markdown("### 📥 Database Integration")
    uploaded_file = st.file_uploader(
        "Upload operational database", 
        type=["csv", "xlsx"],
        help="Drag & drop asset CSV or Excel registries."
    )
    
    active_data_source = None
    if uploaded_file is not None:
        active_data_source = f"data/uploaded_{uploaded_file.name}"
        with open(active_data_source, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.markdown(f'<div class="sidebar-success-box">✓ Connected:<br>{uploaded_file.name}</div>', unsafe_allow_html=True)
        
        if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
            st.session_state.messages = []
            st.session_state.last_uploaded = uploaded_file.name
    else:
        st.info("👋 Upload a CSV/XLSX file to initiate live processing.")

    st.markdown("---")
    st.markdown("### ⚙️ Workspace Tools")
    
    # PDF Compilation Downloader
    if len(st.session_state.messages) > 0:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        
        # Version-safe cell writing syntax
        pdf.cell(200, 10, "InventoryAI Professional Chat History Log", ln=1)
        pdf.cell(200, 10, "--------------------------------------------------", ln=1)
        
        for msg in st.session_state.messages:
            speaker = "USER" if msg["role"] == "user" else "INVENTORYAI"
            clean_text = msg["content"].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 8, f"[{speaker}]: {clean_text}")
            pdf.cell(200, 5, "", ln=1)
            
        pdf_output = pdf.output(dest='S') if hasattr(pdf, 'output') else pdf.output()
        
        st.download_button(
            label="📥 Download Chat Log (PDF)",
            data=bytes(pdf_output) if isinstance(pdf_output, (bytes, bytearray)) else pdf_output.encode('latin-1'),
            file_name="inventory_ai_chat_log.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
    if st.button("🗑️ Clear Workspace Memory", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 4. MAIN CENTRAL INTERFACE LAYOUT
st.markdown('<p class="main-title">💬 AI Operations Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Query deployment statuses, cross-reference unique hardware configurations, run registry duplicates auditing, or track warehouse item thresholds instantly.</p>', unsafe_allow_html=True)

# 5. ADAPTIVE METRICS PANEL
if active_data_source and os.path.exists(active_data_source):
    stats = get_inventory_metrics(active_data_source)
else:
    stats = {"total_assets": 0, "departments": 0, "rooms": 0, "types": 0, "total_columns": 0, "has_special_data": False}

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

with metric_col1:
    st.metric(label="📋 Total Records Found", value=f"{stats['total_assets']:,}")

if stats["has_special_data"]:
    with metric_col2:
        st.metric(label="🏢 Unique Departments", value=stats["departments"])
    with metric_col3:
        st.metric(label="📍 Active Rooms / Labs", value=stats["rooms"])
    with metric_col4:
        st.metric(label="🏷️ Asset Types Detected", value=stats["types"])
else:
    with metric_col2:
        st.metric(label="📊 Total Data Columns", value=stats["total_columns"])
    with metric_col3:
        st.metric(label="🏢 Unique Departments", value="N/A")
    with metric_col4:
        st.metric(label="📍 Active Rooms / Labs", value="N/A")

st.markdown("<br><hr>", unsafe_allow_html=True)

# 6. ENHANCED CHAT CONTEXT WINDOW
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(f'<div class="chat-bubble-user">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(f'<div class="chat-bubble-ai">{message["content"]}</div>', unsafe_allow_html=True)

clicked_prompt = None

# Show Suggested Queries Grid Only if Chat Memory is Blank
if len(st.session_state.messages) == 0:
    st.markdown("#### 💡 Suggested Core Queries")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Count all CC devices", use_container_width=True): clicked_prompt = "Count all CC devices"
        if st.button("📍 Show all devices in D-203", use_container_width=True): clicked_prompt = "Show all devices in D-203"
        if st.button("🔍 Find UID of CC-24", use_container_width=True): clicked_prompt = "Find UID of CC-24"
    with col2:
        if st.button("📋 List all SYS devices", use_container_width=True): clicked_prompt = "List all SYS devices"
        if st.button("🏢 Which room has the most devices?", use_container_width=True): clicked_prompt = "Which room has the most devices?"
        if st.button("⚠️ Show duplicate UIDs", use_container_width=True): clicked_prompt = "Show duplicate UIDs"

# Input field listener processing
user_query = st.chat_input("Query assets, hardware locations, or auditing compliance lists...")
if clicked_prompt:
    user_query = clicked_prompt

if user_query:
    if not active_data_source:
        st.warning("⚠️ Please upload an inventory database file in the sidebar controller before initiating analytical requests.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.rerun()

# Run actual LLM calls on state change
if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "user":
    current_query = st.session_state.messages[-1]["content"]
    
    with st.spinner("Analyzing operational database records..."):
        inventory_context = load_inventory_context(active_data_source)
        ai_response = get_response(
            system_prompt=SYSTEM_PROMPT,
            inventory_data=inventory_context,
            user_question=current_query,
            file_path=active_data_source
        )
        
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    st.rerun()
