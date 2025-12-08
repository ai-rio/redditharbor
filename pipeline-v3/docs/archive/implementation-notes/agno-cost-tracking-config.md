# Agno Cost Tracking Configuration Requirements

## Missing Configuration Identified

Based on the audit report, the following configuration is missing from `config/settings.py`:

### Required Configuration: AGNO_TRACK_COSTS

**Environment Variable**: `AGNO_TRACK_COSTS`
**Default Value**: `true`
**Type**: Boolean
**Description**: Enable cost tracking for Agno agent operations

## Configuration Details

```python
# In config/settings.py, add this field:

agno_track_costs: bool = Field(
    default=True,
    alias="AGNO_TRACK_COSTS",
    description="Enable cost tracking for Agno agent operations"
)
```

## Usage Context

This configuration is referenced in:

1. **Branch Plan** (`docs/implementation/BRANCH_PLAN.md`):
   - Lists `AGNO_TRACK_COSTS=true` as a required configuration

2. **AgentOps Integration**:
   - Used to determine whether to track costs for Agno agents
   - Integrates with AgentOps for cost monitoring

3. **Cost Monitoring System**:
   - Controls cost tracking functionality in Agno analyzer
   - Works alongside `AGNO_ENABLE_AGENTOPS` for complete observability

## Related Configurations

The `AGNO_TRACK_COSTS` setting works alongside:

- `AGNO_ENABLE_AGENTOPS`: Enable AgentOps tracking
- `AGNO_DEBUG_MODE`: Enable debug mode for enhanced logging

## Implementation Priority

**Priority**: High
**Reason**: Required by audit report
**Impact**: Without this configuration, cost tracking for Agno agents cannot be properly enabled