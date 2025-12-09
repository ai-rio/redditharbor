#!/usr/bin/env python3
"""Script to properly add _track_agent_completion method"""

# Read the file
file_path = '/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py'
with open(file_path) as f:
    content = f.read()

# Replace the malformed section
old_content = '''    def a_run(self, prompt: str, *args, **kwargs):
        """Override Agno's a_run method to add AgentOps tracking"""
        return super().a_run(prompt, *args, **kwargs)

        """Track agent completion metrics and session lifecycle"""
        pass

        """Override Agno\'s a_run method to add AgentOps tracking"""
        return super().a_run(prompt, *args, **kwargs)'''

new_content = '''    def a_run(self, prompt: str, *args, **kwargs):
        """Override Agno's a_run method to add AgentOps tracking"""
        return super().a_run(prompt, *args, **kwargs)

    def _track_agent_completion(self, result, success: bool = True, error: Optional[str] = None) -> None:
        """Track agent completion metrics and session lifecycle"""
        pass'''

# Replace the content
fixed_content = content.replace(old_content, new_content)

# Write back to file
with open(file_path, 'w') as f:
    f.write(fixed_content)

print("Properly added _track_agent_completion method")
