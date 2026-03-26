"""Math utility functions for basic arithmetic operations."""


def multiply(a, b):
    """Multiply two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The product of a and b (a * b).
    """
    return a * b


def divide(a, b):
    """Divide two numbers.

    Args:
        a: Dividend (numerator).
        b: Divisor (denominator).

    Returns:
        The quotient of a divided by b (a / b).

    Raises:
        ZeroDivisionError: If b is zero.
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def power(base, exponent):
    """Raise a base to an exponent.

    Args:
        base: The base number.
        exponent: The exponent to raise the base to.

    Returns:
        The result of base ** exponent.
    """
    return base ** exponent