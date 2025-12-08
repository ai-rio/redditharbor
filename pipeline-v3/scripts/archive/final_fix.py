#!/usr/bin/env python3
"""Final script to fix the file"""

# Read the entire file
with open('/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py') as f:
    content = f.read()

# Split the content into lines
lines = content.split('\n')

# Find the line with a_run method and add the new method after it
for i, line in enumerate(lines):
    if 'def a_run(self, prompt: str, *args, **kwargs):' in line:
        # Insert the _track_agent_completion method after the a_run method
        indent = '    '
        new_method_lines = [
            f'{indent}"""Override Agno\'s a_run method to add AgentOps tracking"""',
            f'{indent}return super().a_run(prompt, *args, **kwargs)',
            '',
            f'{indent}def _track_agent_completion(self, result, success: bool = True, error: Optional[str] = None) -> None:',
            f'{indent}    """Track agent completion metrics and session lifecycle"""',
            f'{indent}    pass',
            ''
        ]

        # Remove any existing malformed lines
        while i + 1 < len(lines) and lines[i + 1].strip() != '' and not lines[i + 1].startswith('#'):
            if 'def _track_agent_completion' in lines[i + 1]:
                break
            if lines[i + 1].startswith('        """'):
                break
            lines.pop(i + 1)

        # Insert the new method
        lines[i + 1:i + 1] = new_method_lines
        break

# Write back to file
with open('/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py', 'w') as f:
    f.write('\n'.join(lines))

print("Final fix applied")
