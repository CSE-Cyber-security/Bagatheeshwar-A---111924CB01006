# Week 02 - Factorial of a Number

## Problem
Write a Python program to find the factorial of a given number.

## About
This program asks the user to enter a number and then calculates its
factorial. Factorial of n (n!) is the product of all whole numbers
from 1 up to n, e.g. 5! = 5 x 4 x 3 x 2 x 1 = 120.

## How to run
```
python3 factorial.py
```

Then type a number when prompted.

### Example
```
Enter a number: 5
Factorial of 5 = 120
```

## Notes
- 0! is a special case - by definition it's 1, not 0, so the program
  handles that correctly instead of just returning 0.
- Negative numbers don't have a factorial, so the program checks for
  that and prints a message instead of giving a wrong/weird answer.
- Also added a basic check so the program doesn't crash if someone
  types letters instead of a number.
