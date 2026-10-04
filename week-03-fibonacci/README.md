# GitHub Task 3 - Fibonacci Series

## Problem
Write a Python program to print the Fibonacci series for n terms.

## About
This program asks the user how many terms of the Fibonacci series
they want, then prints that many numbers. The Fibonacci series
starts with 0 and 1, and every number after that is the sum of the
two numbers before it (0, 1, 1, 2, 3, 5, 8, 13, ...).

## How to run
```
python3 fibonacci.py
```

Then type the number of terms when prompted.

### Example
```
Enter the number of terms: 7
Fibonacci Series:
0 1 1 2 3 5 8
```

## Notes
- If the user enters 1, the program just prints `0`, since there's
  only one term.
- If the user enters 0 or a negative number, the program prints a
  message instead of an empty/wrong series.
- Also added a check so it doesn't crash if someone types letters
  instead of a number.
