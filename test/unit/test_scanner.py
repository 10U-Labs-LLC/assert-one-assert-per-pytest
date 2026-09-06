from __future__ import annotations

from test.helpers import parse_function
from test.samples import (
    ASYNC_TEST,
    ASYNC_TEST_WITH_ASSERT,
    BARE_CONTEXT_MANAGER,
    BARE_FIXTURE,
    BARE_RAISES,
    CALLED_FIXTURE,
    CLASS_METHOD,
    CLEAN,
    COMPARISON_CHAIN,
    CONJUNCTION,
    CONJUNCTION_INSIDE_COMPREHENSION,
    CONJUNCTION_INSIDE_DISJUNCTION,
    CONJUNCTION_IN_MESSAGE,
    CONJUNCTION_IN_NESTED_FUNCTION,
    CONJUNCTION_OF_THREE,
    CONJUNCTION_PLUS_ASSERT,
    CONJUNCTION_WITH_MESSAGE,
    DISJUNCTION,
    HELPER_AND_TEST,
    IMPORTED_FIXTURE,
    MARKED_TEST,
    MIXED_VIOLATIONS,
    NEGATED_CONJUNCTION,
    NESTED_CLASS,
    NESTED_FUNCTION,
    NON_PYTEST_WITH,
    NO_ASSERTS,
    NO_ASSERT_STATEMENTS,
    OTHER_MODULE_RAISES,
    OTHER_PYTEST_CONTEXT_MANAGER,
    PYTEST_RAISES,
    PYTEST_WARNS,
    RAISES_PLUS_ASSERT,
    THREE_ASSERTS,
    TWO_ASSERTS,
    TWO_CONJUNCTIONS,
    TWO_TEST_FUNCTIONS,
)

import pytest

from assert_one_assert_per_pytest.scanner import (
    Finding,
    count_asserts,
    find_conjunctions,
    is_pytest_fixture,
    is_test_function,
    iter_test_functions,
    scan_file,
)

PATH = "test_example.py"


@pytest.mark.unit
class TestIsTestFunction:
    def test_returns_true_for_test_prefix(self) -> None:
        assert is_test_function("test_example") is True

    def test_returns_true_for_test_underscore_only(self) -> None:
        assert is_test_function("test_") is True

    def test_returns_false_for_no_prefix(self) -> None:
        assert is_test_function("example") is False

    def test_returns_false_for_test_without_underscore(self) -> None:
        assert is_test_function("testing") is False

    def test_returns_false_for_empty_string(self) -> None:
        assert is_test_function("") is False


@pytest.mark.unit
class TestIsPytestFixture:
    def test_returns_true_for_bare_decorator(self) -> None:
        assert is_pytest_fixture(parse_function(BARE_FIXTURE)) is True

    def test_returns_true_for_called_decorator(self) -> None:
        assert is_pytest_fixture(parse_function(CALLED_FIXTURE)) is True

    def test_returns_true_for_imported_decorator(self) -> None:
        assert is_pytest_fixture(parse_function(IMPORTED_FIXTURE)) is True

    def test_returns_false_for_a_mark(self) -> None:
        assert is_pytest_fixture(parse_function(MARKED_TEST)) is False

    def test_returns_false_for_an_undecorated_test(self) -> None:
        assert is_pytest_fixture(parse_function(CLEAN)) is False


@pytest.mark.unit
class TestFixturesAreNotTests:
    def test_bare_fixture_yields_no_finding(self) -> None:
        assert scan_file(PATH, BARE_FIXTURE) == []

    def test_called_fixture_yields_no_finding(self) -> None:
        assert scan_file(PATH, CALLED_FIXTURE) == []

    def test_fixture_is_not_iterated(self) -> None:
        assert list(iter_test_functions(PATH, BARE_FIXTURE)) == []


@pytest.mark.unit
class TestCountAsserts:
    def test_counts_single_assert(self) -> None:
        assert count_asserts(parse_function(CLEAN)) == 1

    def test_counts_multiple_asserts(self) -> None:
        assert count_asserts(parse_function(THREE_ASSERTS)) == 3

    def test_counts_zero_asserts(self) -> None:
        assert count_asserts(parse_function(NO_ASSERT_STATEMENTS)) == 0

    def test_ignores_nested_function_asserts(self) -> None:
        assert count_asserts(parse_function(NESTED_FUNCTION)) == 1

    def test_ignores_nested_class_asserts(self) -> None:
        assert count_asserts(parse_function(NESTED_CLASS)) == 1

    def test_counts_pytest_raises_as_assertion(self) -> None:
        assert count_asserts(parse_function(PYTEST_RAISES)) == 1

    def test_counts_pytest_warns_as_assertion(self) -> None:
        assert count_asserts(parse_function(PYTEST_WARNS)) == 1

    def test_counts_pytest_raises_with_assert(self) -> None:
        assert count_asserts(parse_function(RAISES_PLUS_ASSERT)) == 2

    def test_ignores_non_pytest_with_statements(self) -> None:
        assert count_asserts(parse_function(NON_PYTEST_WITH)) == 1

    def test_ignores_raises_without_pytest_prefix(self) -> None:
        assert count_asserts(parse_function(BARE_RAISES)) == 1

    def test_ignores_other_pytest_context_managers(self) -> None:
        assert count_asserts(parse_function(OTHER_PYTEST_CONTEXT_MANAGER)) == 1

    def test_ignores_context_manager_that_is_not_a_call(self) -> None:
        assert count_asserts(parse_function(BARE_CONTEXT_MANAGER)) == 1

    def test_ignores_raises_on_another_module(self) -> None:
        assert count_asserts(parse_function(OTHER_MODULE_RAISES)) == 1


@pytest.mark.unit
class TestScanFile:
    def test_finds_test_with_zero_asserts(self) -> None:
        assert len(scan_file(PATH, NO_ASSERTS)) == 1

    def test_finds_test_with_multiple_asserts(self) -> None:
        assert len(scan_file(PATH, TWO_ASSERTS)) == 1

    def test_no_findings_for_single_assert(self) -> None:
        assert len(scan_file(PATH, CLEAN)) == 0

    def test_ignores_non_test_functions(self) -> None:
        assert len(scan_file(PATH, HELPER_AND_TEST)) == 0

    def test_finds_multiple_violations(self) -> None:
        assert len(scan_file(PATH, MIXED_VIOLATIONS)) == 2

    def test_handles_async_test_functions(self) -> None:
        assert len(scan_file(PATH, ASYNC_TEST)) == 1

    def test_handles_class_test_methods(self) -> None:
        assert len(scan_file(PATH, CLASS_METHOD)) == 1

    def test_raises_on_syntax_error(self) -> None:
        with pytest.raises(SyntaxError):
            scan_file(PATH, "def test_example( broken syntax")


@pytest.mark.unit
class TestFinding:
    def test_str_format(self) -> None:
        finding = Finding(PATH, 10, "test_something", 0)
        assert str(finding) == "test_example.py:10:test_something:0"

    def test_frozen(self) -> None:
        finding = Finding(PATH, 10, "test_something", 0)
        with pytest.raises(AttributeError):
            setattr(finding, "path", "other.py")


@pytest.mark.unit
class TestIterTestFunctions:
    def test_yields_test_functions(self) -> None:
        assert len(list(iter_test_functions(PATH, TWO_TEST_FUNCTIONS))) == 2

    def test_yields_function_name(self) -> None:
        results = list(iter_test_functions(PATH, CLEAN))
        assert results[0][0] == "test_example"

    def test_yields_line_number(self) -> None:
        results = list(iter_test_functions(PATH, CLEAN))
        assert results[0][1] == 2

    def test_yields_assert_count(self) -> None:
        results = list(iter_test_functions(PATH, TWO_ASSERTS))
        assert results[0][2] == 2

    def test_ignores_non_test_functions(self) -> None:
        assert len(list(iter_test_functions(PATH, HELPER_AND_TEST))) == 1

    def test_yields_only_the_test_function(self) -> None:
        results = list(iter_test_functions(PATH, HELPER_AND_TEST))
        assert results[0][0] == "test_only"

    def test_handles_async_functions(self) -> None:
        results = list(iter_test_functions(PATH, ASYNC_TEST_WITH_ASSERT))
        assert len(results) == 1

    def test_yields_async_function_name(self) -> None:
        results = list(iter_test_functions(PATH, ASYNC_TEST_WITH_ASSERT))
        assert results[0][0] == "test_async"


@pytest.mark.unit
class TestFindConjunctions:
    def test_finds_a_top_level_conjunction(self) -> None:
        assert find_conjunctions(parse_function(CONJUNCTION)) == [(3, 2)]

    def test_counts_every_conjunct_in_a_chain(self) -> None:
        node = parse_function(CONJUNCTION_OF_THREE)
        assert find_conjunctions(node) == [(3, 3)]

    def test_finds_a_conjunction_carrying_a_message(self) -> None:
        node = parse_function(CONJUNCTION_WITH_MESSAGE)
        assert find_conjunctions(node) == [(3, 2)]

    def test_finds_every_conjunction_in_a_function(self) -> None:
        node = parse_function(TWO_CONJUNCTIONS)
        assert find_conjunctions(node) == [(3, 2), (4, 2)]

    def test_allows_a_disjunction(self) -> None:
        assert len(find_conjunctions(parse_function(DISJUNCTION))) == 0

    def test_allows_a_negated_conjunction(self) -> None:
        node = parse_function(NEGATED_CONJUNCTION)
        assert len(find_conjunctions(node)) == 0

    def test_allows_a_conjunction_inside_a_disjunction(self) -> None:
        node = parse_function(CONJUNCTION_INSIDE_DISJUNCTION)
        assert len(find_conjunctions(node)) == 0

    def test_allows_a_conjunction_inside_a_comprehension(self) -> None:
        node = parse_function(CONJUNCTION_INSIDE_COMPREHENSION)
        assert len(find_conjunctions(node)) == 0

    def test_allows_a_comparison_chain(self) -> None:
        assert len(find_conjunctions(parse_function(COMPARISON_CHAIN))) == 0

    def test_allows_and_inside_a_message_string(self) -> None:
        node = parse_function(CONJUNCTION_IN_MESSAGE)
        assert len(find_conjunctions(node)) == 0

    def test_ignores_a_conjunction_in_a_nested_function(self) -> None:
        node = parse_function(CONJUNCTION_IN_NESTED_FUNCTION)
        assert len(find_conjunctions(node)) == 0

    def test_finds_nothing_in_a_single_plain_assert(self) -> None:
        assert len(find_conjunctions(parse_function(CLEAN))) == 0


@pytest.mark.unit
class TestScanFileConjunctions:
    def test_reports_a_conjunction(self) -> None:
        assert len(scan_file(PATH, CONJUNCTION)) == 1

    def test_reports_nothing_for_a_disjunction(self) -> None:
        assert len(scan_file(PATH, DISJUNCTION)) == 0

    def test_marks_the_finding_as_a_conjunction(self) -> None:
        assert scan_file(PATH, CONJUNCTION)[0].conjunction is True

    def test_reports_the_number_of_conjuncts(self) -> None:
        assert scan_file(PATH, CONJUNCTION_OF_THREE)[0].assert_count == 3

    def test_reports_the_line_of_the_assert(self) -> None:
        assert scan_file(PATH, CONJUNCTION)[0].line_number == 3

    def test_reports_the_enclosing_function(self) -> None:
        finding = scan_file(PATH, CONJUNCTION)[0]
        assert finding.function_name == "test_conjunction"

    def test_reports_both_kinds_of_finding(self) -> None:
        assert len(scan_file(PATH, CONJUNCTION_PLUS_ASSERT)) == 2

    def test_reports_the_assert_count_finding_first(self) -> None:
        assert scan_file(PATH, CONJUNCTION_PLUS_ASSERT)[0].conjunction is False


@pytest.mark.unit
class TestConjunctionFinding:
    def test_str_appends_the_conjunction_marker(self) -> None:
        finding = Finding(PATH, 10, "test_something", 2, conjunction=True)
        assert str(finding) == "test_example.py:10:test_something:2:conjunction"

    def test_conjunction_defaults_to_false(self) -> None:
        assert Finding(PATH, 10, "test_something", 0).conjunction is False
