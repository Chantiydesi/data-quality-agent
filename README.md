# data-quality-agent
An AI-powered Data Quality Agent that detects pipeline failures using declarative rules and leverages Gemini to auto-draft Pandas and SQL fixes.

# DQ-Agent: Automated Data Quality & Auto-Fix Pipeline

Welcome to the `dq-agent` project! This application serves as an intelligent data quality pipeline. It not only detects anomalies and errors in your datasets (like mixing text with floats) but also uses AI to generate and safely execute Python code to fix those issues in real-time. 

Here is a complete breakdown of how the project is structured, built, and executed.

---

## 1. Project Setup & Environment

### Setting up the Workspace
* **Project Folder:** We use a dedicated root directory named `dq-agent` to keep the workspace isolated and avoid dependency conflicts.
* **Environment Variables (`.env`):** To keep our credentials secure, the `GEMINI_API_KEY` is stored in a local `.env` file rather than being hardcoded into the scripts.
* **Version Control (`.gitignore`):** A `.gitignore` file is included to prevent accidentally pushing sensitive data (like the `.env` file, `__pycache__` folders, and raw `.csv` data logs) to GitHub.
* **Dependencies (`requirements.txt`):** All necessary Python libraries and their specific versions are tracked here so anyone can easily recreate the exact environment.

---

## 2. Installation & Configuration

### Python Dependencies
To get the app running, we install our core stack via `pip`. The main libraries powering this tool are:
* `streamlit` (for the UI)
* `pandas` & `numpy` (for data manipulation)
* `requests` (for API calls)
* `python-dotenv` (for loading secure keys)

### Defining Data Rules (`rules.yaml`)
Instead of hardcoding validation logic, we use a central `rules.yaml` file. This acts as our blueprint, defining required columns, expected data types, and numerical boundaries for specific industries (like Finance or Healthcare).

---

## 3. UI & Application Architecture

### Building the Interface
* **Streamlit Layout:** The app runs on Streamlit in a widescreen layout. We use a tabbed interface (`st.tabs`) to keep the raw data exploration separate from the AI diagnostics panel.
* **Interactive Sidebar:** A fixed sidebar handles app navigation and includes a toggle to pause or activate the AI processing engine on the fly.
* **Custom Styling:** We injected a bit of custom CSS (`unsafe_allow_html=True`) to override the default Streamlit theme, giving the app professional dark UI cards and clean margins.
* **Team Info:** The sidebar also cleanly displays our academic team credentials and branch roll numbers.

---

## 4. Connecting to the AI (Generative Gateway)

* **Dynamic Pathing:** The app uses Python's `Path` library to automatically locate the `.env` file, so the app runs smoothly regardless of where you launch it from in your terminal.
* **Failsafes:** Before making any web requests, the app checks if the API key is present. If it's missing, it gracefully pauses and shows a helpful error banner instead of crashing.
* **JSON Payloads:** When talking to the model, we strictly enforce a `responseMimeType: application/json` rule. This ensures the AI always replies in a predictable format that our app can parse easily.

---

## 5. How the Data Pipeline Works

### Tab 1: Uploading & Inspecting
* **Caching Data:** When you upload a CSV, we store it in `st.session_state`. This stops the app from sluggishly reloading the file every time you click a button.
* **Previewing:** We immediately display a clean grid preview (`df.head(10)`) so you can visually verify the raw data formatting.

### Tab 2: AI Diagnostics
* **Context Assembly:** The app programmatically combines the constraints from `rules.yaml` with 10 actual rows of your uploaded data, giving the AI perfect context.
* **The Audit:** The AI model acts as our auditor. It flags out-of-bounds metrics, translates technical errors into plain English, assigns a severity score (High/Medium/Low), and suggests a fix.
* **Displaying Results:** We parse the AI's JSON response and inject it into clean, expandable UI cards (`st.expander`) so you can review the issues side-by-side.

---

## 6. The Real-Time Auto-Fix Engine

This is where the magic happens:
* **AI Code Generation:** Once an issue is found, we prompt the AI to write a pure block of Python (Pandas) code to fix the specific anomaly (e.g., stripping currency symbols so a column can be converted to floats).
* **Safe Sandboxing:** We create an isolated Python environment map (`local_env`) so the generated code has a safe space to interact with a copy of your dataframe.
* **Live Execution:** We use Python’s built-in `exec()` function to run the AI's patch live, fixing the dataset instantly. 

---

## 7. Exporting the Results

* **Refreshing the UI:** After the data is healed, the app automatically refreshes (`st.rerun()`) to show you the clean dataset right next to the exact Python code that fixed it.
* **Memory Management:** We convert the repaired dataframe into a text stream buffer (`io.StringIO`). This lets us package the data for download without cluttering your hard drive with temporary junk files.
* **Download Button:** Finally, a simple click lets you download your sparkling-clean CSV file, ready for production use.

---

## 📂 Visualizing the Architecture

### Project Structure

```text
dq-agent/                     
│
├── .env                      <-- Secure API Keys (Ignored by Git)
├── .gitignore                <-- Keeps sensitive files out of version control
├── rules.yaml                <-- Centralized validation rules
├── app.py                    <-- Main Streamlit application
└── requirements.txt          <-- Python dependencies
