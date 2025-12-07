# TDD-Guard Testing Instructions

## How to Test TDD-Guard After Restart

### Step 1: Restart Claude Code Session
1. Exit this session completely
2. Start a new Claude Code session in this project
3. Come back to this file

### Step 2: Run Test Scenarios

Ask Claude to do these tasks **in order**. TDD-Guard should block the implementation attempts.

---

## Test Scenario 1: Write Implementation Without Test (Should BLOCK)

**Prompt to Claude:**
```
Create a new file utils/string_helpers.py with a function called reverse_string()
that reverses a string.
```

**Expected Result:**
```
❌ TDD-Guard BLOCKS this because:
- No test exists for reverse_string()
- You must write a failing test first
```

---

## Test Scenario 2: Write Test First (Should ALLOW)

**Prompt to Claude:**
```
Write a test in tests/test_string_helpers.py that tests a reverse_string()
function. The test should fail because the function doesn't exist yet.
```

**Expected Result:**
```
✅ TDD-Guard ALLOWS this because:
- Writing a test is the correct first step in TDD
- Test file created successfully
```

---

## Test Scenario 3: Now Implement (Should ALLOW)

**Prompt to Claude:**
```
Now implement the reverse_string() function to make the test pass.
```

**Expected Result:**
```
✅ TDD-Guard ALLOWS this because:
- A failing test exists
- Implementation is minimal (just makes test pass)
- Pytest runs automatically and confirms tests pass
```

---

## Test Scenario 4: Add Feature Without Test (Should BLOCK)

**Prompt to Claude:**
```
Add a new function capitalize_first() to utils/string_helpers.py that
capitalizes the first letter of each word.
```

**Expected Result:**
```
❌ TDD-Guard BLOCKS this because:
- No test exists for capitalize_first()
- Must follow red-green-refactor cycle
```

---

## Success Criteria

TDD-Guard is working correctly if:
- ✅ Scenario 1: BLOCKED (no test exists)
- ✅ Scenario 2: ALLOWED (writing test)
- ✅ Scenario 3: ALLOWED (implementing to pass test)
- ✅ Scenario 4: BLOCKED (new feature without test)

---

## If TDD-Guard Doesn't Block

If Claude writes code without being blocked, check:

1. **Session restart:** Did you actually restart? Hooks only load on session start
2. **Hook configuration:** Run `cat .claude/settings.local.json | jq '.hooks'`
3. **TDD-Guard CLI:** Run `which tdd-guard` to verify it's accessible
4. **Pytest plugin:** Run `uv pip list | grep tdd-guard`

---

## Quick Verification Commands

Run these to verify installation:

```bash
# Check TDD-Guard CLI is accessible
which tdd-guard

# Check hooks are configured
cat .claude/settings.local.json | jq '.hooks'

# Check pytest plugin is installed
uv pip list | grep tdd-guard

# Check pytest configuration
grep -A 2 "tdd_guard_project_root" pyproject.toml
```

---

## Alternative: Manual Hook Test

You can manually test the hook without restarting:

```bash
# Create a fake hook input
echo '{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "test_new_feature.py",
    "content": "def new_function(): pass"
  }
}' | tdd-guard
```

This should show TDD-Guard's validation output.

---

## Notes

- TDD-Guard only enforces TDD for **new code**
- It won't block edits to existing files (unless adding new functions)
- You can temporarily disable by removing hooks from settings
- For custom validation rules, see: https://github.com/nizos/tdd-guard#custom-instructions
