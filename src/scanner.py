# -*- coding: utf-8 -*-
"""
Apple-Grade Premium Kiberpank HUD, Face ID 3D Skaner va Shaxriyor Raqamli Nomi
(Cupertino Rounded Badges & Apple Face ID Matrix)
"""

import math
import time

C_RESET = "\033[0m"

def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

def strip_ansi(s):
    return ANSI_RE.sub("", s)

def visible_len(s):
    return len(strip_ansi(s))

def center_ansi(s, width):
    v = visible_len(s)
    if v >= width:
        return s
    pad = (width - v) // 2
    return " " * pad + s

class CyberScannerHUD:
    def __init__(self, memory):
        self.memory = memory
        self.laser_active = True
        self.scan_progress = 0.0
        self.state = "FACE_ID_SCAN"
        self.state_time = 0.0
        self.laser_y_norm = 0.0
        
        # Xavfsizlik va tanish holati
        self.is_match = True
        self.similarity_score = 99.8
        self.just_completed = False

    def trigger_scan(self):
        self.laser_active = True
        self.scan_progress = 0.0
        self.state = "FACE_ID_SCAN"
        self.state_time = 0.0
        self.just_completed = False

    def update(self, dt, current_time, camera=None):
        self.state_time += dt

        if self.state in ("FACE_ID_SCAN", "SCANNING"):
            self.scan_progress += dt / 2.5
            self.laser_y_norm = math.sin(self.scan_progress * math.pi * 3.0)

            if self.scan_progress >= 1.0:
                self.scan_progress = 1.0
                self.laser_active = False
                self.just_completed = True
                
                # Kamera orqali haqiqiy solishtirish
                if camera and camera.has_camera:
                    score, is_rec = camera.compare_with_reference()
                    self.similarity_score = max(55.0, score * 100.0)
                    self.is_match = is_rec
                    self.state = "RECOGNIZED" if is_rec else "UNKNOWN_ALERT"
                else:
                    self.is_match = True
                    self.similarity_score = 99.8
                    self.state = "RECOGNIZED"

    def is_laser_on_row(self, y, cy, h_eye):
        if not self.laser_active:
            return False
        laser_screen_y = cy + self.laser_y_norm * (h_eye * 0.95)
        return abs(y - laser_screen_y) < 1.0

    def render_overlay(self, lines, cols, rows, current_time, camera=None, eye=None):
        """Terminal o'lchamiga to'liq moslashuvchi (Responsive) Apple Face ID panellari."""
        c_cyan = (0, 245, 255)
        c_blue = (50, 150, 255)
        c_white = (255, 255, 255)
        c_green = (40, 255, 120)
        c_amber = (255, 170, 40)
        c_red = (255, 60, 60)
        c_border = (255, 45, 55) if (eye and eye.is_sharingan) else (0, 190, 215)

        # ---------------------------------------------------------------------
        # 1. YUQORI RESPONSIVE APPLE FACE ID STATUS BAR
        # ---------------------------------------------------------------------
        if rows >= 14:
            cam_active = camera and camera.has_camera and camera.enabled
            if cam_active:
                if camera.person_detected:
                    cam_tag = f"{rgb(*c_green)}● LOCKED{rgb(*c_border)}" if cols < 95 else f"{rgb(*c_green)}● FACE_ID: SUBJECT LOCKED{rgb(*c_border)}"
                else:
                    cam_tag = f"{rgb(*c_amber)}○ SEARCHING{rgb(*c_border)}" if cols < 95 else f"{rgb(*c_amber)}○ FACE_ID: LOOK AT CAMERA{rgb(*c_border)}"
            else:
                cam_tag = "CAMERA: OFF" if cols < 85 else "FACE_ID: ACTIVE"

            # Rejimga qarab moslashuvchan matn
            if eye and eye.is_sharingan:
                chakra_tag = f"{rgb(255, 30, 40)}◈ SHARINGAN [3-TOMOE]{rgb(*c_border)}" if cols < 95 else f"{rgb(255, 30, 40)}◈ UCHIHA SHARINGAN AWAKENED // 3-TOMOE ACTIVE{rgb(*c_border)}"
                top_text = f" {chakra_tag}  │  {cam_tag} "
            elif eye and eye.manual_squint:
                focus_tag = f"{rgb(255, 220, 0)}⚡ FOCUS{rgb(*c_border)}" if cols < 85 else f"{rgb(255, 220, 0)}⚡ ANIME HYPER-FOCUS ENGAGED{rgb(*c_border)}"
                top_text = f" {focus_tag}  │  {cam_tag} "
            elif self.state == "RECOGNIZED":
                if cols >= 90:
                    top_text = f" {rgb(*c_green)}[✓] FACE ID UNLOCKED: {self.memory.name.upper()}{rgb(*c_border)}  │  MATCH: {self.similarity_score:.1f}%  │  {cam_tag} "
                elif cols >= 65:
                    top_text = f" {rgb(*c_green)}[✓] {self.memory.name.upper()}{rgb(*c_border)}  │  {self.similarity_score:.0f}%  │  {cam_tag} "
                else:
                    top_text = f" {rgb(*c_green)}[✓] {self.memory.name.upper()}{rgb(*c_border)} "
            elif self.state == "UNKNOWN_ALERT":
                top_text = f" {rgb(*c_red)}[!] UNKNOWN SUBJECT{rgb(*c_border)}  │  {cam_tag} "
            else:
                pct = int(self.scan_progress * 100)
                if cols >= 80:
                    top_text = f" {rgb(*c_cyan)}◈ FACE ID 3D DEPTH SCAN: {pct}%{rgb(*c_border)}  │  {cam_tag} "
                else:
                    top_text = f" {rgb(*c_cyan)}◈ SCAN: {pct}%{rgb(*c_border)} "

            # Chegara chizig'i
            vis_len = visible_len(top_text)
            w_box = max(vis_len + 4, min(cols - 4, 110))
            side_dash = max(1, (w_box - vis_len - 4) // 2)

            top_border = f"{rgb(*c_border)}╭{'─' * side_dash}{top_text}{rgb(*c_border)}{'─' * side_dash}╮{C_RESET}"
            lines[0] = center_ansi(top_border, cols)

        # ---------------------------------------------------------------------
        # 2. XATOLIK / OGOHLANTIRISH
        # ---------------------------------------------------------------------
        if self.state == "UNKNOWN_ALERT":
            warn_col = rgb(*c_red)
            txt_col = rgb(*c_white)
            hint_col = rgb(*c_amber)

            if cols >= 80 and rows >= 24:
                msg1 = f" {warn_col}╭─ ⚠️ APPLE FACE ID: UNRECOGNIZED SUBJECT ──────────────────────────────╮{C_RESET} "
                msg2 = f" {warn_col}│{txt_col}  Yuz biometriyasi {self.memory.name} ga to'g'ri kelmadi. Yangi ism kiritasizmi?   {warn_col}│{C_RESET} "
                msg3 = f" {warn_col}│{hint_col}  [R] Yangi ism yozish   │   [L] Qayta Face ID   │   [F] Hyper-Focus        {warn_col}│{C_RESET} "
                msg4 = f" {warn_col}╰────────────────────────────────────────────────────────────────────────╯{C_RESET} "
                for off, m in enumerate([msg1, msg2, msg3, msg4]):
                    p = rows - 6 + off
                    if 0 <= p < rows:
                        lines[p] = center_ansi(m, cols)
            else:
                p = max(1, rows - 3)
                if p < rows:
                    lines[p] = center_ansi(f"{warn_col}[!] Unrecognized. Press [R] to register name.{C_RESET}", cols)

        elif self.state in ("FACE_ID_SCAN", "SCANNING"):
            pct = int(self.scan_progress * 100)
            bar_len = min(20, max(8, cols // 5))
            filled = int((pct / 100) * bar_len)
            bar = "━" * filled + "─" * (bar_len - filled)

            if cols >= 85:
                phase_txt = "DEPTH MESHING" if pct < 50 else "NEURAL AUTHENTICATING"
                scan_msg = f"  ◈ FACE ID 3D SCAN: {pct}%  [{bar}]  {phase_txt}  "
            else:
                scan_msg = f"  ◈ 3D SCAN: {pct}% [{bar}]  "

            pos = rows - 4 if rows >= 24 else rows - 2
            if 0 <= pos < rows:
                lines[pos] = center_ansi(f"{rgb(*c_cyan)}{scan_msg}{C_RESET}", cols)

        # ---------------------------------------------------------------------
        # 3. PASTKI RESPONSIVE TUGMALAR (Cupertino Controls Bar)
        # ---------------------------------------------------------------------
        if rows >= 18:
            b_col = rgb(*c_border)
            w_col = rgb(*c_white)
            k_col = rgb(*c_cyan)
            f_col = rgb(255, 220, 0) if (eye and eye.manual_squint) else k_col
            s_col = rgb(255, 30, 40) if (eye and eye.is_sharingan) else k_col

            if cols >= 92:
                # Katta ekranlar: To'liq kengaytirilgan tugmalar
                btn_row = (
                    f"{b_col}│{C_RESET}  {k_col}[␣ Space]{w_col} Blink  "
                    f"{f_col}[F]{w_col} Focus  "
                    f"{s_col}[S]{w_col} Sharingan  "
                    f"{k_col}[C]{w_col} Iris  "
                    f"{k_col}[K]{w_col} WebCam  "
                    f"{k_col}[I]{w_col} Invert  "
                    f"{k_col}[L]{w_col} Face ID  "
                    f"{k_col}[R]{w_col} New Name  "
                    f"{k_col}[Q]{w_col} Exit  {b_col}│{C_RESET}"
                )
                box_w = visible_len(btn_row)
                dashes = box_w - len("╭─ APPLE CONTROLS ─╮")
                top_c = f"{b_col}╭─ APPLE CONTROLS {'─' * max(0, dashes)}╮{C_RESET}"
                lines[-2] = center_ansi(top_c, cols)
                lines[-1] = center_ansi(btn_row, cols)

            elif cols >= 68:
                # O'rta ekranlar: Ixcham tugmalar
                btn_row = (
                    f"{b_col}│{C_RESET} {k_col}[␣]{w_col}Blink "
                    f"{f_col}[F]{w_col}Focus "
                    f"{s_col}[S]{w_col}Sharingan "
                    f"{k_col}[C]{w_col}Iris "
                    f"{k_col}[K]{w_col}Cam "
                    f"{k_col}[I]{w_col}Invert "
                    f"{k_col}[L]{w_col}Scan "
                    f"{k_col}[R]{w_col}Name "
                    f"{k_col}[Q]{w_col}Exit {b_col}│{C_RESET}"
                )
                box_w = visible_len(btn_row)
                dashes = box_w - len("╭─ CONTROLS ─╮")
                top_c = f"{b_col}╭─ CONTROLS {'─' * max(0, dashes)}╮{C_RESET}"
                lines[-2] = center_ansi(top_c, cols)
                lines[-1] = center_ansi(btn_row, cols)

            else:
                # Kichik ekranlar: Bir qatorli minimalist tugmalar
                mini_row = (
                    f"{k_col}[␣]{w_col}Blink "
                    f"{f_col}[F]{w_col}Focus "
                    f"{s_col}[S]{w_col}Sharingan "
                    f"{k_col}[C]{w_col}Iris "
                    f"{k_col}[K]{w_col}Cam "
                    f"{k_col}[L]{w_col}Scan "
                    f"{k_col}[Q]{w_col}Exit"
                )
                lines[-1] = center_ansi(mini_row, cols)

        return lines

