import pandas as pd
import json
import os
from openai import OpenAI
from src.detector import DQDetector

# --- Bridge Helper ---
class RemediationResult:
    """Matches the structure your existing print statements expect."""
    def __init__(self, data):
        self.explanation = data.get("explanation", "N/A")
        self.root_cause_hypothesis = data.get("root_cause_hypothesis", "N/A")
        self.pandas_fix = data.get("pandas_fix", "# No code generated")
        self.sql_fix = data.get("sql_fix", "-- No code generated")

def generate_fix_with_openai(client, failure, schema_summary):
    """Calls OpenAI and returns a structure compatible with your existing print logic."""
    prompt = f"""
    You are a Data Quality Agent. Audit this failure: {failure}. 
    Schema: {schema_summary}. 
    Return ONLY a JSON object with these keys: 
    'explanation', 'root_cause_hypothesis', 'pandas_fix', 'sql_fix'.
    """
    
    # Using 'gpt-4o-mini' for a cost-effective, high-performance option
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    # Parse the response and map to your existing structure
    data = json.loads(response.choices[0].message.content)
    return RemediationResult(data)

# --- Main Logic ---
def main():
    csv_path = "data/sample_data.csv"
    config_path = "config/rules.yaml"

    print("Step 1: Loading Dataset...")
    df = pd.read_csv(csv_path)
    schema_summary = str(df.dtypes.to_dict())

    print("Step 2: Executing Data Quality Checks...")
    detector = DQDetector(config_path)
    failures = detector.scan_data(df)

    if not failures:
        print("✅ Success! All data quality checks passed successfully.")
        return

    print(f"❌ Found {len(failures)} Data Quality Failure(s). Invoking OpenAI Agent...\n")
    
    # Initialize OpenAI Client
    # Ensure OPENAI_API_KEY is in your environment variables
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    for idx, failure in enumerate(failures, 1):
        print(f"=== Remediation Report for Failure #{idx} ===")
        print(f"Target Column: {failure['column']} | Violation: {failure['assertion']}")
        
        try:
            # Call the new helper instead of agent.generate_fix()
            remediation = generate_fix_with_openai(client, failure, schema_summary)
            
            # Your original print statements remain identical
            print("\n📝 EXPLANATION:")
            print(remediation.explanation)
            print("\n🔍 ROOT CAUSE HYPOTHESIS:")
            print(remediation.root_cause_hypothesis)
            print("\n🐼 PANDAS REMEDIATION CODE:")
            print(remediation.pandas_fix)
            print("\n🗄️ SQL REMEDIATION SNIPPET:")
            print(remediation.sql_fix)
            
        except Exception as e:
            print(f"\n❌ Error calling OpenAI API: {e}")
            print("Check your OPENAI_API_KEY and environment configuration.")
            
        print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
