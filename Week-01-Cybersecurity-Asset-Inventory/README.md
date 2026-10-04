# Week 01 - Cybersecurity Asset Inventory System

## About
This is my Weekly Mini Project 01 for the cybersecurity home lab
course. The idea is pretty simple - an organization has a bunch of IT
assets (PCs, servers, routers, switches, apps) and instead of
tracking them on a spreadsheet, this is a small command line tool
that lets a security admin add, search, update, delete, and display
those assets, along with a quick summary of how risky the current
setup is.

## What it does
- Add a new asset (Asset ID, Name, Type, IP, OS, Department, Risk
  Level, Security Status)
- Display all assets in a formatted list, with a summary at the
  bottom (total assets, how many are Critical/High/Medium risk, how
  many are Vulnerable)
- Search for an asset by ID or name (partial match works too)
- Update an existing asset - you can leave fields blank to keep them
  the same
- Delete an asset (asks for confirmation first so you don't delete
  something by accident)
- Data is saved in `data/assets.json` so it's still there the next
  time you run the program

## How to run
Needs Python 3 (no external libraries required, everything used is
from the standard library).

```
cd src
python3 asset_inventory.py
```

Then just follow the menu - type a number 1-6 and hit enter.

## Project structure
```
Week-01-Cybersecurity-Asset-Inventory/
|
|-- src/
|   `-- asset_inventory.py     (main program)
|
|-- data/
|   `-- assets.json            (where the assets get saved)
|
|-- tests/
|   `-- test_cases.md          (manual test cases I ran)
|
|-- screenshots/                (screenshots of the program running)
|
`-- README.md
```

## Design notes
- I used a list of dictionaries to hold the assets in memory, and
  just dump the whole list to JSON every time something changes
  (add/update/delete). For this size of project that was simpler
  than trying to do partial file writes.
- Asset Type, Risk Level, and Security Status all have to be one of
  a fixed set of values, so I wrote a helper function
  `get_valid_choice()` that keeps re-asking until the user types
  something valid. It's case-insensitive so typing "server" still
  gets stored as "Server".
- If `assets.json` doesn't exist yet (first time running the
  program) or somehow gets corrupted, the program doesn't crash - it
  just starts with an empty list.
- Didn't use any external packages, just `json` and `os` from the
  standard library, since this didn't really need anything more than
  that.

## Known limitations / things I'd improve later
- No proper IP address format validation right now, it just accepts
  whatever string you type in.
- Everything runs in the terminal, no GUI.
- If two people ran this on the same file at the same time it could
  overwrite each other's changes, but that's outside the scope of
  this assignment since it's meant to be single-user.
