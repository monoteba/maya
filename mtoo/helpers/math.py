def isclose(a, b, epsilon=1e-09):
    """
    Compare two numbers for equality with supplied epsilon
    :param a: First value
    :param b: Second value
    :param epsilon: Max. allowed difference
    :return: True if difference between a and b is less than epsilon
    """
    return abs(a - b) < epsilon
