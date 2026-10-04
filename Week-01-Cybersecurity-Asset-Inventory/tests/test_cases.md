# Test Cases – Cybersecurity Asset Inventory System

Manual test cases I ran while building this. I didn't use a testing
framework like pytest for this since the whole thing is CLI based with
input(), so I just ran the program with different inputs and checked
the output/JSON file manually.

## TC-01: Add a valid asset
**Steps:** Choose option 1, enter Asset ID `A101`, fill in all fields
with valid values (Asset Type = Workstation, Risk Level = Medium,
Status = Secure).
**Expected:** "Asset 'A101' added successfully." message shown, and
the asset appears in `data/assets.json`.
**Result:** Pass

## TC-02: Add asset with duplicate ID
**Steps:** Try to add another asset using an Asset ID that already
exists (e.g. `A101` again).
**Expected:** Program should reject it and tell the user to use
update instead, not create a duplicate entry.
**Result:** Pass

## TC-03: Add asset with invalid Asset Type
**Steps:** When prompted for Asset Type, type something not in the
list, e.g. `Laptop`.
**Expected:** Program should not accept it and should keep asking
until a valid type (Workstation/Server/Router/Switch/Application) is
entered.
**Result:** Pass

## TC-04: Case-insensitive input for type/risk/status
**Steps:** Enter `server` (lowercase) for Asset Type.
**Expected:** Should be accepted and stored as `Server` (proper case).
**Result:** Pass

## TC-05: Display all assets
**Steps:** Choose option 2 with 3 assets already saved.
**Expected:** Prints all 3 assets in the required format, plus a
summary at the bottom (Total, Critical, High, Medium, Vulnerable
counts).
**Result:** Pass - matches expected output in assignment PDF.

## TC-06: Display with zero assets
**Steps:** Run option 2 right after starting with an empty
`assets.json`.
**Expected:** Should print "No assets found." instead of crashing.
**Result:** Pass

## TC-07: Search by partial Asset Name
**Steps:** Choose option 3, search for `Web` when `Web-Server`
exists.
**Expected:** Should find and display `Web-Server` even though the
search term is only part of the name.
**Result:** Pass

## TC-08: Search with no matches
**Steps:** Search for something that doesn't exist, e.g. `zzz`.
**Expected:** "No matching assets found." message, no crash.
**Result:** Pass

## TC-09: Update asset - partial update
**Steps:** Choose option 4, enter existing Asset ID, leave most
fields blank except IP Address, and say 'y' to change Security
Status.
**Expected:** Only IP Address and Security Status should change;
everything else stays the same.
**Result:** Pass

## TC-10: Update non-existent asset
**Steps:** Try to update an Asset ID that doesn't exist, e.g.
`Z999`.
**Expected:** "No asset found with ID 'Z999'." message, program
doesn't crash.
**Result:** Pass

## TC-11: Delete asset with confirmation
**Steps:** Choose option 5, enter a valid Asset ID, confirm with
`y`.
**Expected:** Asset removed from list and from assets.json.
**Result:** Pass

## TC-12: Delete asset, cancel at confirmation
**Steps:** Choose option 5, enter valid Asset ID, but answer `n` at
the confirmation prompt.
**Expected:** Asset should NOT be deleted, "Delete cancelled."
message shown.
**Result:** Pass

## TC-13: Invalid main menu choice
**Steps:** At the main menu, type something outside 1-6, e.g. `99`
or `abc`.
**Expected:** Should show "Invalid choice..." and reload the menu
instead of crashing.
**Result:** Pass

## TC-14: Data persists across runs
**Steps:** Add an asset, exit the program (option 6), then run the
program again and choose option 2.
**Expected:** The asset added in the previous run should still be
there, since it's saved to assets.json.
**Result:** Pass

## TC-15: Corrupted/missing data file
**Steps:** Delete `data/assets.json` (or put garbage text in it) and
run the program.
**Expected:** Program should not crash - it should just start with
an empty asset list.
**Result:** Pass
