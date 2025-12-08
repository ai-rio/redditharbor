#!/usr/bin/env python3
"""Script to add minimal a_run method stub to BaseAgent"""

import re

# Read the file
file_path = '/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py'
with open(file_path) as f:
    content = f.read()

# Find the _get_default_name method and add a_run method after it
pattern = r'(def _get_default_name\(self\) -> str:\s*"""Get default agent name"""\s*return self\.__class__\.__name__\.replace\(\'Agent\', \'\'\))'

replacement = r'\1\n\n    def a_run(self, prompt: str, *args, **kwargs):\n        """Override Agno\'s a_run method to add AgentOps tracking"""\n        return super().a_run(prompt, *args, **kwargs)'

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back to file
with open(file_path, 'w') as f:
    f.write(new_content)

print("Added a_run method stub to BaseAgent")
