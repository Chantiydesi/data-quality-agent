import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Force load the .env file explicitly
load_dotenv()

class RemediationSuggestion(BaseModel):
    explanation: str = Field(description="Clear explanation of why the data failed.")
    root_cause_hypothesis: str = Field(description="A technical guess on what went wrong upstream.")
    pandas_fix: str = Field(description="Clean, executable Pandas code to fix this specific issue.")
    sql_fix: str = Field(description="SQL query snippet (using a CASE WHEN or WHERE clause) to clean the data.")

class DQAgent:
    def __init__(self):
        # Fetch the key from os.environ and pass it directly to the client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing from your .env file or the file is named incorrectly!")
        
        self.client = genai.Client(api_key=api_key)

    def generate_fix(self, failure_context: dict, schema_summary: str) -> RemediationSuggestion:
        prompt = f"""
        You are an expert Data Engineering Quality Agent. A data quality check has failed.
        
        DATASET SCHEMA CONTEXT:
        {schema_summary}
        
        FAILED VIOLATION:
        Column Evaluated: {failure_context['column']}
        Assertion Violated: {failure_context['assertion']}
        Rule Specs: {failure_context['rule_details']}
        Total Impacted Rows: {failure_context['total_failed_rows']}
        
        SAMPLE BAD DATA ROWS CAUGHT:
        {failure_context['sample_bad_rows']}
        
        Provide a concise human explainer, a technical root-cause hypothesis, and precise Pandas and SQL code snippets to clean/remediate this error.
        """

        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RemediationSuggestion,
            ),
        )
        
        return RemediationSuggestion.model_validate_json(response.text)
