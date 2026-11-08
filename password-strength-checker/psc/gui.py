"""Tkinter desktop interface with a live strength meter."""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Optional

from . import analyzer, breach, crack_time, generator

BG = "#f4f6fb"
CARD = "#ffffff"
TEXT = "#1f2937"
MUTED = "#6b7280"
OK_COLOR = "#16a34a"
BAD_COLOR = "#dc2626"
LEVEL_COLORS = {
    "Empty": "#9ca3af", "Very Weak": "#dc2626", "Weak": "#f97316", "Moderate": "#eab308",
    "Strong": "#22c55e", "Very Strong": "#15803d", "Compromised": "#7f1d1d",
}
CLIPBOARD_CLEAR_MS = 30_000


class PasswordCheckerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Password Strength Checker")
        self.geometry("700x820")
        self.minsize(620, 720)
        self.configure(bg=BG)

        self._breach_count: Optional[int] = None
        self._breach_token = 0
        self._events: "queue.Queue" = queue.Queue()
        self._score = 0
        self._color = LEVEL_COLORS["Empty"]

        self._build()
        self.var_pw.trace_add("write", self._on_change)
        self._refresh()
        self.after(100, self._poll_events)
        self.entry.focus_set()

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        tk.Label(self, text="Password Strength Checker", font=("Segoe UI", 20, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w", padx=18, pady=(14, 0))
        tk.Label(self, text="Analysis runs on your computer. Nothing is stored, and nothing is sent "
                            "unless you press \"Check breach database\".",
                 font=("Segoe UI", 9), bg=BG, fg=MUTED, wraplength=640, justify="left"
                 ).pack(anchor="w", padx=18)

        row = tk.Frame(self, bg=BG)
        row.pack(fill="x", padx=18, pady=(12, 6))
        self.var_pw = tk.StringVar()
        self.var_show = tk.BooleanVar(value=False)
        self.entry = ttk.Entry(row, textvariable=self.var_pw, show="\u2022", font=("Consolas", 15))
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Checkbutton(row, text="Show", variable=self.var_show,
                        command=self._toggle_show).pack(side="left", padx=(10, 0))

        self.meter = tk.Canvas(self, height=24, bg="#e5e7eb", highlightthickness=0)
        self.meter.pack(fill="x", padx=18, pady=(4, 0))
        self.meter.bind("<Configure>", lambda _e: self._draw_meter())

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=18, pady=(6, 0))
        self.lbl_label = tk.Label(head, text="", font=("Segoe UI", 16, "bold"), bg=BG)
        self.lbl_label.pack(side="left")
        self.lbl_score = tk.Label(head, text="", font=("Segoe UI", 12), bg=BG, fg=MUTED)
        self.lbl_score.pack(side="right")
        self.lbl_stats = tk.Label(self, text="", font=("Segoe UI", 10), bg=BG, fg=MUTED,
                                  anchor="w", justify="left", wraplength=650)
        self.lbl_stats.pack(fill="x", padx=18)
        self.bind("<Configure>", lambda e: self.lbl_stats.config(wraplength=max(300, self.winfo_width() - 40))
                  if e.widget is self else None)

        # Checklist
        box = tk.LabelFrame(self, text=" Checks ", bg=BG, fg=TEXT, font=("Segoe UI", 10, "bold"))
        box.pack(fill="x", padx=18, pady=(10, 0))
        self.check_labels = {}
        for i, (key, text) in enumerate(analyzer.CHECK_LABELS.items()):
            lbl = tk.Label(box, text="", anchor="w", bg=BG, font=("Segoe UI", 10))
            lbl.grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=1)
            self.check_labels[key] = (lbl, text)
        box.columnconfigure(0, weight=1)
        box.columnconfigure(1, weight=1)

        # Crack times
        box = tk.LabelFrame(self, text=" Estimated time to crack (average) ", bg=BG, fg=TEXT,
                            font=("Segoe UI", 10, "bold"))
        box.pack(fill="x", padx=18, pady=(10, 0))
        self.crack_labels = {}
        for i, (key, (description, _rate)) in enumerate(crack_time.SCENARIOS.items()):
            tk.Label(box, text=description, anchor="w", bg=BG, font=("Segoe UI", 9)
                     ).grid(row=i, column=0, sticky="w", padx=10)
            value = tk.Label(box, text="-", anchor="e", bg=BG, font=("Segoe UI", 9, "bold"))
            value.grid(row=i, column=1, sticky="e", padx=10)
            self.crack_labels[key] = value
        box.columnconfigure(0, weight=1)

        # Suggestions
        box = tk.LabelFrame(self, text=" Findings & suggestions ", bg=BG, fg=TEXT,
                            font=("Segoe UI", 10, "bold"))
        box.pack(fill="both", expand=True, padx=18, pady=(10, 0))
        self.lbl_tips = tk.Label(box, text="", anchor="nw", justify="left", bg=BG,
                                 font=("Segoe UI", 10), wraplength=620)
        self.lbl_tips.pack(fill="both", expand=True, padx=10, pady=6)
        box.bind("<Configure>", lambda e: self.lbl_tips.config(wraplength=max(200, e.width - 30)))

        self.var_status = tk.StringVar(value="")
        tk.Label(self, textvariable=self.var_status, bg=BG, fg=MUTED, anchor="w",
                 font=("Segoe UI", 9)).pack(fill="x", padx=18, pady=(4, 0))

        buttons = tk.Frame(self, bg=BG)
        buttons.pack(fill="x", padx=18, pady=10)
        for text, command in (("Generate password", self._generate),
                              ("Generate passphrase", self._generate_phrase),
                              ("Copy", self._copy),
                              ("Check breach database", self._check_breach),
                              ("Clear", self._clear)):
            ttk.Button(buttons, text=text, command=command).pack(side="left", padx=(0, 8))

    # ------------------------------------------------------------- drawing
    def _draw_meter(self) -> None:
        self.meter.delete("all")
        width = max(self.meter.winfo_width(), 10)
        self.meter.create_rectangle(0, 0, width * self._score / 100, 30, fill=self._color, width=0)
        for mark in (35, 75, 100):  # rough boundaries between labels
            x = width * mark / 100
            self.meter.create_line(x - 1, 0, x - 1, 30, fill="#ffffff")

    def _refresh(self) -> None:
        r = analyzer.analyze(self.var_pw.get(), breach_count=self._breach_count)
        self._score = r.score
        self._color = LEVEL_COLORS.get(r.label, "#9ca3af")
        self._draw_meter()
        self.lbl_label.config(text=r.label, fg=self._color)
        self.lbl_score.config(text=f"{r.score} / 100" if r.length else "")
        if r.length:
            self.lbl_stats.config(
                text=f"{r.length} characters  |  {', '.join(r.charsets)}  |  "
                     f"{r.naive_bits:.0f} bits naive -> {r.effective_bits:.0f} bits after pattern analysis")
        else:
            self.lbl_stats.config(text="")
        for key, (lbl, text) in self.check_labels.items():
            ok = r.checks.get(key, False) and r.length > 0
            lbl.config(text=("\u2714 " if ok else "\u2718 ") + text,
                       fg=OK_COLOR if ok else (BAD_COLOR if r.length else MUTED))
        for est in r.crack_times:
            self.crack_labels[est["key"]].config(text=est["display"] if r.length else "-")
        lines = []
        for f in r.findings:
            token = f" ({f['token']})" if f["token"] else ""
            lines.append(f"\u2022 {f['detail']}{token}")
        if lines:
            lines.append("")
        lines += [f"\u2192 {tip}" for tip in r.suggestions]
        self.lbl_tips.config(text="\n".join(lines))

    # ------------------------------------------------------------- actions
    def _toggle_show(self) -> None:
        self.entry.config(show="" if self.var_show.get() else "\u2022")

    def _on_change(self, *_args) -> None:
        self._breach_count = None  # result belonged to the previous password
        self._breach_token += 1
        self.var_status.set("")
        self._refresh()

    def _set_generated(self, text: str) -> None:
        self.var_show.set(True)
        self._toggle_show()
        self.var_pw.set(text)

    def _generate(self) -> None:
        self._set_generated(generator.generate_password(18))

    def _generate_phrase(self) -> None:
        self._set_generated(generator.generate_passphrase(6, "-", capitalize=True, add_number=True))

    def _clear(self) -> None:
        self.var_pw.set("")
        self.entry.focus_set()

    def _copy(self) -> None:
        text = self.var_pw.get()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)

        def wipe() -> None:
            try:
                if self.clipboard_get() == text:
                    self.clipboard_clear()
            except tk.TclError:
                pass
        self.after(CLIPBOARD_CLEAR_MS, wipe)
        self.var_status.set("Copied. The clipboard is cleared automatically in 30 seconds.")

    def _check_breach(self) -> None:
        password = self.var_pw.get()
        if not password:
            self.var_status.set("Type a password first.")
            return
        token = self._breach_token
        self.var_status.set("Checking Have I Been Pwned (only a 5-character hash prefix is sent)...")

        def worker() -> None:
            self._events.put((token, password, breach.check_pwned(password)))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_events(self) -> None:
        try:
            while True:
                token, password, count = self._events.get_nowait()
                if token != self._breach_token or password != self.var_pw.get():
                    continue  # the user edited the password meanwhile
                if count is None:
                    self.var_status.set("Could not reach the breach service (are you offline?).")
                else:
                    self._breach_count = count
                    self.var_status.set(
                        f"Found in {count:,} known breaches!" if count
                        else "Not found in any known breach.")
                    self._refresh()
        except queue.Empty:
            pass
        self.after(100, self._poll_events)


def launch() -> None:
    PasswordCheckerApp().mainloop()
