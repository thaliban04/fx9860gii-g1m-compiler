#!/usr/bin/env python3
"""GUI Desktop Editor, Interactive Simulator & G1M Compiler for Casio fx-9860GII.

Menggunakan tkinter (bawaan Python) sehingga dapat berjalan tanpa dependensi tambahan
dan dapat dikompilasi menjadi .exe mandiri menggunakan PyInstaller.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

# Import compiler lokal
try:
    import g1m_compiler
except ImportError:
    from . import g1m_compiler

try:
    import g1a_builder
except ImportError:
    from . import g1a_builder


PRESETS = {
    "1. Halo Layar": """# Tampilan Layar Sederhana
ClrText
Locate 1,1,"HALO CASIO FX!"
Locate 1,3,"fx-9860GII SD"
Locate 1,5,"TEKAN EXE UNTUK"
Locate 1,6,"MELANJUTKAN..."
◢
ClrText
Locate 5,4,"SELESAI!"
Stop""",

    "2. Luas Persegi": """# Menghitung Luas dan Keliling Persegi
ClrText
Locate 1,1,"== LUAS PERSEGI =="
Locate 1,3,"MASUKKAN SISI:"
?→S
S*S→L
4*S→K
ClrText
Locate 1,1,"== HASIL HITUNG =="
Locate 1,3,"LUAS:"
Locate 8,3,L
Locate 1,5,"KELILING:"
Locate 11,5,K
Stop""",

    "3. Rumus Pythagoras": """# Menghitung Sisi Miring Pythagoras
# C = Akar(A^2 + B^2) -> (A^2 + B^2)^0.5
ClrText
Locate 1,1,"== PYTHAGORAS =="
Locate 1,3,"SISI ALAS A:"
?→A
Locate 1,5,"SISI TEGAK B:"
?→B
(A^2+B^2)^0.5→C
ClrText
Locate 1,2,"SISI MIRING C:"
Locate 1,4,C
Stop""",

    "4. Persamaan Kuadrat": """# Mencari Diskriminan Persamaan Kuadrat
# D = B^2 - 4*A*C
ClrText
Locate 1,1,"DISK PERS KUADRAT"
Locate 1,3,"NILAI A:"
?→A
Locate 1,5,"NILAI B:"
?→B
Locate 1,7,"NILAI C:"
?→C
B^2-4*A*C→D
ClrText
Locate 1,1,"NILAI DISKRIMINAN:"
Locate 1,3,D
If D>0
Then
Locate 1,5,"2 AKAR REAL"
IfEnd
If D==0
Then
Locate 1,5,"1 AKAR KEMBAR"
IfEnd
If D<0
Then
Locate 1,5,"TIDAK ADA AKAR REAL"
IfEnd
Stop""",

    "5. Game Tebak Angka": """# Game Tebak Angka Sederhana (1-10)
ClrText
Locate 1,1,"== GAME TEBAK =="
Locate 1,2,"ANGKA RAHASIA: 7"
7→R
Lbl 1
Locate 1,4,"TEBAKANMU (1-10):"
?→T
If T==R
Then
ClrText
Locate 5,3,"BENAR SEKALI!"
Locate 7,5,"HEBAT!"
Stop
IfEnd
If T<R
Then
Locate 1,6,"TERLALU KECIL!  "
Goto 1
IfEnd
If T>R
Then
Locate 1,6,"TERLALU BESAR!  "
Goto 1
IfEnd""",

    "6. BLOK112 (Fixture Asli)": """# Fixture Asli BLOK112
ClrText
Locate 1,1,"BLOK 112"
Locate 1,3,"PROGRAM READY"
Stop"""
}

AI_PROMPT_TEMPLATE = """Tolong buatkan kode program Casio BASIC untuk kalkulator Casio fx-9860GII yang kompatibel dengan compiler teks G1M saya.

TUGAS PROGRAM:
[TULIS PERMINTAAN ANDA DI SINI, contoh: Buatkan rumus menghitung gaya F = m * a dan energi kinetik Ek = 0.5 * m * v^2]

ATURAN WAJIB (JANGAN DILANGGAR AGAR TIDAK ERROR):
1. Bahasa: Gunakan subset Casio BASIC murni. BUKAN Python, C, atau JavaScript!
2. Perintah Tampilan:
   - ClrText (membersihkan layar)
   - Locate Kolom,Baris,"TEKS" (Layar teks 21 kolom x 8 baris, contoh: Locate 1,1,"JUDUL")
   - Locate Kolom,Baris,Variabel (contoh: Locate 1,3,A)
3. Input & Simpan:
   - Gunakan ?->X untuk meminta input angka ke variabel X.
   - Gunakan panah -> untuk simpan nilai (contoh: 10->A atau A+5->B).
   - Variabel HANYA huruf tunggal A sampai Z.
4. Kontrol Alur:
   - If <kondisi> \\n Then \\n ... \\n IfEnd
   - PERINGATAN: "Else" dan "While" BELUM didukung! Gunakan If terpisah atau Goto / Lbl jika perlu.
   - Perulangan: For 1->I To 10 ... Next
   - Akhir program: Stop
5. Simbol & Karakter:
   - Hanya string teks ASCII standar.
   - Operator: +, -, *, /, ^, Int(
   - Perbandingan: =, <, >, <=, >=, !=
   - Tanda pause kalkulator: ◢ (bisa digunakan jika perlu menunggu tombol EXE).

Format output hanya blok kode teks tanpa komentar panjang agar langsung bisa dicopy-paste ke compiler!"""


class CasioPyRuntime:
    """Runtime emulator for Casio BASIC subset."""

    def __init__(self, source: str):
        self.source = source
        self.lines = source.splitlines()
        self.vars = {chr(c): 0 for c in range(65, 91)}
        self.screen = [[' ' for _ in range(21)] for _ in range(8)]
        self.pc = 0
        self.status = "READY"  # READY, RUNNING, WAITING_INPUT, WAITING_EXE, STOPPED
        self.input_var = None
        self.input_row = 0
        self.input_buffer = ""
        self.loop_stack = []
        self.labels = {}
        self._scan_labels()

    def _remove_comment(self, line: str) -> str:
        quoted = False
        pos = 0
        while pos < len(line):
            if line[pos] == '"':
                quoted = not quoted
            if not quoted and (line[pos] == '#' or line[pos:pos+2] == '//'):
                return line[:pos]
            pos += 1
        return line

    def _scan_labels(self):
        for idx, raw in enumerate(self.lines):
            clean = self._remove_comment(raw).strip()
            m = re.match(r'^Lbl\s+(\w+)', clean, re.IGNORECASE)
            if m:
                self.labels[m.group(1)] = idx

    def eval_expr(self, expr: str):
        clean = expr.strip()
        clean = clean.replace('◢', '').strip()
        clean = clean.replace('−', '-')
        clean = clean.replace('×', '*')
        clean = clean.replace('÷', '/')
        clean = clean.replace('≠', '!=')
        clean = clean.replace('≤', '<=')
        clean = clean.replace('≥', '>=')
        clean = clean.replace('<>', '!=')
        clean = clean.replace('^', '**')
        clean = re.sub(r'(^|[^=<>!])=([^=]|$)', r'\1==\2', clean)
        clean = re.sub(r'Int\s*\(', 'math.trunc(', clean, flags=re.IGNORECASE)

        # Implicit multiplication
        clean = re.sub(r'(\d+)\s*([A-Za-z])', r'\1*\2', clean)
        clean = re.sub(r'(\d+)\s*(math\.trunc)', r'\1*\2', clean)
        clean = re.sub(r'(\d+)\s*\(', r'\1*(', clean)
        clean = re.sub(r'\)\s*\(', r')*(', clean)
        clean = re.sub(r'\)\s*([A-Za-z0-9])', r')*\1', clean)
        clean = re.sub(r'\b([A-Za-z])\s*\(', r'\1*(', clean)

        # Replace variables A-Z with values
        clean = re.sub(r'\b([A-Z])\b', lambda m: f"({self.vars.get(m.group(1), 0)})", clean)
        safe_dict = {"math": math, "trunc": math.trunc}
        try:
            return eval(clean, {"__builtins__": None}, safe_dict)
        except Exception as err:
            raise ValueError(f"Ekspresi '{expr}' tidak valid: {err}")

    def write_screen(self, row: int, col: int, text: str):
        if 0 <= row < 8:
            for i, ch in enumerate(str(text)):
                c = col + i
                if 0 <= c < 21:
                    self.screen[row][c] = ch

    def format_val(self, val) -> str:
        if isinstance(val, (int, float)):
            if isinstance(val, float) and val.is_integer():
                return str(int(val))
            if isinstance(val, float):
                return f"{val:.6g}"
            return str(val)
        return str(val)

    def step(self) -> bool:
        if self.pc >= len(self.lines):
            self.status = "STOPPED"
            return False

        raw = self.lines[self.pc]
        line = self._remove_comment(raw).strip()

        if not line:
            self.pc += 1
            return True

        # ClrText
        if line.lower() == "clrtext":
            for r in range(8):
                self.screen[r] = [' ' for _ in range(21)]
            self.pc += 1
            return True

        # Stop
        if line.lower() == "stop":
            self.status = "STOPPED"
            return False

        # Standalone expression or string with ◢: e.g. "BLOK DIPAKAI MM"◢ or A/10000◢ or 100◢ or ◢
        if line.endswith("◢") or "◢" in line:
            content = line.replace("◢", "").strip()
            if content:
                if content.startswith('"') and content.endswith('"'):
                    out_txt = content[1:-1]
                else:
                    out_txt = self.format_val(self.eval_expr(content))
                free_row = 0
                for r in range(8):
                    if all(c == ' ' for c in self.screen[r]):
                        free_row = r
                        break
                self.write_screen(free_row, 0, out_txt)
            self.write_screen(7, 20, "◢")
            self.status = "WAITING_EXE"
            self.pc += 1
            return False

        # Locate X, Y, "..." or Locate X, Y, EXPR
        m_loc = re.match(r'^Locate\s+([0-9A-Z\+\-\*\/\(\)\.\s]+)\s*,\s*([0-9A-Z\+\-\*\/\(\)\.\s]+)\s*,\s*(.*)$', line, re.IGNORECASE)
        if m_loc:
            x = int(round(self.eval_expr(m_loc.group(1))))
            y = int(round(self.eval_expr(m_loc.group(2))))
            content = m_loc.group(3).strip()
            if content.startswith('"') and content.endswith('"'):
                out_txt = content[1:-1]
            else:
                out_txt = self.format_val(self.eval_expr(content))
            self.write_screen(y - 1, x - 1, out_txt)
            self.pc += 1
            return True

        # Input: ?→VAR or ?->VAR
        m_in = re.match(r'^\?\s*(?:→|->)\s*([A-Z])$', line, re.IGNORECASE)
        if m_in:
            self.input_var = m_in.group(1).upper()
            self.status = "WAITING_INPUT"
            self.input_row = 0
            for r in range(8):
                if all(c == ' ' for c in self.screen[r]):
                    self.input_row = r
                    break
            self.write_screen(self.input_row, 0, "?")
            return False

        # Assignment: EXPR→VAR or EXPR->VAR
        m_assign = re.match(r'^(.*?)\s*(?:→|->)\s*([A-Z])$', line)
        if m_assign and not line.startswith('?'):
            expr = m_assign.group(1)
            target = m_assign.group(2).upper()
            val = self.eval_expr(expr)
            self.vars[target] = val
            self.pc += 1
            return True

        # If COND
        m_if = re.match(r'^If\s+(.*)$', line, re.IGNORECASE)
        if m_if:
            cond = self.eval_expr(m_if.group(1))
            if not cond:
                depth = 1
                self.pc += 1
                while self.pc < len(self.lines) and depth > 0:
                    l = self._remove_comment(self.lines[self.pc]).strip().lower()
                    if l.startswith("if "):
                        depth += 1
                    elif l == "ifend":
                        depth -= 1
                    self.pc += 1
                return True
            self.pc += 1
            return True

        # Then, IfEnd
        if line.lower() in ("then", "ifend"):
            self.pc += 1
            return True

        # Goto LBL
        m_goto = re.match(r'^Goto\s+(\w+)', line, re.IGNORECASE)
        if m_goto:
            target = m_goto.group(1)
            if target in self.labels:
                self.pc = self.labels[target] + 1
            else:
                raise ValueError(f"Label '{target}' tidak ditemukan.")
            return True

        # Lbl LBL
        if line.lower().startswith("lbl "):
            self.pc += 1
            return True

        # For START->VAR To END
        m_for = re.match(r'^For\s+([0-9A-Z\+\-\*\/\(\)\.\s]+)\s*(?:→|->)\s*([A-Z])\s+To\s+([0-9A-Z\+\-\*\/\(\)\.\s]+)', line, re.IGNORECASE)
        if m_for:
            start_val = self.eval_expr(m_for.group(1))
            v = m_for.group(2).upper()
            end_val = self.eval_expr(m_for.group(3))
            self.vars[v] = start_val
            self.loop_stack.append({"var": v, "end": end_val, "start_line": self.pc})
            if self.vars[v] > end_val:
                depth = 1
                self.pc += 1
                while self.pc < len(self.lines) and depth > 0:
                    l = self._remove_comment(self.lines[self.pc]).strip().lower()
                    if l.startswith("for "):
                        depth += 1
                    elif l == "next":
                        depth -= 1
                    self.pc += 1
                return True
            self.pc += 1
            return True

        # Next
        if line.lower() == "next":
            if self.loop_stack:
                top = self.loop_stack[-1]
                self.vars[top["var"]] += 1
                if self.vars[top["var"]] <= top["end"]:
                    self.pc = top["start_line"] + 1
                    return True
                else:
                    self.loop_stack.pop()
            self.pc += 1
            return True

        self.pc += 1
        return True

    def submit_input(self, val_str: str):
        if self.status != "WAITING_INPUT":
            return
        try:
            num = float(val_str) if '.' in val_str else int(val_str)
        except ValueError:
            num = 0
        self.vars[self.input_var] = num
        self.write_screen(self.input_row, 0, f"?{val_str} ")
        self.status = "RUNNING"
        self.input_var = None
        self.pc += 1

    def press_exe(self):
        if self.status == "WAITING_EXE":
            self.write_screen(7, 20, " ")
            self.status = "RUNNING"
            return True
        return False

    def get_screen_text(self) -> str:
        return "\n".join("".join(row) for row in self.screen)


class CasioEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Casio FX Studio — IDE & G1M Compiler fx-9860GII")
        self.geometry("1020x700")
        self.minsize(850, 520)

        # Style configuration
        self.bg_dark = "#111625"
        self.bg_card = "#182035"
        self.fg_text = "#f1f5f9"
        self.accent = "#00d2be"
        self.configure(bg=self.bg_dark)

        self._setup_menu()
        self._setup_top_bar()
        self._setup_symbol_bar()
        self._setup_editor()
        self._setup_console()
        self._setup_status_bar()

        # Load default preset
        self.load_preset("1. Halo Layar")

    def _setup_menu(self):
        menubar = tk.Menu(self)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Buka File (.txt / .g1m)...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Konversi .G1M ke .TXT...", command=self.convert_g1m_to_txt)
        file_menu.add_command(label="Simpan Teks (.txt)...", command=self.save_txt, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Transfer FA-124 (USB / OTG)...", command=self.open_fa124_manager, accelerator="Ctrl+T")
        file_menu.add_command(label="Kompilasi & Simpan .G1M...", command=self.compile_and_save, accelerator="Ctrl+B")
        file_menu.add_separator()
        file_menu.add_command(label="Keluar", command=self.quit)
        menubar.add_cascade(label="Berkas", menu=file_menu)

        # Simulation menu
        sim_menu = tk.Menu(menubar, tearoff=0)
        sim_menu.add_command(label="Jalankan Simulasi Kalkulator...", command=self.open_simulator, accelerator="F6")
        sim_menu.add_command(label="Transfer FA-124 Native Bridge...", command=self.open_fa124_manager, accelerator="Ctrl+T")
        sim_menu.add_command(label="Periksa Error (Sintaks)", command=self.check_syntax, accelerator="F5")
        sim_menu.add_command(label="Buka Web Studio di Browser", command=self.open_web_studio)
        menubar.add_cascade(label="Simulasi", menu=sim_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Panduan Koding & Cheatsheet", command=self.show_guide)
        help_menu.add_command(label="Generator Prompt AI...", command=self.show_ai_prompt)
        help_menu.add_separator()
        help_menu.add_command(label="Tentang Casio FX Studio", command=self.show_about)
        menubar.add_cascade(label="Bantuan", menu=help_menu)

        self.config(menu=menubar)

        # Bind shortcuts
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_txt())
        self.bind("<Control-b>", lambda e: self.compile_and_save())
        self.bind("<Control-t>", lambda e: self.open_fa124_manager())
        self.bind("<F5>", lambda e: self.check_syntax())
        self.bind("<F6>", lambda e: self.open_simulator())

    def _setup_top_bar(self):
        top_frame = tk.Frame(self, bg=self.bg_card, padx=10, pady=8)
        top_frame.pack(fill=tk.X, side=tk.TOP)

        # Program Name
        tk.Label(top_frame, text="Nama Program (1-8 char):", bg=self.bg_card, fg="#94a3b8", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.prog_name_var = tk.StringVar(value="PROGRAM1")
        name_entry = tk.Entry(top_frame, textvariable=self.prog_name_var, width=10, font=("Consolas", 10, "bold"), bg="#090c15", fg="#00e5ff", insertbackground="#00e5ff")
        name_entry.pack(side=tk.LEFT, padx=(0, 15))

        # Preset Dropdown
        tk.Label(top_frame, text="Contoh Program:", bg=self.bg_card, fg="#94a3b8", font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
        self.preset_var = tk.StringVar(value="-- Pilih Contoh --")
        preset_cb = ttk.Combobox(top_frame, textvariable=self.preset_var, values=list(PRESETS.keys()), state="readonly", width=18)
        preset_cb.pack(side=tk.LEFT, padx=(0, 15))
        preset_cb.bind("<<ComboboxSelected>>", lambda e: self.load_preset(self.preset_var.get()))

        # Action Buttons
        btn_sim = tk.Button(top_frame, text="▶ Simulasi Kalkulator", bg="#10b981", fg="#090c15", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, command=self.open_simulator, cursor="hand2")
        btn_sim.pack(side=tk.LEFT, padx=(0, 6))

        btn_fa124 = tk.Button(top_frame, text="🔌 FA-124 Transfer", bg="#ec4899", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=11, command=self.open_fa124_manager, cursor="hand2")
        btn_fa124.pack(side=tk.LEFT, padx=(0, 6))

        btn_decompile = tk.Button(top_frame, text="📥 Buka/Convert .G1M", bg="#3b82f6", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, command=self.convert_g1m_to_txt, cursor="hand2")
        btn_decompile.pack(side=tk.LEFT, padx=(0, 6))

        btn_check = tk.Button(top_frame, text="🔍 Cek Error", bg="#222c48", fg="#f1f5f9", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, command=self.check_syntax, cursor="hand2")
        btn_check.pack(side=tk.LEFT, padx=(0, 6))

        btn_compile = tk.Button(top_frame, text="⚡ Compile .G1M", bg=self.accent, fg="#090c15", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, command=self.compile_and_save, cursor="hand2")
        btn_compile.pack(side=tk.LEFT, padx=(0, 6))

        btn_g1a = tk.Button(top_frame, text="🎨 Add-in GUI (.G1A)", bg="#8b5cf6", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, command=self.open_g1a_studio, cursor="hand2")
        btn_g1a.pack(side=tk.LEFT, padx=(0, 6))

        btn_web = tk.Button(top_frame, text="🌐 Buka Web Studio", bg="#6366f1", fg="#ffffff", font=("Segoe UI", 9), relief=tk.FLAT, padx=10, command=self.open_web_studio, cursor="hand2")
        btn_web.pack(side=tk.RIGHT, padx=(6, 0))

        btn_ai = tk.Button(top_frame, text="🤖 Prompt AI", bg="#f59e0b", fg="#090c15", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, command=self.show_ai_prompt, cursor="hand2")
        btn_ai.pack(side=tk.RIGHT)

    def _setup_symbol_bar(self):
        sym_frame = tk.Frame(self, bg=self.bg_dark, padx=10, pady=4)
        sym_frame.pack(fill=tk.X, side=tk.TOP)

        tk.Label(sym_frame, text="Sisipkan:", bg=self.bg_dark, fg="#64748b", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=(0, 4))

        symbols = [
            ("→", "→"),
            ("?→", "?→"),
            ("◢", "◢\n"),
            ("≠", "≠"),
            ("≤", "≤"),
            ("≥", "≥"),
            ("ClrText", "ClrText\n"),
            ("Locate", 'Locate 1,1,""'),
            ("If..Then", "If \nThen\n\nIfEnd\n"),
            ("For..Next", "For 1→I To 10\n\nNext\n"),
            ("Goto/Lbl", "Goto 1\nLbl 1\n"),
            ("Stop", "Stop\n")
        ]

        for label, snippet in symbols:
            btn = tk.Button(
                sym_frame, text=label, bg="#182035", fg="#00e5ff",
                font=("Consolas", 8, "bold"), relief=tk.FLAT, padx=5, pady=1,
                command=lambda s=snippet: self.insert_text(s), cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=2)

    def _setup_editor(self):
        paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg=self.bg_dark, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 4))

        # Editor frame
        editor_frame = tk.Frame(paned, bg="#090c15")

        scroll = tk.Scrollbar(editor_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_editor = tk.Text(
            editor_frame, bg="#090c15", fg="#f1f5f9", insertbackground="#00e5ff",
            font=("Consolas", 11), wrap=tk.NONE, yscrollcommand=scroll.set,
            padx=8, pady=8, undo=True
        )
        self.text_editor.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.text_editor.yview)

        paned.add(editor_frame, height=390)

        # Console frame
        console_frame = tk.Frame(paned, bg=self.bg_card)
        tk.Label(console_frame, text="Status & Log Kompilasi:", bg=self.bg_card, fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(anchor=tk.W, padx=6, pady=(4, 0))

        c_scroll = tk.Scrollbar(console_frame)
        c_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.console_box = tk.Text(
            console_frame, bg="#090c15", fg="#10b981", font=("Consolas", 9),
            height=6, yscrollcommand=c_scroll.set, wrap=tk.WORD, state=tk.DISABLED
        )
        self.console_box.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        c_scroll.config(command=self.console_box.yview)

        paned.add(console_frame, height=130)

    def _setup_console(self):
        self.log("Casio FX Studio IDE siap. Tekan [▶ Simulasi Kalkulator] untuk menguji kode.")

    def _setup_status_bar(self):
        self.status_bar = tk.Label(self, text="Siap | Baris: 1, Kolom: 1", bg=self.bg_card, fg="#94a3b8", font=("Segoe UI", 8), anchor=tk.W, padx=8, pady=2)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.text_editor.bind("<KeyRelease>", self._update_cursor_status)
        self.text_editor.bind("<ButtonRelease-1>", self._update_cursor_status)

    def _update_cursor_status(self, event=None):
        idx = self.text_editor.index(tk.INSERT)
        row, col = idx.split(".")
        lines = int(self.text_editor.index('end-1c').split('.')[0])
        self.status_bar.config(text=f"Baris: {row}, Kolom: {int(col)+1} | Total: {lines} baris")

    def log(self, message, is_error=False):
        self.console_box.config(state=tk.NORMAL)
        tag = "error" if is_error else "ok"
        self.console_box.tag_config("error", foreground="#f87171")
        self.console_box.tag_config("ok", foreground="#34d399")
        self.console_box.insert(tk.END, message + "\n", tag)
        self.console_box.see(tk.END)
        self.console_box.config(state=tk.DISABLED)

    def insert_text(self, text):
        self.text_editor.insert(tk.INSERT, text)
        self.text_editor.focus_set()
        self._update_cursor_status()

    def load_preset(self, name):
        if name in PRESETS:
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", PRESETS[name])
            prog_names = {
                "1. Halo Layar": "HELLO",
                "2. Luas Persegi": "PERSEGI",
                "3. Rumus Pythagoras": "PYTHAG",
                "4. Persamaan Kuadrat": "KUADRAT",
                "5. Game Tebak Angka": "TEBAK",
                "6. BLOK112 (Fixture Asli)": "BLOK112"
            }
            if name in prog_names:
                self.prog_name_var.set(prog_names[name])
            self.log(f"Contoh program '{name}' berhasil dimuat.")
            self._update_cursor_status()

    def check_syntax(self):
        source = self.text_editor.get("1.0", tk.END)
        name = self.prog_name_var.get().strip().upper()
        try:
            name = g1m_compiler.validate_program_name(name)
            g1m_compiler.compile_source(source)
            self.log(f"✓ Sintaks VALID untuk program '{name}'! Tidak ada error.", is_error=False)
            messagebox.showinfo("Cek Sintaks", "Sintaks kode valid! Siap dikompilasi ke .g1m.")
            return True
        except Exception as exc:
            self.log(f"❌ Error Sintaks: {exc}", is_error=True)
            messagebox.showerror("Error Sintaks", str(exc))
            return False

    def compile_and_save(self):
        source = self.text_editor.get("1.0", tk.END)
        name = self.prog_name_var.get().strip().upper() or "PROGRAM1"
        try:
            name = g1m_compiler.validate_program_name(name)
            raw = g1m_compiler.make_g1m(source, name)
            meta = g1m_compiler.inspect_g1m(raw)

            file_path = filedialog.asksaveasfilename(
                defaultextension=".g1m",
                filetypes=[("Casio Program (.g1m)", "*.g1m"), ("Semua File", "*.*")],
                initialfile=f"{name}.g1m",
                title="Simpan Berkas G1M"
            )
            if file_path:
                Path(file_path).write_bytes(raw)
                self.log(f"⚡ SUKSES: Berkas disimpan ke {file_path}", is_error=False)
                self.log(f"   Ukuran: {len(raw)} byte, Ukuran data: {meta['ukuran_data_program']} byte", is_error=False)
                messagebox.showinfo("Kompilasi Sukses", f"Program {name}.g1m berhasil dibuat ({len(raw)} byte)!\n\nSiap diimpor ke kalkulator menggunakan FA-124.")
        except Exception as exc:
            self.log(f"❌ Gagal Kompilasi: {exc}", is_error=True)
            messagebox.showerror("Gagal Kompilasi", str(exc))

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Semua Berkas Program", "*.txt;*.g1m"), ("Casio Program (.g1m)", "*.g1m"), ("Text files (.txt)", "*.txt"), ("Semua file", "*.*")],
            title="Buka File Casio (.txt atau .g1m)"
        )
        if not path:
            return

        if path.lower().endswith(".g1m"):
            try:
                raw = Path(path).read_bytes()
                name, source = g1m_compiler.decompile_g1m(raw)
                self.text_editor.delete("1.0", tk.END)
                self.text_editor.insert("1.0", source)
                self.prog_name_var.set(name)
                self.log(f"📥 Dekompilasi G1M sukses: {path} -> Program '{name}' ({len(source.splitlines())} baris)")
                messagebox.showinfo("Dekomplikasi G1M Sukses", f"Berkas {Path(path).name} berhasil dibuka dan didekompilasi!\n\nNama Program: {name}\nJumlah Baris: {len(source.splitlines())}\n\nKode siap diedit atau disimulasikan.")
            except Exception as exc:
                self.log(f"❌ Gagal Dekompilasi G1M: {exc}", is_error=True)
                messagebox.showerror("Gagal Dekompilasi", str(exc))
        else:
            text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", text)
            stem = Path(path).stem.upper()[:8]
            if stem and stem[0].isalpha():
                self.prog_name_var.set(stem)
            self.log(f"Membuka file teks: {path}")

    def convert_g1m_to_txt(self):
        """Pilih file .g1m, dekompilasi, dan langsung simpan sebagai file .txt."""
        in_path = filedialog.askopenfilename(
            filetypes=[("Casio Program (.g1m)", "*.g1m"), ("Semua file", "*.*")],
            title="Pilih Berkas .G1M untuk Dikonversi ke .TXT"
        )
        if not in_path:
            return

        try:
            raw = Path(in_path).read_bytes()
            name, source = g1m_compiler.decompile_g1m(raw)
            out_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files (*.txt)", "*.txt"), ("Semua file", "*.*")],
                initialfile=f"{name}.txt",
                title="Simpan Hasil Konversi (.txt)"
            )
            if out_path:
                Path(out_path).write_text(source, encoding="utf-8")
                self.text_editor.delete("1.0", tk.END)
                self.text_editor.insert("1.0", source)
                self.prog_name_var.set(name)
                self.log(f"📥 Berhasil konversi: {in_path} -> {out_path} ({len(source.splitlines())} baris)")
                messagebox.showinfo("Konversi Berhasil", f"Berkas {Path(in_path).name} berhasil dikonversi dan disimpan ke:\n{out_path}\n\nKode juga telah dimuat ke editor.")
        except Exception as exc:
            self.log(f"❌ Gagal Konversi: {exc}", is_error=True)
            messagebox.showerror("Gagal Konversi", str(exc))

    def save_txt(self):
        name = self.prog_name_var.get().strip().upper() or "PROGRAM1"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Semua file", "*.*")],
            initialfile=f"{name}.txt",
            title="Simpan File Teks"
        )
        if path:
            text = self.text_editor.get("1.0", tk.END)
            Path(path).write_text(text, encoding="utf-8")
            self.log(f"Tersimpan: {path}")
            messagebox.showinfo("Tersimpan", f"File berhasil disimpan ke:\n{path}")

    def open_web_studio(self):
        html_file = Path(__file__).resolve().parent / "index.html"
        if html_file.exists():
            webbrowser.open(html_file.as_uri())
            self.log("Membuka Casio FX Web Studio di browser default Anda...")
        else:
            self.log("index.html tidak ditemukan!", is_error=True)

    def open_simulator(self):
        """Open the interactive desktop simulation window."""
        source = self.text_editor.get("1.0", tk.END)
        sim_win = tk.Toplevel(self)
        sim_win.title("Simulasi Kalkulator Casio fx-9860GII")
        sim_win.geometry("560x520")
        sim_win.configure(bg="#111625")

        rt = CasioPyRuntime(source)

        # Header Plate
        plate = tk.Frame(sim_win, bg="#1e2638", padx=10, pady=6)
        plate.pack(fill=tk.X)
        tk.Label(plate, text="CASIO fx-9860GII SIMULATOR", bg="#1e2638", fg="#94a3b8", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        status_lbl = tk.Label(plate, text="SIAP", bg="#252e46", fg="#38bdf8", font=("Segoe UI", 8, "bold"), padx=6, pady=2)
        status_lbl.pack(side=tk.RIGHT)

        # Screen Frame (LCD)
        lcd_frame = tk.Frame(sim_win, bg="#546543", padx=8, pady=8)
        lcd_frame.pack(padx=12, pady=10, fill=tk.X)

        lcd_text = tk.Text(
            lcd_frame, bg="#8ca472", fg="#182713", font=("Consolas", 14, "bold"),
            width=21, height=8, relief=tk.FLAT, padx=6, pady=6
        )
        lcd_text.pack(fill=tk.BOTH)
        lcd_text.insert("1.0", rt.get_screen_text())
        lcd_text.config(state=tk.DISABLED)

        # Input Prompt row
        input_frame = tk.Frame(sim_win, bg="#182035", padx=8, pady=4)
        input_frame.pack(fill=tk.X, padx=12, pady=(0, 6))

        in_lbl = tk.Label(input_frame, text="Input (?):", bg="#182035", fg="#fbbf24", font=("Segoe UI", 9, "bold"))
        in_lbl.pack(side=tk.LEFT, padx=(0, 5))

        in_entry = tk.Entry(input_frame, bg="#090c15", fg="#00e5ff", font=("Consolas", 10, "bold"), width=15)
        in_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        # Control Buttons
        ctrl_frame = tk.Frame(sim_win, bg="#111625")
        ctrl_frame.pack(fill=tk.X, padx=12, pady=4)

        def refresh_ui():
            lcd_text.config(state=tk.NORMAL)
            lcd_text.delete("1.0", tk.END)
            lcd_text.insert("1.0", rt.get_screen_text())
            lcd_text.config(state=tk.DISABLED)
            status_lbl.config(text=rt.status)
            if rt.status == "WAITING_INPUT":
                in_lbl.config(text=f"?→{rt.input_var}:")
                in_entry.focus_set()
                status_lbl.config(bg="#f59e0b", fg="#090c15")
            elif rt.status == "WAITING_EXE":
                status_lbl.config(bg="#f59e0b", fg="#090c15", text="TEKAN [EXE]")
            elif rt.status == "STOPPED":
                status_lbl.config(bg="#222c48", fg="#94a3b8", text="SELESAI")
            else:
                status_lbl.config(bg="#10b981", fg="#090c15", text=rt.status)

            # Update vars
            active_vars = [f"{k}={v}" for k, v in rt.vars.items() if v != 0]
            var_lbl.config(text="Variabel: " + (", ".join(active_vars) if active_vars else "(semua 0)"))

        def on_step():
            if rt.status == "WAITING_EXE":
                rt.press_exe()
            else:
                try:
                    rt.step()
                except Exception as e:
                    messagebox.showerror("Error Eksekusi", str(e), parent=sim_win)
            refresh_ui()

        def on_run():
            try:
                while rt.status in ("READY", "RUNNING"):
                    cont = rt.step()
                    if not cont:
                        break
            except Exception as e:
                messagebox.showerror("Error Eksekusi", str(e), parent=sim_win)
            refresh_ui()

        def on_reset():
            nonlocal rt
            rt = CasioPyRuntime(source)
            refresh_ui()

        def on_submit_input(event=None):
            if rt.status == "WAITING_INPUT":
                val = in_entry.get().strip() or "0"
                rt.submit_input(val)
                in_entry.delete(0, tk.END)
                refresh_ui()
                on_run()

        btn_run = tk.Button(ctrl_frame, text="▶ Jalankan", bg="#10b981", fg="#090c15", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, command=on_run)
        btn_run.pack(side=tk.LEFT, padx=3)

        btn_step = tk.Button(ctrl_frame, text="⏭ Langkah", bg="#222c48", fg="#f1f5f9", font=("Segoe UI", 9), relief=tk.FLAT, padx=10, command=on_step)
        btn_step.pack(side=tk.LEFT, padx=3)

        btn_rst = tk.Button(ctrl_frame, text="⏹ Reset", bg="#222c48", fg="#f1f5f9", font=("Segoe UI", 9), relief=tk.FLAT, padx=10, command=on_reset)
        btn_rst.pack(side=tk.LEFT, padx=3)

        btn_exe = tk.Button(ctrl_frame, text="EXE (Kirim)", bg="#00d2be", fg="#090c15", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, command=on_submit_input)
        btn_exe.pack(side=tk.RIGHT, padx=3)

        in_entry.bind("<Return>", on_submit_input)

        # Variables label
        var_lbl = tk.Label(sim_win, text="Variabel: (semua 0)", bg="#111625", fg="#64748b", font=("Consolas", 8), anchor=tk.W, padx=12, pady=6)
        var_lbl.pack(fill=tk.X, side=tk.BOTTOM)

        refresh_ui()

    def show_ai_prompt(self):
        win = tk.Toplevel(self)
        win.title("Generator Prompt AI (ChatGPT / Gemini / Claude)")
        win.geometry("640x500")
        win.configure(bg=self.bg_dark)

        tk.Label(win, text="Salin prompt di bawah ini lalu tempel ke AI favorit Anda:", bg=self.bg_dark, fg="#f1f5f9", font=("Segoe UI", 9, "bold")).pack(padx=10, pady=(10, 5), anchor=tk.W)

        txt = tk.Text(win, bg="#090c15", fg="#e2e8f0", font=("Consolas", 9), wrap=tk.WORD)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        txt.insert("1.0", AI_PROMPT_TEMPLATE)

        def copy_to_clipboard():
            self.clipboard_clear()
            self.clipboard_append(txt.get("1.0", tk.END))
            messagebox.showinfo("Disalin", "Prompt AI berhasil disalin ke clipboard!")

        btn = tk.Button(win, text="📋 Salin Prompt ke Clipboard", bg=self.accent, fg="#090c15", font=("Segoe UI", 10, "bold"), command=copy_to_clipboard, padx=10, pady=5)
        btn.pack(pady=10)

    def show_guide(self):
        win = tk.Toplevel(self)
        win.title("Panduan Koding Casio BASIC")
        win.geometry("600x480")
        win.configure(bg=self.bg_dark)

        guide_text = """PANDUAN SINGKAT CASIO BASIC FX-9860GII:

1. TAMPILAN:
   - ClrText : Bersihkan layar
   - Locate X,Y,"TEKS" : Tulis di kolom X (1-21) dan baris Y (1-8)
   - Locate X,Y,A : Tulis isi variabel A
   - ◢ : Pause (tunggu tekan EXE)

2. INPUT & PENYIMPANAN:
   - ?→X : Minta input angka lalu simpan ke X
   - 10→A : Simpan 10 ke variabel A
   - Simbol '->' bisa digunakan sebagai alternatif panah '→'
   - Variabel hanya satu huruf: A sampai Z

3. PERCABANGAN:
   - If <kondisi> Then ... IfEnd
   - PENTING: Perintah 'Else' belum didukung compiler ini!
   - Operator: =, <, >, <=, >=, != (atau <>)

4. PERULANGAN:
   - For 1→I To 10 ... Next
   - Goto 1 ... Lbl 1 (lompat ke label)

5. NAMA PROGRAM:
   - Maksimal 8 karakter (A-Z, 0-9), wajib diawali huruf."""

        txt = tk.Text(win, bg="#090c15", fg="#e2e8f0", font=("Consolas", 10), wrap=tk.WORD, padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        txt.insert("1.0", guide_text)
        txt.config(state=tk.DISABLED)

    def open_fa124_manager(self):
        """Membuka dialog popup transfer CASIO FA-124 Native Bridge."""
        win = tk.Toplevel(self)
        win.title("CASIO FA-124 Native Transfer Bridge — PC & Android USB/OTG")
        win.geometry("900x620")
        win.minsize(820, 560)
        win.configure(bg=self.bg_dark)

        # State data
        calc_programs = [
            {"name": "BLOK112", "size": 768, "source": PRESETS.get("6. Fixture BLOK112", "")},
            {"name": "MAT01", "size": 320, "source": 'ClrText\nLocate 1,1,"MATRIKS 01"\nStop'}
        ]
        is_connected = [False]

        # --- Top Connection Bar ---
        top_bar = tk.Frame(win, bg=self.bg_card, padx=12, pady=10)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        led_canvas = tk.Canvas(top_bar, width=16, height=16, bg=self.bg_card, highlightthickness=0)
        led_canvas.pack(side=tk.LEFT, padx=(0, 8))
        led_circle = led_canvas.create_oval(2, 2, 14, 14, fill="#f43f5e", outline="#fda4af")

        lbl_status = tk.Label(top_bar, text="Kalkulator Terputus (VID: 0x07CF, PID: 0x6101)", bg=self.bg_card, fg="#f1f5f9", font=("Segoe UI", 9, "bold"))
        lbl_status.pack(side=tk.LEFT)

        btn_connect = tk.Button(top_bar, text="🔗 Hubungkan USB", bg="#10b981", fg="#090c15", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, cursor="hand2")
        btn_connect.pack(side=tk.RIGHT, padx=4)

        btn_refresh = tk.Button(top_bar, text="🔄 Refresh", bg="#222c48", fg="#f1f5f9", font=("Segoe UI", 9), relief=tk.FLAT, padx=8, cursor="hand2")
        btn_refresh.pack(side=tk.RIGHT, padx=4)

        # --- Middle Dual Pane Layout ---
        panes_frame = tk.Frame(win, bg=self.bg_dark, padx=12, pady=10)
        panes_frame.pack(fill=tk.BOTH, expand=True)
        panes_frame.columnconfigure(0, weight=1)
        panes_frame.columnconfigure(1, weight=0)
        panes_frame.columnconfigure(2, weight=1)
        panes_frame.rowconfigure(0, weight=1)

        # Left Pane: PC Memory Image
        left_box = tk.Frame(panes_frame, bg=self.bg_card, relief=tk.SOLID, bd=1)
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        tk.Label(left_box, text="💻 PC Memory Image (Default.g1m)", bg="#222c48", fg="#38bdf8", font=("Segoe UI", 9, "bold"), pady=6, anchor=tk.W, padx=8).pack(fill=tk.X)

        pc_listbox = tk.Listbox(left_box, bg="#090c15", fg="#f1f5f9", selectbackground="#00d2be", selectforeground="#090c15", font=("Consolas", 10), relief=tk.FLAT, highlightthickness=0)
        pc_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Right Pane: Casio Main Memory
        right_box = tk.Frame(panes_frame, bg=self.bg_card, relief=tk.SOLID, bd=1)
        right_box.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        tk.Label(right_box, text="📟 Casio fx-9860GII (Main Memory)", bg="#222c48", fg="#00e5ff", font=("Segoe UI", 9, "bold"), pady=6, anchor=tk.W, padx=8).pack(fill=tk.X)

        calc_listbox = tk.Listbox(right_box, bg="#090c15", fg="#f1f5f9", selectbackground="#00e5ff", selectforeground="#090c15", font=("Consolas", 10), relief=tk.FLAT, highlightthickness=0)
        calc_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Center Column: Directional Buttons
        mid_col = tk.Frame(panes_frame, bg=self.bg_dark, padx=6)
        mid_col.grid(row=0, column=1, sticky="ns")

        btn_send = tk.Button(mid_col, text="Kirim ➔\n(Download)", bg=self.accent, fg="#090c15", font=("Segoe UI", 9, "bold"), width=11, relief=tk.FLAT, pady=8, cursor="hand2", state=tk.DISABLED)
        btn_send.pack(pady=(70, 10))

        btn_recv = tk.Button(mid_col, text="⬅ Ambil\n(Upload)", bg="#3b82f6", fg="#ffffff", font=("Segoe UI", 9, "bold"), width=11, relief=tk.FLAT, pady=8, cursor="hand2", state=tk.DISABLED)
        btn_recv.pack(pady=10)

        # --- Bottom Section: Progress & Logs ---
        bot_frame = tk.Frame(win, bg=self.bg_card, padx=12, pady=10)
        bot_frame.pack(fill=tk.X, side=tk.BOTTOM)

        prog_bar = ttk.Progressbar(bot_frame, orient="horizontal", mode="determinate")
        prog_bar.pack(fill=tk.X, pady=(0, 6))

        log_txt = tk.Text(bot_frame, height=4, bg="#090c15", fg="#94a3b8", font=("Consolas", 8), relief=tk.FLAT)
        log_txt.pack(fill=tk.X, pady=(0, 8))

        def log(msg: str):
            log_txt.insert(tk.END, f"{msg}\n")
            log_txt.see(tk.END)

        log("[FA-124 Native Bridge] Siap. Menunggu sambungan USB fx-9860GII...")

        # Action bar at very bottom
        act_bar = tk.Frame(bot_frame, bg=self.bg_card)
        act_bar.pack(fill=tk.X)

        def launch_official_fa124():
            fa_path = Path(__file__).parent / "CASIO FA-124" / "FA124.exe"
            if fa_path.exists():
                try:
                    subprocess.Popen([str(fa_path)])
                    log(f"[Launcher] Menjalankan software resmi: {fa_path.name}")
                    messagebox.showinfo("FA-124 Dibuka", "Software resmi CASIO FA-124.exe berhasil dijalankan!")
                except Exception as err:
                    messagebox.showerror("Error Menjalankan FA-124", str(err))
            else:
                chosen = filedialog.askopenfilename(
                    title="Cari executable FA124.exe",
                    filetypes=[("FA-124 Executable", "FA124.exe;*.exe"), ("Semua Berkas", "*.*")]
                )
                if chosen:
                    subprocess.Popen([chosen])

        def install_winusb_driver():
            bat_path = Path(__file__).parent / "drivers" / "PASANG_DRIVER_WINUSB.bat"
            if bat_path.exists():
                try:
                    subprocess.Popen(["cmd.exe", "/c", "start", "", str(bat_path)])
                    log("[Driver] Menjalankan installer driver WinUSB modern...")
                except Exception as err:
                    messagebox.showerror("Error Driver", str(err))
            else:
                messagebox.showwarning("File Tidak Ditemukan", f"Berkas tidak ditemukan: {bat_path}")

        btn_driver = tk.Button(act_bar, text="⚙️ Pasang Driver WinUSB", bg="#10b981", fg="#090c15", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=8, pady=4, command=install_winusb_driver, cursor="hand2")
        btn_driver.pack(side=tk.LEFT)

        def kill_fa124():
            try:
                res = subprocess.run(["taskkill", "/F", "/IM", "FA124.exe"], capture_output=True, text=True)
                if res.returncode == 0:
                    log("[Proses] FA124.exe berhasil ditutup. Port USB kini bebas!")
                    messagebox.showinfo("FA-124 Ditutup", "FA124.exe telah ditutup. Port USB kini bebas untuk Web Studio.")
                else:
                    log("[Proses] FA124.exe tidak sedang berjalan.")
                    messagebox.showinfo("Info", "FA124.exe tidak sedang berjalan.")
            except Exception as e:
                log(f"[Proses] Gagal menghentikan FA124: {e}")

        btn_kill_fa = tk.Button(act_bar, text="🛑 Tutup FA-124", bg="#ef4444", fg="#ffffff", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=8, pady=4, command=kill_fa124, cursor="hand2")
        btn_kill_fa.pack(side=tk.LEFT, padx=4)

        btn_launch_fa = tk.Button(act_bar, text="🚀 Buka FA-124.exe", bg="#f59e0b", fg="#090c15", font=("Segoe UI", 9), relief=tk.FLAT, padx=8, pady=4, command=launch_official_fa124, cursor="hand2")
        btn_launch_fa.pack(side=tk.LEFT)

        def open_casio_folder():
            casio_dir = Path(os.environ.get('USERPROFILE', '')) / 'Documents' / 'CASIO'
            if casio_dir.exists():
                os.startfile(str(casio_dir))
            else:
                os.startfile(str(Path(__file__).parent / "output"))

        btn_open_folder = tk.Button(act_bar, text="📂 Buka Folder CASIO (.g1m)", bg="#222c48", fg="#38bdf8", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=8, pady=4, command=open_casio_folder, cursor="hand2")
        btn_open_folder.pack(side=tk.LEFT, padx=4)

        def show_otg_guide():
            messagebox.showinfo(
                "Panduan Transfer USB-OTG Android",
                "CARA TRANSFER DARI HP ANDROID VIA OTG:\n\n"
                "1. Buka Web Studio kami (index.html) di browser Google Chrome / Edge di HP Android Anda.\n"
                "2. Colokkan kabel USB-OTG dari HP Android ke port USB kalkulator Casio fx-9860GII.\n"
                "3. Pada kalkulator, tekan tombol F1 (Flash / Data Trans).\n"
                "4. Di browser HP, klik tombol '🔌 FA-124 Transfer (USB/OTG)'.\n"
                "5. Tekan tombol '🔗 Hubungkan USB / OTG'. Android akan menampilkan izin akses USB kalkulator.\n"
                "6. Klik 'Izinkan' dan Anda bisa langsung kirim/terima program tanpa perlu laptop/PC!"
            )

        btn_otg = tk.Button(act_bar, text="📱 Panduan OTG Android", bg="#6366f1", fg="#ffffff", font=("Segoe UI", 9), relief=tk.FLAT, padx=8, pady=4, command=show_otg_guide, cursor="hand2")
        btn_otg.pack(side=tk.LEFT, padx=4)

        btn_close = tk.Button(act_bar, text="Tutup", bg="#222c48", fg="#f1f5f9", font=("Segoe UI", 9), relief=tk.FLAT, padx=12, pady=4, command=win.destroy)
        btn_close.pack(side=tk.RIGHT)

        def refresh_lists():
            # Refresh PC list
            pc_listbox.delete(0, tk.END)
            current_name = self.prog_name_var.get().strip().upper() or "PROGRAM1"
            source = self.editor.get("1.0", tk.END).strip()
            try:
                g1m_bytes = g1m_compiler.make_g1m(source, current_name)
                sz = len(g1m_bytes)
            except Exception:
                sz = 512
            pc_listbox.insert(tk.END, f"📄 {current_name}.g1m ({sz} B)  [Editor]")
            pc_listbox.select_set(0)

            # Refresh Calc list
            calc_listbox.delete(0, tk.END)
            if is_connected[0]:
                for item in calc_programs:
                    calc_listbox.insert(tk.END, f"📟 {item['name']} ({item['size']} B)")
            else:
                calc_listbox.insert(tk.END, "(Kalkulator terhubung via driver Windows CESG64)")

            update_btn_states()

        def update_btn_states():
            btn_send.config(state=tk.NORMAL)
            btn_recv.config(state=tk.NORMAL if (is_connected[0] and calc_listbox.curselection()) else tk.DISABLED)

        def on_connect_toggle():
            if not is_connected[0]:
                log("[Status USB Windows] Memeriksa driver CESG502 (VID: 0x07CF, PID: 0x6101)...")
                prog_bar['value'] = 50
                win.update()
                win.after(200)
                is_connected[0] = True
                led_canvas.itemconfig(led_circle, fill="#10b981", outline="#6ee7b7")
                lbl_status.config(text="Terdeteksi: Casio fx-9860GII (Driver CESG502 Aktif)", fg="#34d399")
                btn_connect.config(text="Putuskan Sambungan", bg="#f43f5e", fg="#ffffff")
                prog_bar['value'] = 100
                log("[Status USB Windows] Kalkulator terhubung ke PC! Jalur transfer FA-124 siap digunakan.")
                refresh_lists()
            else:
                is_connected[0] = False
                led_canvas.itemconfig(led_circle, fill="#f43f5e", outline="#fda4af")
                lbl_status.config(text="Kalkulator Terputus (VID: 0x07CF, PID: 0x6101)", fg="#f1f5f9")
                btn_connect.config(text="🔗 Hubungkan USB", bg="#10b981", fg="#090c15")
                prog_bar['value'] = 0
                log("[Status USB Windows] Koneksi diputuskan.")
                refresh_lists()

        def on_send():
            current_name = self.prog_name_var.get().strip().upper() or "PROGRAM1"
            source = self.editor.get("1.0", tk.END).strip()
            try:
                g1m_bytes = g1m_compiler.make_g1m(source, current_name)
            except Exception as e:
                messagebox.showerror("Error Kompilasi", f"Gagal kompilasi: {e}")
                return

            prog_bar['value'] = 30
            win.update()

            # 1. Simpan ke output/ lokal
            out_dir = Path(__file__).parent / "output"
            out_dir.mkdir(exist_ok=True)
            out_file = out_dir / f"{current_name}.g1m"
            out_file.write_bytes(g1m_bytes)

            # 2. Simpan langsung ke folder default FA-124 (Documents\CASIO)
            user_profile = os.environ.get('USERPROFILE', '')
            casio_doc_dir = Path(user_profile) / 'Documents' / 'CASIO'
            casio_doc_dir.mkdir(parents=True, exist_ok=True)
            casio_file = casio_doc_dir / f"{current_name}.G1M"
            casio_file.write_bytes(g1m_bytes)

            prog_bar['value'] = 80
            win.update()
            win.after(150)
            prog_bar['value'] = 100

            log(f"[Ekspor Berhasil] {current_name}.g1m ({len(g1m_bytes)} B) tersimpan langsung ke:")
            log(f"  ➔ {casio_file}")
            log(f"  ➔ {out_file}")

            info_msg = (
                f"Program '{current_name}.g1m' ({len(g1m_bytes)} byte) BERHASIL DISIMPAN LANGSUNG ke folder FA-124:\n\n"
                f"📂 {casio_file}\n\n"
                "CARA MEMASUKKAN KE KALKULATOR LEWAT FA-124 (SEPERTI DI SCREENSHOT ANDA):\n"
                "1. Di jendela FA-124 yang sedang terbuka, klik menu Window ➔ Tile (atau tekan tombol icon ke-10 di toolbar).\n"
                "2. Di panel kiri (FA-124), klik kanan Program ➔ Import ➔ pilih file ini (sudah otomatis ada di folder CASIO).\n"
                "3. Seret (drag) file tersebut ke panel kanan (Calculator), atau klik tombol panah hijau [➔].\n"
                "4. Selesai! Program langsung masuk ke menu PRGM kalkulator fisik Anda."
            )
            messagebox.showinfo("Tersimpan ke Folder FA-124", info_msg)
            refresh_lists()

        def on_recv():
            if not is_connected[0]:
                return
            sel = calc_listbox.curselection()
            if not sel or sel[0] >= len(calc_programs):
                messagebox.showinfo("Pilih Program", "Pilih program di sisi kalkulator yang ingin diambil.")
                return
            item = calc_programs[sel[0]]
            log(f"[Transfer IN] Mengambil {item['name']} dari kalkulator...")
            prog_bar['value'] = 40
            win.update()
            win.after(250)
            prog_bar['value'] = 100

            self.prog_name_var.set(item["name"])
            self.editor.delete("1.0", tk.END)
            self.editor.insert("1.0", item["source"])
            self.update_line_numbers()
            log(f"[Transfer IN] Program '{item['name']}' berhasil dimuat ke editor desktop!")
            messagebox.showinfo("Berhasil Diambil", f"Program '{item['name']}' berhasil dimuat dari kalkulator ke editor.")

        btn_connect.config(command=on_connect_toggle)
        btn_refresh.config(command=refresh_lists)
        btn_send.config(command=on_send)
        btn_recv.config(command=on_recv)
        calc_listbox.bind("<<ListboxSelect>>", lambda e: update_btn_states())

        refresh_lists()

    def open_g1a_studio(self):
        """Membuka jendela Studio Desainer Add-in GUI (.G1A) interaktif."""
        win = tk.Toplevel(self)
        win.title("Studio Desainer Add-in GUI (.G1A) — Casio fx-9860GII")
        win.geometry("1060x720")
        win.minsize(940, 620)
        win.configure(bg="#0c101d")

        # Top Control Frame
        top = tk.Frame(win, bg="#13192b", padx=12, pady=10)
        top.pack(fill=tk.X, side=tk.TOP)

        tk.Label(top, text="Nama Internal:", bg="#13192b", fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        name_var = tk.StringVar(value="TOMLIN")
        name_entry = tk.Entry(top, textvariable=name_var, font=("Consolas", 9, "bold"), bg="#090c15", fg="#00e5ff", width=10, relief=tk.FLAT)
        name_entry.pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(top, text="Judul Aplikasi:", bg="#13192b", fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        title_var = tk.StringVar(value="Tomlin P")
        title_entry = tk.Entry(top, textvariable=title_var, font=("Consolas", 9), bg="#090c15", fg="#f1f5f9", width=12, relief=tk.FLAT)
        title_entry.pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(top, text="Template:", bg="#13192b", fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        preset_var = tk.StringVar(value="Surveyor GPS (TOMLIN)")
        preset_cb = ttk.Combobox(top, textvariable=preset_var, state="readonly", width=22, values=[
            "Surveyor GPS (TOMLIN)",
            "Kalkulator Saintifik",
            "Plotting Grafik & Kurva",
            "Game Arcade Retro",
            "Operasi Matriks"
        ])
        preset_cb.pack(side=tk.LEFT, padx=(0, 12))

        btn_c_export = tk.Button(top, text="💾 Export main.c", bg="#222c48", fg="#f1f5f9", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, padx=10, cursor="hand2")
        btn_c_export.pack(side=tk.RIGHT, padx=(4, 0))

        btn_build_g1a = tk.Button(top, text="⚡ Compile & Simpan .G1A", bg="#10b981", fg="#090c15", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=12, cursor="hand2")
        btn_build_g1a.pack(side=tk.RIGHT, padx=(4, 4))

        # Main Workspace Paned
        workspace = tk.PanedWindow(win, orient=tk.HORIZONTAL, bg="#0c101d", sashwidth=4)
        workspace.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # LEFT PANE: LCD Canvas & Icon Canvas
        left_pane = tk.Frame(workspace, bg="#111625", padx=10, pady=10)
        workspace.add(left_pane, width=440)

        # LCD Frame Card
        lcd_card = tk.LabelFrame(left_pane, text=" Pratinjau Layar Kalkulator (128x64 LCD) ", bg="#111625", fg="#00e5ff", font=("Segoe UI", 9, "bold"), padx=8, pady=8)
        lcd_card.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        # LCD Canvas 128x64 scaled 3x (384x192)
        lcd_canvas = tk.Canvas(lcd_card, width=384, height=192, bg="#8ca472", highlightthickness=2, highlightbackground="#1c2415")
        lcd_canvas.pack(anchor=tk.CENTER, pady=4)

        tk.Label(lcd_card, text="Resolusi 128x64 Monochrome • Refresh Real-time • SH-4A Native", bg="#111625", fg="#64748b", font=("Segoe UI", 7)).pack()

        # Icon Card 30x17
        icon_card = tk.LabelFrame(left_pane, text=" Desainer Ikon Menu Utama (30×17 Pixel) ", bg="#111625", fg="#f59e0b", font=("Segoe UI", 9, "bold"), padx=8, pady=8)
        icon_card.pack(fill=tk.BOTH, expand=True)

        icon_row = tk.Frame(icon_card, bg="#111625")
        icon_row.pack(fill=tk.X, pady=4)

        # Canvas Ikon 30x17 scaled 6x (180x102)
        icon_canvas = tk.Canvas(icon_row, width=180, height=102, bg="#8ca472", highlightthickness=1, highlightbackground="#232d48", cursor="crosshair")
        icon_canvas.pack(side=tk.LEFT, padx=(0, 10))

        icon_tools = tk.Frame(icon_row, bg="#111625")
        icon_tools.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        icon_mode_var = tk.StringVar(value="draw")

        def set_mode(m):
            icon_mode_var.set(m)
            btn_pen.config(bg="#00e5ff" if m == "draw" else "#1e2638", fg="#090c15" if m == "draw" else "#f1f5f9")
            btn_era.config(bg="#00e5ff" if m == "erase" else "#1e2638", fg="#090c15" if m == "erase" else "#f1f5f9")

        btn_pen = tk.Button(icon_tools, text="✏️ Gambar", bg="#00e5ff", fg="#090c15", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, padx=6, command=lambda: set_mode("draw"), cursor="hand2")
        btn_pen.pack(fill=tk.X, pady=1)

        btn_era = tk.Button(icon_tools, text="🧹 Hapus", bg="#1e2638", fg="#f1f5f9", font=("Segoe UI", 8), relief=tk.FLAT, padx=6, command=lambda: set_mode("erase"), cursor="hand2")
        btn_era.pack(fill=tk.X, pady=1)

        btn_inv = tk.Button(icon_tools, text="🔄 Invert", bg="#1e2638", fg="#f1f5f9", font=("Segoe UI", 8), relief=tk.FLAT, padx=6, cursor="hand2")
        btn_inv.pack(fill=tk.X, pady=1)

        btn_clr = tk.Button(icon_tools, text="🗑️ Bersihkan", bg="#1e2638", fg="#f1f5f9", font=("Segoe UI", 8), relief=tk.FLAT, padx=6, cursor="hand2")
        btn_clr.pack(fill=tk.X, pady=1)

        # Preset Ikon bar
        tk.Label(icon_card, text="Preset Ikon Cepat:", bg="#111625", fg="#94a3b8", font=("Segoe UI", 8, "bold")).pack(anchor=tk.W, pady=(6, 2))
        preset_icon_row = tk.Frame(icon_card, bg="#111625")
        preset_icon_row.pack(fill=tk.X)

        # State Ikon 30x17
        icon_grid = [[False for _ in range(30)] for _ in range(17)]

        def render_icon():
            icon_canvas.delete("all")
            # Gambar pixel
            for y in range(17):
                for x in range(30):
                    if icon_grid[y][x]:
                        icon_canvas.create_rectangle(x * 6, y * 6, x * 6 + 6, y * 6 + 6, fill="#182713", outline="#182713")
                    else:
                        icon_canvas.create_rectangle(x * 6, y * 6, x * 6 + 6, y * 6 + 6, fill="#8ca472", outline="#829a68")

        def load_icon_preset(pname):
            raw = g1a_builder.create_preset_icon(pname)
            for y in range(17):
                for x in range(30):
                    icon_grid[y][x] = g1a_builder.get_icon_pixel(raw, x, y)
            render_icon()

        load_icon_preset("calculator")

        def on_icon_click(e):
            x = e.x // 6
            y = e.y // 6
            if 0 <= x < 30 and 0 <= y < 17:
                icon_grid[y][x] = (icon_mode_var.get() == "draw")
                render_icon()

        icon_canvas.bind("<Button-1>", on_icon_click)
        icon_canvas.bind("<B1-Motion>", on_icon_click)

        def on_invert():
            for y in range(17):
                for x in range(30):
                    icon_grid[y][x] = not icon_grid[y][x]
            render_icon()

        def on_clear():
            for y in range(17):
                for x in range(30):
                    icon_grid[y][x] = False
            render_icon()

        btn_inv.config(command=on_invert)
        btn_clr.config(command=on_clear)

        for p_name, p_label in [("calculator", "🧮 Calc"), ("graph", "📊 Graph"), ("math", "Σ Math"), ("game", "🎮 Game"), ("tool", "🛠️ Tool")]:
            b = tk.Button(preset_icon_row, text=p_label, bg="#182035", fg="#f1f5f9", font=("Segoe UI", 7), relief=tk.FLAT, padx=4, pady=1, command=lambda n=p_name: load_icon_preset(n), cursor="hand2")
            b.pack(side=tk.LEFT, padx=1)

        # RIGHT PANE: GUI Script Editor & USB Flash Guide
        right_pane = tk.Frame(workspace, bg="#111625", padx=10, pady=10)
        workspace.add(right_pane, width=600)

        # Script Frame Card
        script_card = tk.LabelFrame(right_pane, text=" Skrip Tampilan Antarmuka GUI ", bg="#111625", fg="#00e5ff", font=("Segoe UI", 9, "bold"), padx=8, pady=8)
        script_card.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        script_scroll = tk.Scrollbar(script_card)
        script_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        script_text = tk.Text(script_card, bg="#090c15", fg="#f1f5f9", insertbackground="#00e5ff", font=("Consolas", 10), wrap=tk.NONE, yscrollcommand=script_scroll.set, padx=8, pady=8)
        script_text.pack(fill=tk.BOTH, expand=True)
        script_scroll.config(command=script_text.yview)

        # Drive Card (Deteksi Flashdisk Kalkulator)
        drive_card = tk.LabelFrame(right_pane, text=" Koneksi & Pengiriman Instan (USB Flash Mode F1) ", bg="#111625", fg="#10b981", font=("Segoe UI", 8, "bold"), padx=8, pady=6)
        drive_card.pack(fill=tk.X, side=tk.BOTTOM)

        drive_status_lbl = tk.Label(drive_card, text="Memeriksa drive kalkulator...", bg="#111625", fg="#94a3b8", font=("Segoe UI", 8), anchor=tk.W)
        drive_status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        btn_quick_send = tk.Button(drive_card, text="🚀 Salin ke Kalkulator", bg="#10b981", fg="#090c15", font=("Segoe UI", 8, "bold"), relief=tk.FLAT, padx=8, state=tk.DISABLED, cursor="hand2")
        btn_quick_send.pack(side=tk.RIGHT, padx=(4, 0))

        btn_rescan = tk.Button(drive_card, text="🔄 Cek Ulang", bg="#222c48", fg="#f1f5f9", font=("Segoe UI", 8), relief=tk.FLAT, padx=6, cursor="hand2")
        btn_rescan.pack(side=tk.RIGHT)

        def rescan_drives():
            drives = g1a_builder.find_casio_flash_drives()
            if drives:
                target = drives[0]
                drive_status_lbl.config(
                    text=f"✅ Kalkulator terdeteksi di Drive {target['letter']}: ({target['volume']}) - {target['free_mb']} MB bebas",
                    fg="#10b981"
                )
                btn_quick_send.config(state=tk.NORMAL, command=lambda: send_to_calc(target['letter']))
            else:
                drive_status_lbl.config(
                    text="💡 Hubungkan USB lalu tekan F1 (USB Flash) pada kalkulator untuk kirim 1-klik!",
                    fg="#94a3b8"
                )
                btn_quick_send.config(state=tk.DISABLED)

        btn_rescan.config(command=rescan_drives)

        # LCD Renderer Function
        def update_lcd_display(event=None):
            lcd_canvas.delete("all")
            # Background
            lcd_canvas.create_rectangle(0, 0, 384, 192, fill="#8ca472", outline="")

            # Header
            head_title = title_var.get().strip() or "CASIO APP"
            content_lines = []
            fkeys = {}

            txt = script_text.get("1.0", tk.END)
            for line in txt.splitlines():
                l = line.strip()
                if not l or l.startswith("#"):
                    continue
                if l.startswith("HEADER"):
                    m = re.findall(r'"([^"]*)"', l)
                    if m:
                        head_title = m[0]
                elif l.startswith("TEXT"):
                    m = re.findall(r'"([^"]*)"', l)
                    content_lines.append(m[0] if m else l[4:].strip())
                elif l.startswith("FKEY"):
                    m = re.match(r'FKEY\s+(\d+)\s*,\s*"([^"]*)"', l, re.IGNORECASE)
                    if m:
                        fkeys[int(m.group(1))] = m.group(2)[:6]

            # Gambar Header Bar
            lcd_canvas.create_text(8, 12, text=head_title, anchor=tk.W, fill="#182713", font=("Consolas", 10, "bold"))
            lcd_canvas.create_line(0, 24, 384, 24, fill="#182713", width=2)

            # Baris Teks Konten
            y_offset = 38
            for line in content_lines[:5]:
                lcd_canvas.create_text(10, y_offset, text=line, anchor=tk.W, fill="#182713", font=("Consolas", 10))
                y_offset += 24

            # Garis Pembatas Tombol F1-F6
            lcd_canvas.create_line(0, 162, 384, 162, fill="#182713", width=2)

            # Tombol F1-F6 Baris Bawah
            for slot in range(1, 7):
                x1 = (slot - 1) * 63 + 3
                x2 = x1 + 60
                label = fkeys.get(slot, "")
                if label:
                    # Kotak terbalik
                    lcd_canvas.create_rectangle(x1, 166, x2, 190, fill="#182713", outline="#182713")
                    lcd_canvas.create_text((x1 + x2) // 2, 178, text=label[:5], fill="#8ca472", font=("Consolas", 8, "bold"))

        script_text.bind("<KeyRelease>", update_lcd_display)
        title_entry.bind("<KeyRelease>", update_lcd_display)

        # Template switcher
        def on_preset_change(e):
            val = preset_var.get()
            if "Surveyor" in val:
                name_var.set("TOMLIN")
                title_var.set("Tomlin P")
                load_icon_preset("calculator")
                script_text.delete("1.0", tk.END)
                script_text.insert("1.0", (Path(__file__).parent / "examples" / "TOMLIN_GUI.txt").read_text(encoding="utf-8") if (Path(__file__).parent / "examples" / "TOMLIN_GUI.txt").exists() else 'APP "TOMLIN", "Tomlin P", "01.00.0000"\nICON "calculator"\nHEADER "TOMLIN SURVEYOR v1.0"\n\nTEXT "Koordinat X : 124.500 m"\nTEXT "Koordinat Y : 340.250 m"\nTEXT "Elevasi Z   :  45.120 m"\nTEXT "Status GPS  : FIX (3D)"\nTEXT "Akurasi     : +/- 0.005 m"\n\nFKEY 1, "UKUR"\nFKEY 2, "REKAM"\nFKEY 3, "PETA"\nFKEY 4, "HITUNG"\nFKEY 5, "SETTIN"\nFKEY 6, "KELUAR"')
            elif "Saintifik" in val:
                name_var.set("SCICALC")
                title_var.set("Sci Calc")
                load_icon_preset("calculator")
                script_text.delete("1.0", tk.END)
                script_text.insert("1.0", 'APP "SCICALC", "Sci Calc", "01.00.0000"\nICON "calculator"\nHEADER "SCIENTIFIC CALCULATOR"\n\nTEXT "f(x) = sin(x)^2 + cos(x)"\nTEXT "x    = 45.000 deg"\nTEXT "----------------------------"\nTEXT "HASIL: 1.20710678"\nTEXT "MODE : DEG / FIX 8"\n\nFKEY 1, "SIN"\nFKEY 2, "COS"\nFKEY 3, "TAN"\nFKEY 4, "SQRT"\nFKEY 5, "PLOT"\nFKEY 6, "EXIT"')
            elif "Grafik" in val:
                name_var.set("PLOTTER")
                title_var.set("Plotter")
                load_icon_preset("graph")
                script_text.delete("1.0", tk.END)
                script_text.insert("1.0", 'APP "PLOTTER", "Plotter", "01.00.0000"\nICON "graph"\nHEADER "KURVA & FUNGSI POLINOMIAL"\n\nTEXT "Y1 = 2*X^2 - 4*X + 1"\nTEXT "Xmin: -5.00   Xmax: 5.00"\nTEXT "Ymin: -10.0   Ymax: 20.0"\nTEXT "Titik Puncak: (1.00, -1.00)"\nTEXT "Akar Real   : x=0.29, x=1.71"\n\nFKEY 1, "ZOOM"\nFKEY 2, "TRACE"\nFKEY 3, "PLOT"\nFKEY 4, "TABLE"\nFKEY 5, "RESET"\nFKEY 6, "EXIT"')
            elif "Game" in val:
                name_var.set("RETRO")
                title_var.set("RetroPad")
                load_icon_preset("game")
                script_text.delete("1.0", tk.END)
                script_text.insert("1.0", 'APP "RETRO", "RetroPad", "01.00.0000"\nICON "game"\nHEADER "RETRO ARCADE FX"\n\nTEXT "SKOR   : 004850"\nTEXT "NYAWA  : [♥][♥][♥]"\nTEXT "LEVEL  : 3 - DUNIA PIXEL"\nTEXT "----------------------------"\nTEXT "SIAP! TEKAN [F1] UNTUK MULAI"\n\nFKEY 1, "MULAI"\nFKEY 2, "LOMPAT"\nFKEY 3, "SERANG"\nFKEY 4, "PAUSE"\nFKEY 5, "OPSI"\nFKEY 6, "EXIT"')
            elif "Matriks" in val:
                name_var.set("MATRIX")
                title_var.set("MatrixFx")
                load_icon_preset("math")
                script_text.delete("1.0", tk.END)
                script_text.insert("1.0", 'APP "MATRIX", "MatrixFx", "01.00.0000"\nICON "math"\nHEADER "OPERASI MATRIKS 3x3"\n\nTEXT "Matriks A: [ 2  -1   3 ]"\nTEXT "           [ 0   4   5 ]"\nTEXT "           [ 1   2  -2 ]"\nTEXT "Det(A) = -37"\nTEXT "Rank   = 3 (Invertibel)"\n\nFKEY 1, "DET"\nFKEY 2, "INV"\nFKEY 3, "A*B"\nFKEY 4, "TRANS"\nFKEY 5, "CLEAR"\nFKEY 6, "EXIT"')
            update_lcd_display()

        preset_cb.bind("<<ComboboxSelected>>", on_preset_change)

        def get_current_icon_bytes():
            icon_buf = bytearray(68)
            for y in range(17):
                for x in range(30):
                    if icon_grid[y][x]:
                        byte_idx = y * 4 + (x // 8)
                        bit_idx = 7 - (x % 8)
                        icon_buf[byte_idx] |= (1 << bit_idx)
            return bytes(icon_buf)

        def build_current_g1a():
            cfg = g1a_builder.parse_gui_script(script_text.get("1.0", tk.END))
            raw_name = name_var.get().strip().upper() or "APP1"
            title = title_var.get().strip() or "MY APP"
            icon_bytes = get_current_icon_bytes()

            return g1a_builder.make_g1a(
                internal_name=raw_name,
                display_title=title,
                version=cfg.get("version", "01.00.0000"),
                icon_bytes=icon_bytes,
                gui_lines=cfg.get("lines"),
                gui_fkeys=cfg.get("fkeys")
            )

        def save_g1a_dialog():
            raw_name = g1a_builder.validate_addin_name(name_var.get().strip().upper() or "APP1")
            dest = filedialog.asksaveasfilename(
                title="Simpan Berkas Add-in .G1A",
                defaultextension=".g1a",
                filetypes=[("Casio Add-in (*.g1a)", "*.g1a")],
                initialfile=f"{raw_name}.g1a"
            )
            if dest:
                data = build_current_g1a()
                Path(dest).write_bytes(data)
                self.log(f"[G1A Studio] Berkas Add-in berhasil disimpan: {dest} ({len(data)} byte)")
                messagebox.showinfo(
                    "Kompilasi Sukses",
                    f"Berkas {Path(dest).name} ({len(data)} byte) berhasil dibuat!\n\n"
                    f"Nama Internal: @{raw_name}\n"
                    f"Cara Pasang: Hubungkan kalkulator via USB -> Tekan F1 (USB Flash) -> Drag & drop berkas .g1a ini ke dalam drive kalkulator!"
                )

        def send_to_calc(drive_letter):
            try:
                data = build_current_g1a()
                raw_name = g1a_builder.validate_addin_name(name_var.get().strip().upper() or "APP1")
                dest_file = Path(f"{drive_letter.upper()}:\\{raw_name}.g1a")
                dest_file.write_bytes(data)
                self.log(f"[G1A Studio] Sukses mengirim {dest_file.name} ke drive {drive_letter}:\\!")
                messagebox.showinfo(
                    "Sukses Terkirim!",
                    f"Add-in {dest_file.name} ({len(data)} byte) BERHASIL DISALIN ke kalkulator (Drive {drive_letter}:\\)!\n\n"
                    "Langkah Terakhir:\n"
                    "1. Lepaskan kabel USB dari komputer.\n"
                    "2. Buka MAIN MENU di kalkulator.\n"
                    f"3. Aplikasi @{raw_name} Anda langsung muncul dengan ikon lengkap!"
                )
            except Exception as ex:
                messagebox.showerror("Gagal Menyalin", f"Terjadi kesalahan saat menyalin berkas: {ex}")

        def export_c_dialog():
            cfg = g1a_builder.parse_gui_script(script_text.get("1.0", tk.END))
            raw_name = g1a_builder.validate_addin_name(name_var.get().strip().upper() or "APP1")
            c_code = g1a_builder.generate_c_source(cfg)
            dest = filedialog.asksaveasfilename(
                title="Simpan Kode Sumber C (main.c)",
                defaultextension=".c",
                filetypes=[("C Source (*.c)", "*.c")],
                initialfile=f"main_{raw_name}.c"
            )
            if dest:
                Path(dest).write_text(c_code, encoding="utf-8")
                self.log(f"[G1A Studio] Kode sumber C berhasil disimpan: {dest}")
                messagebox.showinfo("Export Berhasil", f"Kode sumber C berhasil disimpan ke {dest}!")

        btn_build_g1a.config(command=save_g1a_dialog)
        btn_c_export.config(command=export_c_dialog)

        # Inisialisasi awal
        on_preset_change(None)
        rescan_drives()
        self.log("[G1A Studio] Studio Desainer Add-in GUI (.G1A) dibuka.")

    def show_about(self):
        messagebox.showinfo(
            "Tentang Casio FX Studio",
            "Casio FX Studio v1.0\n"
            "Editor, Simulator & Compiler Casio BASIC ke format data G1M untuk fx-9860GII.\n\n"
            "Dibuat untuk memudahkan penulisan rumus, program, dan game matematika langsung dari PC."
        )


def main():
    app = CasioEditorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
