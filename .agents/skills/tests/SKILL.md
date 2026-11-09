---
name: tests
description: Python test-writing best practices covering test structure, fixtures, parametrization. Use when writing, reviewing, or refactoring tests, adding test coverage, or working in tests directories.
---

# Name Tests After the Behavior
A test name should state the scenario and the expected outcome, not just the function it calls. A useful pattern: test_<condition>_<expected result> — e.g. test_negative_amount_raises_value_error. Group related scenarios in a class (class TestTokenValidation:) so names stay short without losing context.

# Test One Behavior per Test
Each test should verify a single behavior. When one test checks several behaviors, the first failing assert aborts the test and hides whether the later behaviors also broke, and the test name can no longer say what failed. One behavior per test yields precise failure reports and lets tests fail independently.

# Test Structure
Organize every test into three visible phases: Arrange (set up inputs and state), Act (call the one thing under test), Assert (verify the outcome). Always split sections blank lines.

The basic building blocks of unit testing are test cases — single scenarios that must be set up and checked for correctness. In unittest, test cases are represented by unittest.TestCase instances.
