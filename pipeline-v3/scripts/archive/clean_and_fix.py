#!/usr/bin/env python3
"""Clean and fix the file properly"""

# Read the file
with open('/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py') as f:
    content = f.read()

# Replace the problematic section with properly formatted code
old_problematic = '''    def a_run(self, prompt: str, *args, **kwargs):
    """Override Agno's a_run method to add AgentOps tracking"""
    return super().a_run(prompt, *args, **kwargs)

    def _track_agent_completion(self, result, success: bool = True, error: Optional[str] = None) -> None:
        """Track agent completion metrics and session lifecycle"""
        pass

        """Override Agno's a_run method to add AgentOps tracking"""
        return super().a_run(prompt, *args, **kwargs)

        """Track agent completion metrics and session lifecycle"""
        pass'''

new_proper = '''    def a_run(self, prompt: str, *args, **kwargs):
        """Override Agno's a_run method to add AgentOps tracking"""
        return super().a_run(prompt, *args, **kwargs)

    def _track_agent_completion(self, result, success: bool = True, error: Optional[str] = None) -> None:
        """Track agent completion metrics and session lifecycle"""
        pass'''

# Replace the content
fixed_content = content.replace(old_problematic, new_proper)

# Write back to file
with open('/home/carlos/projects/redditharbor-core-functions-fix/pipeline-v3/transform/agno_agents.py', 'w') as f:
    f.write(fixed_content)

print("File properly fixed")
