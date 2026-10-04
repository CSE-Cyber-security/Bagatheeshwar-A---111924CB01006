"""
GitHub Task 3
Fibonacci Series

This program asks the user how many terms they want and prints that
many numbers of the Fibonacci series.

The Fibonacci series starts with 0 and 1, and after that every
number is just the sum of the two numbers before it:
0, 1, 1, 2, 3, 5, 8, 13, 21, ...

Author: BAGATHEESHWAR A 11924CB01006
"""


def fibonacci_series(n):
    """Return a list containing the first n terms of the Fibonacci
    series. Handles n = 0 and n = 1 as special cases since there
    aren't two previous terms to add yet."""
    if n <= 0:
        return []

    if n == 1:
        return [0]

    series = [0, 1]
    while len(series) < n:
        next_term = series[-1] + series[-2]
        series.append(next_term)

    return series


def main():
    num_input = input("Enter the number of terms: ").strip()

    if not num_input.isdigit():
        print("Please enter a valid positive whole number.")
        return

    n = int(num_input)

    if n == 0:
        print("Please enter a number greater than 0.")
        return

    series = fibonacci_series(n)

    # convert each number to a string so they can be joined with
    # spaces for printing on one line
    series_str = " ".join(str(num) for num in series)

    print("Fibonacci Series:")
    print(series_str)


if __name__ == "__main__":
    main()
