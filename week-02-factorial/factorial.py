"""
Weekly Mini Project 02
Factorial of a Number

Simple program that asks the user for a number and prints its
factorial. Factorial of n (written n!) is just n * (n-1) * (n-2) *
... * 1. For example 5! = 5*4*3*2*1 = 120.

A couple of edge cases I had to think about:
- 0! is defined as 1 (not 0), so that needs to be handled.
- Factorial doesn't make sense for negative numbers, so the program
  should reject those instead of giving a wrong answer.

Author: BAGATHEESHWAR A 111924CB01006
"""


def factorial(n):
    """Return n! using a simple loop. Could also do this with
    recursion but a loop is easier to follow and doesn't risk hitting
    Python's recursion limit for bigger numbers."""
    result = 1
    for i in range(1, n + 1):
        result = result * i
    return result


def main():
    num_input = input("Enter a number: ").strip()

    # make sure what they typed is actually a whole number before
    # trying to convert it, so the program doesn't crash on bad input
    if not num_input.lstrip("-").isdigit():
        print("Please enter a valid whole number.")
        return

    num = int(num_input)

    if num < 0:
        print("Factorial is not defined for negative numbers.")
        return

    result = factorial(num)
    print(f"Factorial of {num} = {result}")


if __name__ == "__main__":
    main()
