#!/usr/bin/env python3
"""Script to add extract_and_track_cost method to AgnoOpportunityAnalyzer"""

# Read the file
file_path = '/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_analyzer.py'
with open(file_path) as f:
    content = f.read()

# Find the end_analysis_session method and add new method after it
pattern = r'(def end_analysis_session\(self, status: str\) -> dict:\s*"""End analysis session"""\s*return \{"status": status\})'

replacement = r'\1\n\n    def extract_and_track_cost(self, response: dict) -> dict:\n        """Extract and track costs from API response"""\n        return {"cost": 0.0, "currency": "USD", "tracked": False}'

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back to file
with open(file_path, 'w') as f:
    f.write(new_content)

print("Added extract_and_track_cost method stub to AgnoOpportunityAnalyzer")
