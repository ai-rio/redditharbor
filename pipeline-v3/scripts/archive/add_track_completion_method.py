#!/usr/bin/env python3
"""Script to add minimal _track_agent_completion method stub to BaseAgent"""

import re

# Read the file
file_path = '/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py'
with open(file_path) as f:
    content = f.read()

# Find the a_run method and add _track_agent_completion method after it
pattern = r'(def a_run\(self, prompt: str, \*args, \*\*kwargs\):\s*"""Override Agno\'s a_run method to add AgentOps tracking"""\s*return super\(\)\.a_run\(prompt, \*args, \*\*kwargs\))'

replacement = r'\1\n\n    def _track_agent_completion(self, result, success: bool = True, error: Optional[str] = None) -> None:\n        """Track agent completion metrics and session lifecycle"""\n        pass'

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back to file
with open(file_path, 'w') as f:
    f.write(new_content)

print("Added _track_agent_completion method stub to BaseAgent")
