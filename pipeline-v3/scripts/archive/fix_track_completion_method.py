#!/usr/bin/env python3
"""Script to add _track_agent_completion method to BaseAgent"""

# Read the file
file_path = '/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py'
with open(file_path) as f:
    lines = f.readlines()

# Find the line with a_run method and insert new method after it
for i, line in enumerate(lines):
    if 'def a_run(self, prompt: str, *args, **kwargs):' in line:
        # Insert the new method after the a_run method
        indent = '    '
        new_method = [
            '\n',
            f'{indent}def _track_agent_completion(self, result, success: bool = True, error: Optional[str] = None) -> None:\n',
            f'{indent}    """Track agent completion metrics and session lifecycle"""\n',
            f'{indent}    pass\n',
            '\n'
        ]
        lines[i+1:i+1] = new_method
        break

# Write back to file
with open(file_path, 'w') as f:
    f.writelines(lines)

print("Added _track_agent_completion method to BaseAgent")
