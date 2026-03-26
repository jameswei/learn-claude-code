"""Greeting module."""


def greet(name: str) -> str:
    """Return a greeting message for the given name.

    Args:
        name: The name of the person to greet.

    Returns:
        A greeting message string.

    Examples:
        >>> greet("Alice")
        'Hello, Alice!'
        >>> greet("World")
        'Hello, World!'
    """
    return f"Hello, {name}!"


if __name__ == "__main__":
    # Demo usage
    print(greet("World"))