import pandas as pd
import yaml
from typing import List, Dict, Any

class DQDetector:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def scan_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        failures = []
        
        for rule in self.config['rules']:
            col = rule['column']
            assertion = rule['assertion']
            bad_mask = pd.Series(False, index=df.index)

            if assertion == 'is_not_null':
                bad_mask = df[col].isnull()
                
            elif assertion == 'is_greater_than_or_equal_to':
                bad_mask = df[col] < rule['value']
                
            elif assertion == 'is_in_set':
                bad_mask = df[col].notnull() & (~df[col].isin(rule['values']))

            if bad_mask.any():
                failed_rows_samples = df[bad_mask].head(3).to_dict(orient='records')
                failures.append({
                    "column": col,
                    "assertion": assertion,
                    "rule_details": rule,
                    "sample_bad_rows": failed_rows_samples,
                    "total_failed_rows": int(bad_mask.sum())
                })
                
        return failures
