from __future__ import annotations

CLEAN = """
def test_example():
    assert True
"""

TWO_CLEAN = """
def test_example():
    assert True

def test_another():
    assert 1 == 1
"""

NO_ASSERTS = """
def test_no_asserts():
    pass
"""

NO_ASSERTS_TWICE = """
def test_no_asserts():
    pass

def test_also_no_asserts():
    x = 1
"""

THREE_ASSERTS = """
def test_many_asserts():
    assert True
    assert False
    assert 1 == 1
"""

NO_ASSERT_STATEMENTS = """
def test_example():
    x = 1
    print(x)
"""

NESTED_FUNCTION = """
def test_with_nested():
    def helper():
        assert False
    assert True
"""

NESTED_CLASS = """
def test_with_nested_class():
    class Helper:
        def check(self):
            assert False
    assert True
"""

ASYNC_TEST = """
async def test_async():
    pass
"""

ASYNC_TEST_WITH_ASSERT = """
async def test_async():
    assert True
"""

CLASS_METHOD = """
class TestExample:
    def test_method(self):
        pass
"""

HELPER_AND_TEST = """
def helper():
    pass

def test_only():
    assert True
"""

PYTEST_RAISES = """
def test_raises_exception():
    with pytest.raises(ValueError):
        raise ValueError("expected")
"""

PYTEST_WARNS = """
def test_warns_user():
    with pytest.warns(UserWarning):
        warnings.warn("expected", UserWarning)
"""

RAISES_PLUS_ASSERT = """
def test_two_assertions():
    with pytest.raises(ValueError):
        raise ValueError("expected")
    assert True
"""

NON_PYTEST_WITH = """
def test_with_open():
    with open(__file__) as f:
        pass
    assert True
"""

BARE_CONTEXT_MANAGER = """
def test_with_bare_manager():
    with cm:
        pass
    assert True
"""

BARE_RAISES = """
def test_bare_raises():
    with raises(ValueError):
        raise ValueError("expected")
    assert True
"""

OTHER_PYTEST_CONTEXT_MANAGER = """
def test_deprecated():
    with pytest.deprecated_call():
        pass
    assert True
"""

OTHER_MODULE_RAISES = """
def test_other_raises():
    with helper.raises(ValueError):
        pass
    assert True
"""

MIXED_VIOLATIONS = """
def test_no_asserts():
    pass

def test_one_assert():
    assert True

def test_many_asserts():
    assert True
    assert False
"""

TWO_TEST_FUNCTIONS = """
def test_a():
    assert True

def test_b():
    pass
"""

TWO_ASSERTS = """
def test_multiple():
    assert True
    assert False
"""

CONJUNCTION = """
def test_conjunction():
    assert True and False
"""

CONJUNCTION_OF_THREE = """
def test_three_conjuncts():
    assert True and False and True
"""

CONJUNCTION_WITH_MESSAGE = """
def test_conjunction_with_message():
    assert True and False, "message"
"""

DISJUNCTION = """
def test_disjunction():
    assert True or False
"""

NEGATED_CONJUNCTION = """
def test_negated_conjunction():
    assert not (True and False)
"""

CONJUNCTION_INSIDE_DISJUNCTION = """
def test_conjunction_inside_disjunction():
    assert (True and False) or True
"""

CONJUNCTION_INSIDE_COMPREHENSION = """
def test_conjunction_inside_comprehension():
    assert all(item.a and item.b for item in items)
"""

COMPARISON_CHAIN = """
def test_comparison_chain():
    assert 0 < value < 10
"""

CONJUNCTION_IN_MESSAGE = """
def test_conjunction_in_message():
    assert value, "expected a and b"
"""

CONJUNCTION_IN_NESTED_FUNCTION = """
def test_conjunction_in_nested_function():
    def helper():
        assert True and False
    assert True
"""

CONJUNCTION_PLUS_ASSERT = """
def test_conjunction_plus_assert():
    assert True and False
    assert True
"""

TWO_CONJUNCTIONS = """
def test_two_conjunctions():
    assert True and False
    assert False and True
"""

BARE_FIXTURE = """
@pytest.fixture
def test_device_id():
    return "e2e-test-device"
"""

CALLED_FIXTURE = """
@pytest.fixture(scope="module")
def test_session_id():
    return "e2e-test-session"
"""

IMPORTED_FIXTURE = """
@fixture
def test_client():
    return object()
"""

MARKED_TEST = """
@pytest.mark.unit
def test_marked():
    assert True
"""
