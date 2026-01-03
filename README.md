# assert-one-assert-per-pytest

A CLI tool to assert that each pytest test function contains exactly one assert statement.

## Why One Assert Per Test?

The "one assert per test" pattern encourages writing focused, atomic tests that verify a single behavior. Benefits include:

- **Clear failure messages**: When a test fails, you know exactly what behavior broke
- **Better test names**: Tests naturally describe specific behaviors
- **Easier maintenance**: Changes to one behavior don't affect unrelated assertions
- **Faster debugging**: No need to hunt through multiple assertions to find the failure

## Installation

```bash
pip install assert-one-assert-per-pytest
```

## Usage

### Command Line

```bash
# Scan specific files
assert-one-assert-per-pytest test_example.py

# Scan directories recursively
assert-one-assert-per-pytest tests/

# Use glob patterns
assert-one-assert-per-pytest "tests/**/test_*.py"

# Exclude patterns
assert-one-assert-per-pytest tests/ --exclude "**/conftest.py,**/fixtures/*"

# Verbose output
assert-one-assert-per-pytest tests/ --verbose

# JSON output
assert-one-assert-per-pytest tests/ --json

# Count only
assert-one-assert-per-pytest tests/ --count

# Fail fast (exit on first finding)
assert-one-assert-per-pytest tests/ --fail-fast

# Warn only (always exit 0)
assert-one-assert-per-pytest tests/ --warn-only
```

### GitHub Actions

```yaml
- uses: 10U-Labs-LLC/assert-one-assert-per-pytest@v1
  with:
    files: "tests/"
    exclude: "**/conftest.py"
    verbose: "true"
```

### As a Python Module

```bash
python -m assert_one_assert_per_pytest tests/
```

## Output Format

Default output shows one finding per line:

```
path/to/test_file.py:10:test_example:0
path/to/test_file.py:25:test_another:3
```

Format: `file_path:line_number:function_name:assert_count`

### JSON Output

```json
[
  {
    "path": "path/to/test_file.py",
    "line_number": 10,
    "function_name": "test_example",
    "assert_count": 0
  }
]
```

## Exit Codes

- `0`: No findings (or `--warn-only` specified)
- `1`: Findings detected
- `2`: Error (missing files, syntax errors, etc.)

## What Counts as an Assert?

This tool counts Python `assert` statements at the immediate level of test functions. It does **not** count:

- Assertions in nested functions or classes
- `pytest.raises` or `pytest.warns` context managers
- Helper assertions in fixtures or utility functions

## Options

| Option | Description |
|--------|-------------|
| `--exclude PATTERNS` | Comma-separated glob patterns to exclude |
| `--quiet` | Suppress all output (exit code only) |
| `--count` | Output only the count of findings |
| `--json` | Output findings as JSON |
| `--verbose` | Show detailed processing information |
| `--fail-fast` | Exit after first finding |
| `--warn-only` | Always exit 0, even with findings |

## License

Apache 2.0 - See [LICENSE.txt](LICENSE.txt)
