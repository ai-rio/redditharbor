#!/usr/bin/env python3
"""Script to fix syntax error in agno_agents.py"""

# Read the file
file_path = '/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py'
with open(file_path) as f:
    content = f.read()

# Fix the syntax error by replacing the malformed section
old_section = '''    def a_run(self, prompt: str, *args, **kwargs):

    def _track_agent_completion(self, result, success: bool = True, error: Optional[str] = None) -> None:
        """Track agent completion metrics and session lifecycle"""
        pass

        """Override Agno\'s a_run method to add AgentOps tracking"""
        return super().a_run(prompt, *args, **kwargs)'''

new_section = '''    def a_run(self, prompt: str, *args, **kwargs):
        """Override Agno\'s a_run method to add AgentOps tracking"""
        return super().a_run(prompt, *args, **kwargs)

    def _track_agent_completion(self, result, success: bool = True, error: Optional[str] = None) -> None:
        """Track agent completion metrics and session lifecycle"""
        pass'''

# Replace the problematic section
fixed_content = content.replace(old_section, new_section)

# Write back to file
with open(file_path, 'w') as f:
    f.write(fixed_content)

print("Fixed syntax error in agno_agents.py")
