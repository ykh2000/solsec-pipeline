import streamlit as st
import requests
import json
import pandas as pd

st.set_page_config(page_title="SolSec Pipeline", layout="wide")

st.title("🛡️ SolSec: Unified Smart Contract Analysis")
st.markdown("Upload a Solidity smart contract to run a consolidated security scan.")

uploaded_file = st.file_uploader("Choose a .sol file", type="sol")

if uploaded_file is not None:
    st.info(f"Analyzing {uploaded_file.name}...")
    
    # Prepare the file for the POST request
    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
    
    try:
        # Call the FastAPI backend
        response = requests.post("http://localhost:8000/analyze", files=files)
        
        if response.status_code == 200:
            final_report = response.json()
            findings = final_report.get("findings", [])
            
            total_findings = len(findings)
            st.success(f"Analysis Complete! Found {total_findings} deduplicated findings.")
            
            if total_findings > 0:
                # Flatten findings for display in a table
                flat_findings = []
                for f in findings:
                    flat_findings.append({
                        "Tool": f["tool"],
                        "Severity": f["severity"],
                        "Score": f.get("metadata", {}).get("security_score", 0),
                        "Title": f["title"],
                        "Description": f["description"][:200] + "...",
                        "File": f["file_path"]
                    })
                
                df = pd.DataFrame(flat_findings)
                
                # Show summary metrics
                cols = st.columns(4)
                cols[0].metric("Deduplicated Findings", total_findings)
                cols[1].metric("High Severity", len(df[df["Severity"] == "High"]))
                cols[2].metric("Average Score", round(df["Score"].mean(), 1))
                cols[3].metric("Raw Alerts", final_report.get("metadata", {}).get("total_raw_findings", 0))
                
                st.subheader("Consolidated Security Report")
                st.dataframe(df.sort_values(by="Score", ascending=False), use_container_width=True)
                
                # Details
                for i, f in enumerate(findings, 1):
                    with st.expander(f"{i}. [{f['severity']}] {f['title']} (Score: {f.get('metadata', {}).get('security_score', 0)})"):
                        st.markdown(f"**Detected by:** {f['tool']}")
                        st.markdown(f"**Location:** {f['file_path']} - Lines: {f['line_number']}")
                        st.text(f["description"])
                        if f.get("metadata", {}).get("tools"):
                             st.info(f"Consolidated from tools: {', '.join(f['metadata']['tools'])}")
                        st.divider()
            else:
                st.balloons()
                st.info("No vulnerabilities found! Your contract looks clean.")
                
        else:
            st.error(f"Error from Backend: {response.status_code} - {response.text}")
            
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")

st.sidebar.title("About")
st.sidebar.info(
    "This pipeline integrates multiple security tools for Ethereum smart contracts."
)
