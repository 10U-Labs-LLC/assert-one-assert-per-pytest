# assert-one-assert-per-pytest

Assert that each pytest test function contains exactly one assert.

## Why One Assert Per Test?

The "one assert per test" pattern encourages writing focused,
atomic tests that verify a single behavior. Benefits include:

- **Clear failure messages**: When a test fails, you know exactly
  what behavior broke
- **Better test names**: Tests naturally describe specific behaviors
- **Easier maintenance**: Changes to one behavior don't affect
  unrelated assertions
- **Faster debugging**: No need to hunt through multiple assertions

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
assert-one-assert-per-pytest tests/ src/

# Use glob patterns
assert-one-assert-per-pytest "tests/**/test_*.py"

# Exclude patterns
assert-one-assert-per-pytest tests/ --exclude "**/conftest.py"

# Verbose output
assert-one-assert-per-pytest tests/ --verbose

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

```text
path/to/test_file.py:10:test_example:0
path/to/test_file.py:25:test_another:3
path/to/test_file.py:31:test_third:2:conjunction
```

Format: `file_path:line_number:function_name:assert_count`

A conjunction finding adds a fifth field, `conjunction`. Its line number is the
`assert` statement rather than the enclosing function, and its count is the
number of conjuncts the expression joins.

## Exit Codes

- `0`: No findings (or `--warn-only` specified)
- `1`: Findings detected
- `2`: Error (missing files, syntax errors, etc.)

## What Counts as a Test?

A test is any function whose name starts with `test_` and which is not
decorated as a pytest fixture. The file it lives in does not matter: a
directory argument is walked for every `.py` file it holds, dotted directories
aside, and each one is read.

Filename is not a proxy for content. A `test_*` function defined in
`base_classes.py` or in a factory module is inherited into a suite and run by
pytest exactly like one written in `test_thing.py`, so the rule applies to it
the same way. Selecting on the filename would leave those functions unchecked
while reporting a clean run.

A function carrying `@pytest.fixture`, bare or called, is skipped whatever it
is named. `test_device_id` decorated as a fixture supplies a value to tests; it
is not one.

Use `--exclude` to drop files you do not want read.

## What Counts as an Assert?

This tool counts Python `assert` statements at the immediate level
of test functions. It also counts:

- `pytest.raises()` context managers
- `pytest.warns()` context managers

It does **not** count:

- Assertions in nested functions or classes
- Helper assertions in fixtures or utility functions

## Conjunctions

An `assert` whose test expression is a top-level `and` carries one claim per
conjunct, so a red run names the whole expression rather than the claim that
broke. The tool reports it the way it reports a second `assert`.

```python
def test_bucket():
    assert "bucket_name" in result and "bucket_arn" in result
```

Only a top-level `and` is refused. These are all allowed:

- `assert a or b`, one claim about two alternatives. Splitting it into two
  tests would assert something stronger than the author meant.
- `assert 0 < x < 10`, a comparison chain, which is one claim about one value
  whatever the length of the chain.
- `assert not (a and b)`, which is `not a or not b`, and so a disjunction.
- `assert (a and b) or c`, where the claim being made is the disjunction.
- `assert all(i.a and i.b for i in items)`, where the `and` is evaluated per
  item inside a comprehension rather than joining two claims about the test.
- `assert a, "b and c"`, where the `and` is inside a string.

A short-circuit guard is refused along with the rest, because nothing in the
expression distinguishes a guard from a claim. Drop the guard and let the
failure speak for itself: `assert len(blocks) == 1` raises on `None` and names
the line, where `assert blocks is not None and len(blocks) == 1` does not.

## Options

| Option                | Description                                |
| --------------------- | ------------------------------------------ |
| `--exclude PATTERNS`  | Glob patterns to exclude (comma-separated) |
| `--quiet`             | Suppress all output (exit code only)       |
| `--verbose`           | Show detailed processing information       |
| `--fail-fast`         | Exit after first finding                   |
| `--warn-only`         | Always exit 0, even with findings          |

## License

Apache 2.0 - See [LICENSE.txt](LICENSE.txt)
