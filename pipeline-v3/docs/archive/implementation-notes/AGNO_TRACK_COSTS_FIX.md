# Fix for Missing AGNO_TRACK_COSTS Configuration

## Issue Identified

Audit Report: "AGNO_TRACK_COSTS=true not found in settings"

## Solution

Add the following configuration to `config/settings.py`:

### Location
Insert after line 93 (after `agno_enable_agentops` field):

### Code to Add
```python
agno_track_costs: bool = Field(
    default=True,
    alias="AGNO_TRACK_COSTS",
    description="Enable cost tracking for Agno agent operations"
)
```

### Full Context
```python
# Around line 89-100 in config/settings.py:

agno_enable_agentops: bool = Field(
    default=False,
    alias="AGNO_ENABLE_AGENTOPS",
    description="Enable AgentOps tracking for Agno agents"
)
agno_track_costs: bool = Field(
    default=True,
    alias="AGNO_TRACK_COSTS",
    description="Enable cost tracking for Agno agent operations"
)
max_tokens: int = Field(
    default=2000,
    description="Maximum tokens for LLM responses"
)
```

## Additional Requirements

1. **Remove Duplicate Field**: There's a duplicate `agno_enable_agentops` field around line 190. Remove this duplicate to clean up the settings file.

2. **Environment Variable Support**: The configuration will support:
   - Default value: `True` (cost tracking enabled by default)
   - Environment variable: `AGNO_TRACK_COSTS`
   - Can be overridden with `false` to disable cost tracking

## Testing

After implementing this fix:

1. Run the configuration test:
   ```python
   from config.settings import Settings
   settings = Settings.create_for_testing()
   assert hasattr(settings, 'agno_track_costs')
   assert settings.agno_track_costs == True  # Default value
   ```

2. Test with environment variable:
   ```bash
   export AGNO_TRACK_COSTS=false
   python -c "from config.settings import Settings; print(Settings().agno_track_costs)"
   # Should print: False
   ```

## Compliance

This fix addresses the audit requirement and follows the existing pattern in settings.py for:
- Using `Field` from Pydantic
- Providing a default value
- Using an environment variable alias
- Including clear description
- Using snake_case for Python attribute name
- Using UPPER_CASE for environment variable name

## Documentation Update

The configuration is now documented in:
- `docs/integrations/agno-cost-tracking-config.md`
- `docs/implementation/BRANCH_PLAN.md` (reference)
- This file for implementation guidance