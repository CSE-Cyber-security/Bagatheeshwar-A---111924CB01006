// To-Do List: add, complete, delete, filter. Tasks persist in localStorage.
const KEY = "todo.tasks.v1";
const ICON = {
  check: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>',
  trash: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>'
};
const $ = (sel) => document.querySelector(sel);
const form = $("#task-form"), input = $("#task-input"), list = $("#task-list"), error = $("#error");
let filter = "all";
let tasks = load();

function load() {
  try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch { return []; }
}
function save() {
  try { localStorage.setItem(KEY, JSON.stringify(tasks)); } catch { /* storage unavailable */ }
}
function showError(msg) { error.textContent = msg; error.hidden = !msg; }

function addTask(text) {
  tasks.push({ id: Date.now() + Math.random(), text, done: false });
  save(); render();
}
function toggleTask(id) {
  const t = tasks.find((x) => x.id === id);
  if (t) t.done = !t.done;
  save(); render();
}
function deleteTask(id) {
  tasks = tasks.filter((x) => x.id !== id);
  save(); render();
}

function iconButton(cls, label, svg, onClick) {
  const b = document.createElement("button");
  b.type = "button"; b.className = "icon-btn " + cls;
  b.title = b.ariaLabel = label; b.innerHTML = svg;   // static icon markup only
  b.addEventListener("click", onClick);
  return b;
}

function taskItem(t) {
  const li = document.createElement("li");
  li.className = "task" + (t.done ? " done" : "");
  const box = document.createElement("input");
  box.type = "checkbox"; box.checked = t.done; box.ariaLabel = "Mark complete: " + t.text;
  box.addEventListener("change", () => toggleTask(t.id));
  const text = document.createElement("span");
  text.className = "text"; text.textContent = t.text;           // textContent prevents HTML injection
  li.append(box, text,
    iconButton("ok", t.done ? "Mark as pending" : "Mark as completed", ICON.check, () => toggleTask(t.id)),
    iconButton("del", "Delete task", ICON.trash, () => deleteTask(t.id)));
  return li;
}

function render() {
  const done = tasks.filter((t) => t.done).length, pending = tasks.length - done;
  const shown = tasks.filter((t) => filter === "all" || (filter === "done") === t.done);
  const labels = { all: `All (${tasks.length})`, pending: `Pending (${pending})`, done: `Completed (${done})` };
  document.querySelectorAll(".filter").forEach((b) => {
    b.textContent = labels[b.dataset.filter];
    b.classList.toggle("active", b.dataset.filter === filter);
  });
  $("#pending-count").textContent = `${pending} pending`;
  $("#done-count").textContent = `${done} completed`;
  if (!shown.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = tasks.length ? "No tasks in this view." : "No tasks yet. Add your first task above.";
    list.replaceChildren(li);
  } else {
    list.replaceChildren(...shown.map(taskItem));
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return showError("Enter a task before adding.");
  if (tasks.some((t) => t.text.toLowerCase() === text.toLowerCase())) return showError("That task is already on your list.");
  showError(""); addTask(text); input.value = ""; input.focus();
});
document.querySelectorAll(".filter").forEach((b) =>
  b.addEventListener("click", () => { filter = b.dataset.filter; render(); }));
render();
