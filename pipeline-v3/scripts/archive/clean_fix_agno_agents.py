#!/usr/bin/env python3
"""Script to clean up agno_agents.py"""

# Read the file
file_path = '/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py'
with open(file_path) as f:
    lines = f.readlines()

# Find and fix the problematic section
fixed_lines = []
for i, line in enumerate(lines):
    if 'def a_run(self, prompt: str, *args, **kwargs):' in line:
        # Add proper a_run implementation
        fixed_lines.append(line)
        fixed_lines.append('        """Override Agno\'s a_run method to add AgentOps tracking"""\n')
        fixed_lines.append('        return super().a_run(prompt, *args, **kwargs)\n')
        # Skip the malformed lines
        while i + 1 < len(lines) and not lines[i + 1].strip().startswith('#') and lines[i + 1].strip() != '':
            if 'def _track_agent_completion' in lines[i + 1]:
                # Add the _track_agent_completion method properly
                fixed_lines.append(lines[i + 1])
                fixed_lines.append(lines[i + 2])
                fixed_lines.append(lines[i + 3])
                fixed_lines.append('\n')
                break
            i += 1
    elif not ('def _track_agent_completion' in line and i > 0):
        fixed_lines.append(line)

# Write back to file
with open(file_path, 'w') as f:
    f.writelines(fixed_lines)

print("Cleaned up agno_agents.py")
