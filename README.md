# To-Do List Application

A simple task manager built with **HTML, CSS and vanilla JavaScript** for the GitHub Week 4 task.

## Objective
Practise web development, JavaScript DOM manipulation and GitHub version control by building a page where users manage their daily activities.

## Features
- Add a task (button click or Enter key), with validation for empty and duplicate tasks
- Mark a task as completed or pending (checkbox or green tick button)
- Delete a task (red bin button)
- Filter by **All / Pending / Completed**, with live counts
- Tasks are saved in the browser (`localStorage`), so they survive a refresh
- Responsive layout, keyboard focus styles, and safe rendering (`textContent`, no HTML injection)

## Project Structure
```
To-Do-List-Application/
├── index.html      # Page structure
├── style.css       # Styling and responsive layout
├── script.js       # Add / complete / delete / filter logic
├── README.md
└── screenshots/    # Output screenshots
```

## How to Run
1. Clone the repository and open the `week-4` branch.
2. Open `index.html` in any browser. No build step or dependencies are needed.

## Output Screenshots
| Empty state | Validation message |
|---|---|
| ![Empty](screenshots/01-empty-state.png) | ![Validation](screenshots/02-validation-error.png) |

| Tasks added | Tasks completed |
|---|---|
| ![Added](screenshots/03-tasks-added.png) | ![Completed](screenshots/04-tasks-completed.png) |

| Pending filter | Completed filter | After delete |
|---|---|---|
| ![Pending](screenshots/05-pending-filter.png) | ![Done](screenshots/06-completed-filter.png) | ![Deleted](screenshots/07-after-delete.png) |

## How It Works
- `script.js` keeps a `tasks` array of `{ id, text, done }` objects.
- Every action (add, toggle, delete, filter) updates the array, saves it, and calls `render()`, which rebuilds the list in the DOM.

## Author
Bagatheeshwar A
