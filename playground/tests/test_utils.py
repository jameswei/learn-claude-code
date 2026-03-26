"""Tests for utils module."""

from playground.utils import greet, add_numbers


class TestGreet:
    def test_greet_returns_greeting(self):
        result = greet("Alice")
        assert result == "Hello, Alice!"

    def test_greet_with_empty_name(self):
        result = greet("")
        assert result == "Hello, !"


class TestAddNumbers:
    def test_add_two_positive_numbers(self):
        result = add_numbers(1, 2)
        assert result == 3

    def test_add_negative_numbers(self):
        result = add_numbers(-1, -1)
        assert result == -2

    def test_add_mixed_numbers(self):
        result = add_numbers(5, -3)
        assert result == 2