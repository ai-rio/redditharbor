# RedditHarbor Pipeline v3 - Claude Code Hooks

This directory contains hooks that enforce file organization standards for the RedditHarbor Pipeline v3 project (ELT Architecture).

## Hook Descriptions

### 1. `validate-file-structure.py`
**Purpose**: Prevents creation of unnecessary files at the project root and enforces proper file organization.

**Rules enforced**:
- Only allowed files can be created at project root (`README.md`, `main.py`, `pyproject.toml`, etc.)
- All markdown files (except `README.md`) must go in `docs/`
- Python files (except `main.py` and `__init__.py`) must go in `core/`
- Configuration files should go in `config/`
- Scripts should go in `scripts/`

### 2. `check-doc-structure.py`
**Purpose**: Validates the documentation organization in the `docs/` directory.

**Rules enforced**:
- Required directories exist (`api/`, `architecture/`, `components/`, etc.)
- No orphan files in `docs/` root (except `README.md`)
- Files use kebab-case naming convention
- Directories are not empty

## Installation

### Prerequisites
- Python 3.12+
- uv (installed)
- Claude Code with hooks support

### Setup

1. **Install dependencies**:
   ```bash
   uv add "click>=8.0.0" "watchfiles>=0.20.0" "jsonschema>=4.0.0"
   ```

2. **Make scripts executable**:
   ```bash
   chmod +x scripts/hooks/*.py
   ```

3. **Configure Claude Code hooks**:
   The hooks configuration is in `.claude/hooks.json` and includes:
   - **PreToolUse**: Validates file structure before Write/Edit operations
   - **PostToolUse**: Checks documentation structure after creating files in `docs/`

## Usage

### Manual Testing

Test file structure validation:
```bash
uv run scripts/hooks/validate-file-structure.py --tool-name Write --file-paths test-file.py bad-doc.md
```

Test documentation structure:
```bash
uv run scripts/hooks/check-doc-structure.py --docs-path docs
```

### Integration with Claude Code

The hooks automatically run when:
- You try to create or edit files (PreToolUse hook)
- You create files in the `docs/` directory (PostToolUse hook)

## Configuration

### Allowed Root Files

The following files are allowed at the project root:
- `README.md`
- `__init__.py`
- `main.py`
- `pyproject.toml`
- `requirements.txt`
- `uv.lock`
- `.env` / `.env.example`
- `.gitignore`
- `CLAUDE.md`
- `ai-rulez.yaml`
- `lint.sh`
- `pytest.ini`
- `ruff.toml`

### File Type Rules (ELT Architecture)

| File Type | Default Location | Pattern Matching | Notes |
|-----------|------------------|------------------|-------|
| `.py` | **Pattern-based** | Intelligent placement | See patterns below |
| `.md` | `docs/` | N/A | Except `README.md` at root |
| `.json` | `config/` | N/A | Except specific report files at root |
| `.yaml/.yml` | `config/` | N/A | Configuration files |
| `.sh` | `scripts/` | N/A | Shell scripts |
| `.sql` | `scripts/database/` | N/A | SQL files |
| `.log` | `error_log/` | N/A | Log files |

#### Python File Pattern Matching

| Directory | File Name Patterns | Examples |
|-----------|-------------------|----------|
| `extract/` | `extract_`, `reddit_`, `scraper`, `collector`, `fetcher` | `extract_reddit.py`, `reddit_client.py` |
| `transform/` | `transform_`, `process_`, `convert_`, `map_`, `filter_` | `transform_data.py`, `process_posts.py` |
| `load/` | `load_`, `save_`, `store_`, `write_`, `export_`, `import_` | `load_to_db.py`, `save_data.py` |
| `core/` | `core`, `shared`, `common` | `core_logic.py`, `shared_utils.py` |
| `models/` | `model`, `schema`, `entity`, `dto` | `data_model.py`, `reddit_schema.py` |
| `services/` | `service`, `client`, `api`, `external` | `api_service.py`, `reddit_client.py` |
| `utils/` | `util`, `helper`, `tool` | `helper_tool.py`, `data_util.py` |
| `tests/` | `test_`, `mock_`, `fixture` | `test_extractor.py`, `mock_reddit.py` |

**Fallback**: Files not matching any pattern go to `core/` by default.

### Documentation Naming Convention

All documentation files should use **kebab-case**:
- ✅ `user-guide.md`
- ✅ `api-documentation.md`
- ❌ `UserGuide.md`
- ❌ `api_documentation.md`

## Troubleshooting

### Hook fails with "uv not found"
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Permission denied on script execution
```bash
chmod +x scripts/hooks/*.py
```

### Hook blocking valid file creation
1. Check if file type is correctly configured
2. Verify file follows naming conventions
3. Consider updating `ALLOWED_ROOT_FILES` if necessary

### Documentation organization issues
1. Move orphan files to appropriate subdirectories
2. Rename files to use kebab-case
3. Remove empty directories or add content

## Customization

To modify the rules, edit the constants at the top of each script:
- `ALLOWED_ROOT_FILES` in `validate-file-structure.py`
- `DOCS_STRUCTURE` in `check-doc-structure.py`
- `NAMING_RULES` in `check-doc-structure.py`

## Integration with AI-Rulez

These hooks complement the `ai-rulez` system by providing automatic enforcement of file organization rules that are otherwise just recommendations in documentation.