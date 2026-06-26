import streamlit as st
import requests
import json
import pandas as pd
import altair as alt

st.set_page_config(page_title="SolSec Core", layout="wide")

# --- MINIMALIST LIGHT MODE CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    /* Pure White Background */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }
    
    /* SideBar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #eeeeee;
    }

    /* THE HERO HEADER */
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 200px;
        font-weight: 700;
        color: #000000;
        line-height: 0.8;
        letter-spacing: -10px;
        margin-bottom: 20px;
        margin-top: -50px;
    }
    .hero-subtitle {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 36px;
        font-weight: 300;
        color: #444444;
        letter-spacing: -1px;
        margin-bottom: 60px;
    }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 48px;
        font-weight: 700;
        color: #000000;
    }
    [data-testid="stMetricLabel"] {
        color: #666666 !important;
    }
    
    /* Finding Cards - High Contrast Light */
    .finding-card {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 0px;
        border: 2px solid #000000;
        margin-bottom: 20px;
        color: #000000;
        box-shadow: 5px 5px 0px #eeeeee;
    }
    .finding-card h3 {
        color: #000000 !important;
    }
    .finding-card p {
        color: #333333;
    }
    .severity-high { border-left: 20px solid #ff4b4b; }
    .severity-medium { border-left: 20px solid #ffa500; }
    .severity-low { border-left: 20px solid #2e7d32; }
    .severity-info { border-left: 20px solid #0288d1; }
    
    /* Code Viewer */
    .stCode {
        border-radius: 0px;
        border: 2px solid #000000;
    }

    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        color: #000000;
        text-transform: uppercase;
    }
    
    .stDivider {
        border-bottom: 1px solid #eeeeee !important;
    }

    /* Upload Box - Light High Contrast */
    section[data-testid="stFileUploadDropzone"] {
        background-color: #fcfcfc;
        border: 2px dashed #000000 !important;
    }
    
    /* Browse Button */
    section[data-testid="stFileUploadDropzone"] button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border: none !important;
        padding: 10px 20px !important;
        border-radius: 0px !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stFileUploaderFileName"] {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("SOL-SEC")
    st.markdown("---")
    min_severity = st.select_slider(
        "SENSITIVITY",
        options=["Optimization", "Informational", "Low", "Medium", "High", "Critical"],
        value="Low"
    )
    st.markdown("---")
    st.subheader("ACTIVE STACK")
    st.write("**SLITHER** / Static Analysis")
    st.write("**MYTHRIL** / Symbolic Exec")
    st.write("**SOLHINT** / Linter")
    st.markdown("---")
    st.write("CORE V1.0 ACTIVE")

# --- MAIN APP HEADER ---
st.markdown('<h1 class="hero-title">SOL-SEC</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Unified Smart Contract Analysis Pipeline</p>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("DROP SOLIDITY CONTRACT", type="sol")

if uploaded_file:
    code_content = uploaded_file.getvalue().decode("utf-8")
    
    # Separate the UI into Audit and CFG Visualizer Tabs
    tab_audit, tab_cfg = st.tabs(["🔒 SECURITY AUDIT", "📊 CFG VISUALIZER"])
    
    with tab_audit:
        with st.spinner("SCANNING..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                response = requests.post("http://localhost:8000/analyze", files=files)
                
                if response.status_code == 200:
                    report = response.json()
                    findings = report.get("findings", [])
                    
                    severity_order = ["Optimization", "Informational", "Low", "Medium", "High", "Critical"]
                    min_idx = severity_order.index(min_severity)
                    filtered_findings = [f for f in findings if severity_order.index(f["severity"]) >= min_idx]
                    
                    col_left, col_right = st.columns([1, 1.2], gap="large")
                    
                    with col_left:
                        st.subheader(f"REPORT / {len(filtered_findings)} ISSUES")
                        
                        m1, m2, m3 = st.columns(3)
                        m1.metric("FINDINGS", len(filtered_findings))
                        health_score = max(0, 100 - len(findings)*5)
                        m2.metric("HEALTH", f"{health_score}")
                        m3.metric("RAW", report.get("metadata", {}).get("total_raw_findings", 0))
                        
                        st.divider()
                        
                        for i, f in enumerate(filtered_findings, 1):
                            sev = f["severity"].lower()
                            st.markdown(f"""
                                <div class="finding-card severity-{sev}">
                                    <h3 style='margin-top:0;'>{i}. {f['title']}</h3>
                                    <p style='font-size:1.1rem; font-weight:700;'>
                                        {f['severity'].upper()} / {f['tool'].upper()} / L:{f['line_number']}
                                    </p>
                                    <p style='font-size:1rem; line-height:1.4;'>{f['description']}</p>
                                </div>
                            """, unsafe_allow_html=True)

                    with col_right:
                        st.subheader("SOURCE")
                        st.code(code_content, language="solidity", line_numbers=True)

                else:
                    st.error("PIPELINE ERROR")
            except Exception as e:
                st.error(f"BACKEND OFFLINE: {e}")
                
    with tab_cfg:
        with st.spinner("EXTRACTING CFG..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                response = requests.post("http://localhost:8000/cfg", files=files)
                
                if response.status_code == 200:
                    cfgs = response.json()
                    
                    if not cfgs:
                        st.info("No contracts found to extract CFG.")
                    else:
                        contract_names = list(cfgs.keys())
                        selected_contract = st.selectbox("SELECT CONTRACT", contract_names, key="cfg_contract_select")
                        
                        if selected_contract:
                            contract_cfg = cfgs[selected_contract]
                            functions = contract_cfg.get("functions", {})
                            
                            if not functions:
                                st.info("No functions with control flow found in this contract.")
                            else:
                                function_names = list(functions.keys())
                                selected_function = st.selectbox("SELECT FUNCTION / MODIFIER", function_names, key="cfg_func_select")
                                
                                if selected_function:
                                    func_cfg = functions[selected_function]
                                    
                                    col_graph, col_details = st.columns([1.5, 1], gap="large")
                                    
                                    with col_graph:
                                        st.subheader("FLOW CHART")
                                        mermaid_code = func_cfg.get("mermaid", "")
                                        if mermaid_code:
                                            import streamlit.components.v1 as components
                                            html_code = f"""
                                            <div style="background-color: white; padding: 20px; border-radius: 8px; border: 2px solid #000000; box-shadow: 5px 5px 0px #eeeeee; overflow: auto;">
                                                <script type="module">
                                                    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                                                    mermaid.initialize({{ startOnLoad: true, theme: 'neutral' }});
                                                </script>
                                                <pre class="mermaid" style="display: flex; justify-content: center; margin: 0;">
                                                    {mermaid_code}
                                                </pre>
                                            </div>
                                            """
                                            components.html(html_code, height=550, scrolling=True)
                                        else:
                                            st.write("No flow chart representation available.")
                                            
                                    with col_details:
                                        st.subheader("BLOCK DETAILS")
                                        st.write(f"**Visibility:** `{func_cfg.get('visibility')}`")
                                        st.write(f"**Type:** `{func_cfg.get('type')}`")
                                        if func_cfg.get("state_mutability"):
                                            st.write(f"**Mutability:** `{func_cfg.get('state_mutability')}`")
                                        st.divider()
                                        
                                        st.write("**BLOCKS & SLITHIR IR:**")
                                        for node in func_cfg.get("nodes", []):
                                            with st.expander(f"Node {node['id']} - {node['type']}", expanded=True):
                                                if node.get("expression"):
                                                    st.write(f"**Expr:** `{node['expression']}`")
                                                if node.get("lines"):
                                                    st.write(f"**Lines:** `{node['lines']}`")
                                                
                                                ir_list = node.get("ir", [])
                                                if ir_list:
                                                    st.write("**SlithIR Instructions:**")
                                                    for ir in ir_list:
                                                        st.code(ir, language="python")
                                                
                                                st.write(f"→ Successors: `{node['successors']}` | ← Predecessors: `{node['predecessors']}`")
                else:
                    try:
                        err_msg = response.json().get("detail", "Unknown backend error")
                    except Exception:
                        err_msg = response.text
                    st.error(f"FAILED TO EXTRACT CFG FROM BACKEND: {err_msg}")
            except Exception as e:
                st.error(f"BACKEND OFFLINE: {e}")

else:
    # Landing / Capabilities
    st.divider()
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### SLITHER")
        st.write("Fast static analysis that detects common vulnerabilities, optimization issues, and security best practices in seconds.")
        
    with c2:
        st.markdown("### MYTHRIL")
        st.write("Advanced security analysis using symbolic execution to discover complex logical bugs and deep reentrancy paths.")
        
    with c3:
        st.markdown("### SOLHINT")
        st.write("Comprehensive linter that enforces style guide consistency and identifies potential security pitfalls in code structure.")
    
    st.info("UPLOAD A .SOL FILE TO INITIATE UNIFIED AUDIT")
