def isPowerOfTwo(x) -> bool:
    """Check if a number is a power of two

    Args:
        x (_type_): a numeric value

    Returns:
        bool: Returns True if the number is a power of two, False otherwise
    """
    return x and (not (x & (x - 1)))


def log2(x) -> int:
    """Returns the integer part of the logarithm of x to the base 2

    Args:
        x (_type_): a numeric value

    Returns:
        int: Returns the integer part of the logarithm of x to the base 2
    """
    return (x & -x).bit_length() - 1
