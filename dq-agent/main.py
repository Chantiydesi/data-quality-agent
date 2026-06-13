import pandas as pd
from src.detector import DQDetector
from src.agent import DQAgent

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

    print(f"❌ Found {len(failures)} Data Quality Failure(s). Invoking Gemini Agent...\n")
    agent = DQAgent()

    for idx, failure in enumerate(failures, 1):
        print(f"=== Remediation Report for Failure #{idx} ===")
        print(f"Target Column: {failure['column']} | Violation: {failure['assertion']}")
        
        try:
            remediation = agent.generate_fix(failure, schema_summary)
            
            print("\n📝 EXPLANATION:")
            print(remediation.explanation)
            
            print("\n🔍 ROOT CAUSE HYPOTHESIS:")
            print(remediation.root_cause_hypothesis)
            
            print("\n🐼 PANDAS REMEDIATION CODE:")
            print(remediation.pandas_fix)
            
            print("\n🗄️ SQL REMEDIATION SNIPPET:")
            print(remediation.sql_fix)
        except Exception as e:
            print(f"\n❌ Error calling Gemini API: {e}")
            print("Make sure your GEMINI_API_KEY is set correctly in your .env file.")
            
        print("=" * 50 + "\n")

if __name__ == "__main__":
    main()
