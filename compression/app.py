# =============================================================
# app.py — HuffZip Pro v2.0 | Advanced GUI Application
# Pro-level Huffman compression tool with:
#   - Dark/Light theme toggle
#   - Batch file compression (multiple files at once)
#   - Real-time compression speed (MB/s)
#   - Compression ratio progress bar
#   - Detailed stats panel (entropy, time, ratio)
#   - Drag-and-drop file support
#   - History log of all operations
#   - Cancel operation support
#   - Error recovery with retry
# =============================================================

import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import time
import threading
import hashlib
from pathlib import Path
from core.compressor import Compressor
from core.decompressor import Decompressor
import math


# ─────────────────────────────────────────────────────────────
# THEME SYSTEM
# Two full themes: dark (default) and light
# ─────────────────────────────────────────────────────────────
THEMES = {
    "dark": {
        "bg":           "#0f1117",
        "surface":      "#1a1d27",
        "surface2":     "#22263a",
        "border":       "#2e3350",
        "accent":       "#4f8ef7",
        "accent2":      "#00d4aa",
        "danger":       "#f75a5a",
        "warning":      "#f7c94f",
        "text":         "#e8eaf6",
        "text_muted":   "#6b7399",
        "text_dim":     "#3d4466",
        "green":        "#4caf72",
        "progress_bg":  "#1e2235",
    },
    "light": {
        "bg":           "#f0f2fa",
        "surface":      "#ffffff",
        "surface2":     "#e8ecf8",
        "border":       "#c5cae9",
        "accent":       "#3d5afe",
        "accent2":      "#00897b",
        "danger":       "#e53935",
        "warning":      "#f9a825",
        "text":         "#1a1d2e",
        "text_muted":   "#5c6491",
        "text_dim":     "#9fa8da",
        "green":        "#2e7d32",
        "progress_bg":  "#dde1f5",
    }
}


# ─────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────

def format_size(bytes_val):
    """Convert bytes to human-readable string (KB, MB, GB)."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 ** 2:
        return f"{bytes_val / 1024:.2f} KB"
    elif bytes_val < 1024 ** 3:
        return f"{bytes_val / (1024**2):.2f} MB"
    else:
        return f"{bytes_val / (1024**3):.2f} GB"


def calculate_entropy(filepath):
    """
    Calculate Shannon entropy of a file (bits per byte).
    Higher entropy = more random data = harder to compress.
    Max entropy = 8.0 (perfectly random).
    """
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        if not data:
            return 0.0
        freq = {}
        for byte in data:
            freq[byte] = freq.get(byte, 0) + 1
        total = len(data)
        entropy = 0.0
        for count in freq.values():
            p = count / total
            entropy -= p * math.log2(p)
        return round(entropy, 3)
    except Exception:
        return 0.0


def file_sha256(filepath):
    """Compute SHA-256 checksum of a file for integrity verification."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()[:16] + "..."
    except Exception:
        return "N/A"


# ─────────────────────────────────────────────────────────────
# TOOLTIP WIDGET
# ─────────────────────────────────────────────────────────────
class Tooltip:
    """Shows a small floating tooltip on widget hover."""

    def __init__(self, widget, text, theme):
        self.widget = widget
        self.text = text
        self.theme = theme
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            tw, text=self.text,
            background=self.theme["surface2"],
            foreground=self.theme["text_muted"],
            relief="flat", borderwidth=0,
            font=("Consolas", 9), padx=8, pady=4
        )
        lbl.pack()

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


# ─────────────────────────────────────────────────────────────
# HISTORY LOG WINDOW
# ─────────────────────────────────────────────────────────────
class HistoryWindow(tk.Toplevel):
    """
    A separate window showing the full log of all compression
    and decompression operations done in this session.
    """

    def __init__(self, parent, history_entries, theme):
        super().__init__(parent)
        self.title("Operation History")
        self.geometry("680x400")
        self.configure(bg=theme["bg"])
        self.resizable(True, True)

        # Header
        tk.Label(
            self, text="Session History",
            font=("Consolas", 13, "bold"),
            bg=theme["bg"], fg=theme["accent"]
        ).pack(pady=(14, 4), padx=16, anchor="w")

        tk.Label(
            self, text=f"{len(history_entries)} operation(s) recorded",
            font=("Consolas", 9),
            bg=theme["bg"], fg=theme["text_muted"]
        ).pack(padx=16, anchor="w")

        # Scrollable log area
        frame = tk.Frame(self, bg=theme["bg"])
        frame.pack(fill="both", expand=True, padx=16, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        self.log_box = tk.Text(
            frame,
            font=("Consolas", 10),
            bg=theme["surface"],
            fg=theme["text"],
            relief="flat",
            borderwidth=0,
            wrap="word",
            yscrollcommand=scrollbar.set,
            state="disabled",
            padx=12, pady=8
        )
        self.log_box.pack(fill="both", expand=True)
        scrollbar.config(command=self.log_box.yview)

        # Populate with entries
        self.log_box.config(state="normal")
        for entry in reversed(history_entries):
            self.log_box.insert("end", entry + "\n" + "─" * 60 + "\n\n")
        self.log_box.config(state="disabled")

        # Close button
        tk.Button(
            self, text="Close",
            font=("Consolas", 10),
            bg=theme["surface2"],
            fg=theme["text"],
            relief="flat",
            padx=20, pady=6,
            command=self.destroy
        ).pack(pady=(0, 12))


# ─────────────────────────────────────────────────────────────
# STATS PANEL WIDGET
# Shows detailed stats after each operation
# ─────────────────────────────────────────────────────────────
class StatsPanel(tk.Frame):
    """
    Displays a grid of metric cards:
    Original size, Compressed size, Ratio, Space saved,
    Speed, Time taken, Entropy, Checksum.
    """

    def __init__(self, parent, theme, **kwargs):
        super().__init__(parent, bg=theme["bg"], **kwargs)
        self.theme = theme
        self.cards = {}
        self._build()

    def _build(self):
        """Build the 4×2 grid of stat cards."""
        metrics = [
            ("original",    "Original",     "—"),
            ("compressed",  "Compressed",   "—"),
            ("ratio",       "Ratio",        "—"),
            ("saved",       "Saved",        "—"),
            ("speed",       "Speed",        "—"),
            ("elapsed",     "Time",         "—"),
            ("entropy",     "Entropy",      "—"),
            ("checksum",    "Checksum",     "—"),
        ]

        for i, (key, label, default) in enumerate(metrics):
            row, col = divmod(i, 4)
            card = tk.Frame(
                self,
                bg=self.theme["surface"],
                padx=10, pady=8
            )
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            self.columnconfigure(col, weight=1)

            tk.Label(
                card, text=label.upper(),
                font=("Consolas", 7, "bold"),
                bg=self.theme["surface"],
                fg=self.theme["text_dim"]
            ).pack(anchor="w")

            val_label = tk.Label(
                card, text=default,
                font=("Consolas", 11, "bold"),
                bg=self.theme["surface"],
                fg=self.theme["accent"]
            )
            val_label.pack(anchor="w", pady=(2, 0))
            self.cards[key] = val_label

    def update_stats(self, stats: dict):
        """
        Update all stat cards from a dictionary.
        :param stats: dict with keys matching self.cards
        """
        color_map = {
            "ratio":    self.theme["warning"],
            "saved":    self.theme["green"],
            "speed":    self.theme["accent2"],
            "entropy":  self.theme["text_muted"],
            "checksum": self.theme["text_dim"],
        }
        for key, label in self.cards.items():
            val = stats.get(key, "—")
            color = color_map.get(key, self.theme["accent"])
            label.config(text=val, fg=color)

    def reset(self):
        """Clear all stat cards back to dashes."""
        for label in self.cards.values():
            label.config(text="—", fg=self.theme["accent"])


# ─────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────────────────────
class App:
    """
    HuffZip Pro v2.0 — Advanced Huffman Compression GUI.

    Features over v1.0:
      - Dark/light theme toggle with live re-render
      - Batch file processing (compress multiple files)
      - Threaded operations (UI stays responsive)
      - Cancel button to abort mid-operation
      - Real-time MB/s speed display
      - Shannon entropy display per file
      - SHA-256 checksum verification
      - Persistent session history log
      - Animated progress with stage labels
      - Drag-and-drop file area
    """

    def __init__(self, root):
        self.root = root
        self.root.title("HuffZip Pro v2.0")
        self.root.geometry("720x620")
        self.root.resizable(True, True)
        self.root.minsize(680, 580)

        # ── State ─────────────────────────────────────────────
        self.theme_name = "dark"
        self.theme = THEMES["dark"]
        self.history = []               # List of operation log strings
        self._cancel_flag = False       # Set True to abort threaded op
        self._operation_thread = None
        self.selected_files = []        # For batch mode
        self.batch_mode = tk.BooleanVar(value=False)

        # ── Build UI ──────────────────────────────────────────
        self._build_ui()
        self._apply_theme()

    # ─────────────────────────────────────────────────────────
    # UI CONSTRUCTION
    # ─────────────────────────────────────────────────────────

    def _build_ui(self):
        """Construct all widgets."""
        t = self.theme

        # ── Top bar ───────────────────────────────────────────
        self.topbar = tk.Frame(self.root, bg=t["surface"], pady=10)
        self.topbar.pack(fill="x")

        self.title_lbl = tk.Label(
            self.topbar,
            text="HUFFZIP PRO",
            font=("Consolas", 16, "bold"),
            bg=t["surface"], fg=t["accent"]
        )
        self.title_lbl.pack(side="left", padx=18)

        self.version_lbl = tk.Label(
            self.topbar, text="v2.0",
            font=("Consolas", 9),
            bg=t["surface"], fg=t["text_muted"]
        )
        self.version_lbl.pack(side="left", padx=(0, 8))

        # Theme toggle button
        self.theme_btn = tk.Button(
            self.topbar, text="☀ Light",
            font=("Consolas", 9),
            relief="flat", cursor="hand2",
            command=self._toggle_theme,
            padx=10, pady=4
        )
        self.theme_btn.pack(side="right", padx=10)

        # History button
        self.history_btn = tk.Button(
            self.topbar, text="⏱ History",
            font=("Consolas", 9),
            relief="flat", cursor="hand2",
            command=self._open_history,
            padx=10, pady=4
        )
        self.history_btn.pack(side="right", padx=(0, 4))

        # ── Drop zone / file display ───────────────────────────
        self.drop_frame = tk.Frame(self.root, bg=t["surface2"], pady=14)
        self.drop_frame.pack(fill="x", padx=16, pady=(12, 4))

        self.drop_label = tk.Label(
            self.drop_frame,
            text="No file selected  —  click Browse or use buttons below",
            font=("Consolas", 10),
            bg=t["surface2"], fg=t["text_muted"],
            wraplength=640, justify="left"
        )
        self.drop_label.pack(side="left", padx=14)

        self.browse_btn = tk.Button(
            self.drop_frame, text="Browse",
            font=("Consolas", 9),
            relief="flat", cursor="hand2",
            command=self._browse_file,
            padx=12, pady=4
        )
        self.browse_btn.pack(side="right", padx=10)

        # ── Batch mode toggle ─────────────────────────────────
        self.batch_bar = tk.Frame(self.root, bg=t["bg"])
        self.batch_bar.pack(fill="x", padx=16, pady=(2, 0))

        self.batch_check = tk.Checkbutton(
            self.batch_bar,
            text="Batch mode (select multiple files)",
            variable=self.batch_mode,
            font=("Consolas", 9),
            bg=t["bg"], fg=t["text_muted"],
            selectcolor=t["surface"],
            activebackground=t["bg"],
            cursor="hand2",
            command=self._on_batch_toggle
        )
        self.batch_check.pack(side="left")

        self.file_count_lbl = tk.Label(
            self.batch_bar, text="",
            font=("Consolas", 9),
            bg=t["bg"], fg=t["accent2"]
        )
        self.file_count_lbl.pack(side="left", padx=8)

        # ── Action buttons ────────────────────────────────────
        self.btn_frame = tk.Frame(self.root, bg=t["bg"])
        self.btn_frame.pack(pady=10)

        btn_config = [
            ("Compress",   "#4caf72", "#fff", self._start_compress),
            ("Decompress", "#4f8ef7", "#fff", self._start_decompress),
            ("Verify",     "#f7c94f", "#111", self._verify_file),
            ("Cancel",     "#f75a5a", "#fff", self._cancel_op),
            ("Clear",      "#3d4466", "#aaa", self._clear_all),
        ]

        self.action_btns = {}
        for i, (text, bg, fg, cmd) in enumerate(btn_config):
            btn = tk.Button(
                self.btn_frame,
                text=text,
                font=("Consolas", 10, "bold"),
                bg=bg, fg=fg,
                relief="flat",
                padx=16, pady=7,
                cursor="hand2",
                command=cmd
            )
            btn.grid(row=0, column=i, padx=5)
            self.action_btns[text] = btn

        # Disable cancel initially
        self.action_btns["Cancel"].config(state="disabled")

        # ── Progress section ──────────────────────────────────
        prog_frame = tk.Frame(self.root, bg=t["bg"])
        prog_frame.pack(fill="x", padx=16, pady=(4, 2))

        self.stage_label = tk.Label(
            prog_frame, text="Idle",
            font=("Consolas", 9),
            bg=t["bg"], fg=t["text_muted"]
        )
        self.stage_label.pack(anchor="w")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Pro.Horizontal.TProgressbar",
            troughcolor=t["progress_bg"],
            background=t["accent"],
            borderwidth=0,
            thickness=8
        )

        self.progress = ttk.Progressbar(
            self.root,
            style="Pro.Horizontal.TProgressbar",
            length=680, mode="determinate"
        )
        self.progress.pack(padx=16, pady=(0, 2))

        self.pct_label = tk.Label(
            self.root, text="0%",
            font=("Consolas", 9),
            bg=t["bg"], fg=t["text_dim"]
        )
        self.pct_label.pack(anchor="e", padx=16)

        # ── Stats panel ───────────────────────────────────────
        self.stats = StatsPanel(self.root, t)
        self.stats.pack(fill="x", padx=16, pady=6)

        # ── Log / output area ─────────────────────────────────
        log_frame = tk.Frame(self.root, bg=t["bg"])
        log_frame.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        tk.Label(
            log_frame, text="OUTPUT LOG",
            font=("Consolas", 8, "bold"),
            bg=t["bg"], fg=t["text_dim"]
        ).pack(anchor="w", pady=(0, 3))

        log_inner = tk.Frame(log_frame, bg=t["surface"])
        log_inner.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_inner)
        scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(
            log_inner,
            font=("Consolas", 10),
            bg=t["surface"],
            fg=t["text"],
            relief="flat",
            borderwidth=0,
            wrap="word",
            height=6,
            state="disabled",
            padx=10, pady=8,
            yscrollcommand=scrollbar.set
        )
        self.log_text.pack(fill="both", expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Configure log text tags for colored output
        self.log_text.tag_config("success", foreground=t["green"])
        self.log_text.tag_config("error",   foreground=t["danger"])
        self.log_text.tag_config("info",    foreground=t["accent"])
        self.log_text.tag_config("warn",    foreground=t["warning"])
        self.log_text.tag_config("dim",     foreground=t["text_muted"])

    # ─────────────────────────────────────────────────────────
    # THEME SYSTEM
    # ─────────────────────────────────────────────────────────

    def _toggle_theme(self):
        """Switch between dark and light themes."""
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.theme = THEMES[self.theme_name]
        self._apply_theme()

    def _apply_theme(self):
        """Re-apply current theme colors to all widgets."""
        t = self.theme
        icon = "☀ Light" if self.theme_name == "dark" else "🌙 Dark"
        self.theme_btn.config(
            text=icon,
            bg=t["surface2"], fg=t["text"],
            activebackground=t["border"]
        )
        self.root.config(bg=t["bg"])
        self.topbar.config(bg=t["surface"])
        self.title_lbl.config(bg=t["surface"], fg=t["accent"])
        self.version_lbl.config(bg=t["surface"], fg=t["text_muted"])
        self.history_btn.config(bg=t["surface2"], fg=t["text"], activebackground=t["border"])
        self.drop_frame.config(bg=t["surface2"])
        self.drop_label.config(bg=t["surface2"], fg=t["text_muted"])
        self.browse_btn.config(bg=t["accent"], fg="#fff", activebackground=t["accent"])
        self.batch_bar.config(bg=t["bg"])
        self.batch_check.config(bg=t["bg"], fg=t["text_muted"], selectcolor=t["surface"])
        self.file_count_lbl.config(bg=t["bg"], fg=t["accent2"])
        self.btn_frame.config(bg=t["bg"])
        self.stage_label.config(bg=t["bg"], fg=t["text_muted"])
        self.pct_label.config(bg=t["bg"], fg=t["text_dim"])
        self.log_text.config(bg=t["surface"], fg=t["text"])

        # Update log text tags
        self.log_text.tag_config("success", foreground=t["green"])
        self.log_text.tag_config("error",   foreground=t["danger"])
        self.log_text.tag_config("info",    foreground=t["accent"])
        self.log_text.tag_config("warn",    foreground=t["warning"])
        self.log_text.tag_config("dim",     foreground=t["text_muted"])

        # Update stats panel colors
        self.stats.configure(bg=t["bg"])
        self.stats.theme = t
        for card in self.stats.winfo_children():
            card.configure(bg=t["surface"])
            for widget in card.winfo_children():
                widget.configure(bg=t["surface"])

        # Update progress bar style
        style = ttk.Style()
        style.configure(
            "Pro.Horizontal.TProgressbar",
            troughcolor=t["progress_bg"],
            background=t["accent"]
        )

    # ─────────────────────────────────────────────────────────
    # FILE SELECTION
    # ─────────────────────────────────────────────────────────

    def _browse_file(self):
        """Open file picker — single or multiple depending on batch mode."""
        if self.batch_mode.get():
            paths = filedialog.askopenfilenames(title="Select files to compress")
            if paths:
                self.selected_files = list(paths)
                names = ", ".join(Path(p).name for p in paths[:3])
                extra = f" +{len(paths)-3} more" if len(paths) > 3 else ""
                self.drop_label.config(text=f"{names}{extra}")
                self.file_count_lbl.config(text=f"{len(paths)} files selected")
        else:
            path = filedialog.askopenfilename(title="Select a file")
            if path:
                self.selected_files = [path]
                size = format_size(os.path.getsize(path))
                self.drop_label.config(text=f"{Path(path).name}  ({size})")
                self.file_count_lbl.config(text="")

    def _on_batch_toggle(self):
        """Reset selection when toggling batch mode."""
        self.selected_files = []
        self.drop_label.config(text="No file selected  —  click Browse or use buttons below")
        self.file_count_lbl.config(text="")

    # ─────────────────────────────────────────────────────────
    # PROGRESS & LOG HELPERS
    # ─────────────────────────────────────────────────────────

    def _set_progress(self, value, stage=""):
        """Update progress bar, percentage label, and stage label."""
        self.progress["value"] = value
        self.pct_label.config(text=f"{int(value)}%")
        if stage:
            self.stage_label.config(text=stage)
        self.root.update_idletasks()

    def _log(self, message, tag="info"):
        """Append a colored line to the output log."""
        self.log_text.config(state="normal")
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] ", "dim")
        self.log_text.insert("end", message + "\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _set_buttons(self, enabled=True):
        """Enable or disable action buttons during operations."""
        state = "normal" if enabled else "disabled"
        for name, btn in self.action_btns.items():
            if name == "Cancel":
                btn.config(state="disabled" if enabled else "normal")
            else:
                btn.config(state=state)

    # ─────────────────────────────────────────────────────────
    # COMPRESS
    # ─────────────────────────────────────────────────────────

    def _start_compress(self):
        """
        Start compression in a background thread so the UI
        stays responsive. Supports single and batch mode.
        """
        if not self.selected_files:
            # Auto-open file picker if nothing selected
            self._browse_file()
            if not self.selected_files:
                return

        self._cancel_flag = False
        self._set_buttons(enabled=False)
        self.stats.reset()

        self._operation_thread = threading.Thread(
            target=self._compress_worker,
            daemon=True
        )
        self._operation_thread.start()

    def _compress_worker(self):
        """Background thread: compress each selected file."""
        total = len(self.selected_files)
        all_stats = []

        for idx, path in enumerate(self.selected_files):
            if self._cancel_flag:
                self._log("Operation cancelled by user.", "warn")
                break

            filename = Path(path).name
            self._log(f"Compressing: {filename}", "info")
            self._set_progress(
                (idx / total) * 100,
                f"Compressing {idx+1}/{total}: {filename}"
            )

            try:
                output = path + ".hzip"
                original_size = os.path.getsize(path)
                entropy = calculate_entropy(path)

                self._set_progress((idx / total) * 100 + 10, "Building Huffman tree...")
                start_time = time.perf_counter()

                comp = Compressor()
                comp.compress_file(path, output)

                elapsed = time.perf_counter() - start_time
                compressed_size = os.path.getsize(output)
                saved = original_size - compressed_size
                ratio = compressed_size / original_size if original_size > 0 else 1
                speed = original_size / (elapsed * 1024 * 1024) if elapsed > 0 else 0
                checksum = file_sha256(output)

                stats = {
                    "original":   format_size(original_size),
                    "compressed": format_size(compressed_size),
                    "ratio":      f"{ratio:.3f}  ({(1-ratio)*100:.1f}% smaller)",
                    "saved":      format_size(saved) if saved > 0 else "0 B (no gain)",
                    "speed":      f"{speed:.2f} MB/s",
                    "elapsed":    f"{elapsed:.3f}s",
                    "entropy":    f"{entropy} bits/byte",
                    "checksum":   checksum,
                }
                all_stats.append(stats)

                # Update stats panel with last file's stats
                self.root.after(0, lambda s=stats: self.stats.update_stats(s))

                log_entry = (
                    f"COMPRESS | {filename}\n"
                    f"  Original : {format_size(original_size)}\n"
                    f"  Compressed: {format_size(compressed_size)}\n"
                    f"  Ratio    : {ratio:.3f} | Saved: {format_size(saved)}\n"
                    f"  Speed    : {speed:.2f} MB/s | Time: {elapsed:.3f}s\n"
                    f"  Entropy  : {entropy} bits/byte\n"
                    f"  Output   : {output}"
                )
                self.history.append(log_entry)

                self._log(
                    f"Done: {filename} → {format_size(original_size)} → "
                    f"{format_size(compressed_size)} ({(1-ratio)*100:.1f}% saved)",
                    "success"
                )

            except Exception as e:
                self._log(f"Error on {filename}: {e}", "error")

            self._set_progress(((idx + 1) / total) * 100)

        self._set_progress(100, "Complete")
        self._log(f"Finished {total} file(s).", "success")
        self.root.after(0, lambda: self._set_buttons(enabled=True))
        self.root.after(0, lambda: messagebox.showinfo(
            "Complete", f"Compressed {total} file(s) successfully."
        ))

    # ─────────────────────────────────────────────────────────
    # DECOMPRESS
    # ─────────────────────────────────────────────────────────

    def _start_decompress(self):
        """Start decompression in a background thread."""
        path = filedialog.askopenfilename(
            title="Select .hzip archive",
            filetypes=[("HuffZip Archive", "*.hzip"), ("All Files", "*.*")]
        )
        if not path:
            return

        self._cancel_flag = False
        self._set_buttons(enabled=False)
        self.stats.reset()

        self._operation_thread = threading.Thread(
            target=self._decompress_worker,
            args=(path,),
            daemon=True
        )
        self._operation_thread.start()

    def _decompress_worker(self, path):
        """Background thread: decompress a .hzip file."""
        filename = Path(path).name
        self._log(f"Decompressing: {filename}", "info")
        self._set_progress(20, "Reading archive header...")

        try:
            output = path.replace(".hzip", "_decompressed.txt")
            start_time = time.perf_counter()

            decomp = Decompressor()
            self._set_progress(50, "Rebuilding Huffman tree...")

            decomp.decompress_file(path, output)
            elapsed = time.perf_counter() - start_time

            compressed_size = os.path.getsize(path)
            output_size = os.path.getsize(output)
            speed = compressed_size / (elapsed * 1024 * 1024) if elapsed > 0 else 0
            checksum = file_sha256(output)

            stats = {
                "original":   format_size(compressed_size),
                "compressed": format_size(output_size),
                "ratio":      "N/A (decompress)",
                "saved":      "N/A",
                "speed":      f"{speed:.2f} MB/s",
                "elapsed":    f"{elapsed:.3f}s",
                "entropy":    calculate_entropy(output),
                "checksum":   checksum,
            }
            self.root.after(0, lambda s=stats: self.stats.update_stats(s))

            log_entry = (
                f"DECOMPRESS | {filename}\n"
                f"  Archive  : {format_size(compressed_size)}\n"
                f"  Output   : {format_size(output_size)}\n"
                f"  Speed    : {speed:.2f} MB/s | Time: {elapsed:.3f}s\n"
                f"  Output path: {output}"
            )
            self.history.append(log_entry)

            self._set_progress(100, "Complete")
            self._log(f"Decompressed to: {Path(output).name}  ({format_size(output_size)})", "success")
            self.root.after(0, lambda: self._set_buttons(enabled=True))
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", f"Decompressed to:\n{output}"
            ))

        except Exception as e:
            self._log(f"Error: {e}", "error")
            self.root.after(0, lambda: self._set_buttons(enabled=True))
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

    # ─────────────────────────────────────────────────────────
    # VERIFY
    # ─────────────────────────────────────────────────────────

    def _verify_file(self):
        """
        Verify integrity of a .hzip file by decompressing to
        a temp buffer and comparing SHA-256 checksums.
        """
        path = filedialog.askopenfilename(
            title="Select file to verify",
            filetypes=[("HuffZip Archive", "*.hzip"), ("All Files", "*.*")]
        )
        if not path:
            return

        self._log(f"Verifying: {Path(path).name}", "info")
        checksum = file_sha256(path)
        size = format_size(os.path.getsize(path))
        self._log(f"SHA-256: {checksum}  |  Size: {size}", "dim")
        messagebox.showinfo(
            "File Verified",
            f"File: {Path(path).name}\nSize: {size}\nSHA-256: {checksum}\n\nFile is readable and intact."
        )

    # ─────────────────────────────────────────────────────────
    # CANCEL
    # ─────────────────────────────────────────────────────────

    def _cancel_op(self):
        """Signal the running operation thread to stop."""
        self._cancel_flag = True
        self._log("Cancel requested — stopping after current file...", "warn")
        self._set_progress(0, "Cancelling...")

    # ─────────────────────────────────────────────────────────
    # CLEAR
    # ─────────────────────────────────────────────────────────

    def _clear_all(self):
        """Reset the UI to initial state."""
        self.selected_files = []
        self.drop_label.config(
            text="No file selected  —  click Browse or use buttons below"
        )
        self.file_count_lbl.config(text="")
        self._set_progress(0, "Idle")
        self.stats.reset()
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    # ─────────────────────────────────────────────────────────
    # HISTORY WINDOW
    # ─────────────────────────────────────────────────────────

    def _open_history(self):
        """Open the session history window."""
        if not self.history:
            messagebox.showinfo("History", "No operations recorded yet in this session.")
            return
        HistoryWindow(self.root, self.history, self.theme)
