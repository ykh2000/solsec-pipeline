# SolSec Pipeline

SolSec Pipeline is a **Unified Smart Contract Analysis Pipeline** designed to audit Solidity smart contracts for security vulnerabilities, control flow anomalies, and style inconsistencies. 

By orchestrating static analysis, symbolic execution, and linting, SolSec aggregates findings, deduplicates issues, calculates security scores, and generates control flow graphs (CFGs) with interactive visualizations.

---

## Key Features

1. **Multi-Tool Orchestration**:
   - **Slither**: Fast static analysis for common vulnerabilities and optimization opportunities.
   - **Mythril**: Symbolic execution for deep logical bugs and reentrancy vectors.
   - **Solhint**: Solidity linting for style guide adherence and code quality.
2. **Dynamic Compiler Resolution**:
   - Automatically reads the `pragma solidity` directive from contracts and uses `solc-select` to dynamically switch to the appropriate compiler version.
3. **Intelligent Deduplication & Scoring**:
   - Combines findings from multiple tools pointing to the same line/issue into a single consolidated finding.
   - Assigns a standardized security score based on severity.
4. **CFG Extraction & Visualization**:
   - Parses the control flow of smart contracts and generates interactive Mermaid diagrams of functions and modifiers.
5. **Modern Dashboard UI**:
   - Clean, high-contrast dashboard built with Streamlit, enabling contract uploading, reports viewing, and interactive control flow charts.

---

## Prerequisites

Before setting up the pipeline, ensure the following are installed on your system:

- **Python**: Version `3.8` up to `3.14`
- **Node.js & npm**: (Required for Solhint)
- **Solidity Compilers**: Handled dynamically, but requires `solc-select` for version management.

---

## Setup & Installation

### 1. Set Up the Python Virtual Environment
Clone this repository and navigate to the project directory:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows (cmd):
.venv\Scripts\activate.bat
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Install External Security Tools

#### A. Slither
Slither is installed as a Python dependency in `requirements.txt`. Verify it runs:
```bash
slither --version
```
*Note: Slither requires `solc` to compile contracts.*

#### B. Solhint
Install Solhint globally or locally using `npm`:
```bash
npm install -g solhint
```
Verify the installation:
```bash
solhint --version
```

#### C. Mythril
Mythril is best installed via pip:
```bash
pip install mythril
```
Verify the installation:
```bash
myth --version
```

### 3. Configure Solidity Compilers via `solc-select`
The compiler resolver relies on `solc-select` to dynamically switch compiler versions.
```bash
# Install specific solc versions (e.g. 0.8.0, 0.4.24, etc.)
solc-select install 0.8.0

# Set 0.8.0 as the active version initially
solc-select use 0.8.0
```

---

## Running the Pipeline

The SolSec pipeline runs as a split architecture with a FastAPI backend and a Streamlit frontend.

### 1. Run the Backend API
Start the FastAPI server (it serves the analysis and CFG extraction endpoints):
```bash
uvicorn backend.main:app --reload --port 8000
```
- API Docs will be available at: `http://localhost:8000/docs`
- Analysis Endpoint: `POST http://localhost:8000/analyze`
- CFG Extraction Endpoint: `POST http://localhost:8000/cfg`

### 2. Run the Frontend App
In a separate terminal window (with the virtual environment active), start the Streamlit web application:
```bash
streamlit run frontend/app.py
```
- This will open `http://localhost:8501` in your browser.
- Simply drag-and-drop or upload a `.sol` contract file to run the audit and view the Control Flow Graph.

---

## How to Test

We use `pytest` for unit and integration testing.

### 1. Run the Automated Test Suite
Ensure the virtual environment is active, then execute:
```bash
pytest
```
This runs the full test suite in the `tests/` directory:
- [tests/test_api.py](file:///Users/yashkhanduja/Documents/solsec-pipeline/tests/test_api.py): Validates API endpoints, input validation, and successful analysis responses.
- [tests/test_orchestrator.py](file:///Users/yashkhanduja/Documents/solsec-pipeline/tests/test_orchestrator.py): Validates backend plugin discovery and multi-tool execution.
- [tests/test_processor.py](file:///Users/yashkhanduja/Documents/solsec-pipeline/tests/test_processor.py): Verifies find deduplication, severity promotions, and scoring logic.

### 2. Run the Unified Test Script
There is a standalone pipeline execution test script. You can run it directly:
```bash
python test_pipeline.py
```
This script runs the core orchestrator locally on [tests/sample_vulnerable.sol](file:///Users/yashkhanduja/Documents/solsec-pipeline/tests/sample_vulnerable.sol) without needing the FastAPI or Streamlit servers running, printing a formatted security report directly to the terminal.
