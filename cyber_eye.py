#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
                     CYBERNETIC BIOMETRIC EYE ENGINE
                (Kiberpank Biometrik Ko'z va Yuzni Tanish Tizimi)
===============================================================================
Operator: Shaxriyor
Apple Face ID 3D skanerlash, Anime Hyper-Focus va Haqiqiy WebCam AI Tracker.

Boshqaruv:
  [SPACE]           : Ko'zni silliq yumib-ochish (Blink)
  [F]               : Anime Hyper-Focus (Ovozsiz, o'ta o'tkir anime diqqat)
  [S]               : Uchiha Sharingan (3-Tomoe Ocular Jutsu & Binar Matrix)
  [C]               : Kamalak parda (Iris) rangini almashtirish
  [K]               : Veb-kamera AI kuzatuvini yoqish / o'chirish
  [I]               : Kamera yo'nalishini almashtirish (Invert Tracking)
  [L]               : Apple Face ID 3D skanerlash va surat olish
  [R]               : Ismni o'zgartirish yoki yangi operator kiritish (Register Name)
  [V]               : Ovozni yoqish / o'chirish (Voice Mute Toggle)
  [Q] / [ESC]       : Tizimdan chiqish
===============================================================================
"""

import sys
import os
import time

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Windows ANSI TrueColor initialization
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        hOut = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(hOut, ctypes.byref(mode))
        kernel32.SetConsoleMode(hOut, mode.value | 0x0004 | 0x0001)
    except Exception:
        pass

# Ensure module import path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.eye_engine import EyeEngine
from src.memory import BiometricMemory
from src.scanner import CyberScannerHUD
from src.voice import CyberVoice
from src.tracker import CameraTracker

C_HIDE = "\033[?25l"
C_SHOW = "\033[?25h"
C_HOME = "\033[H"
C_CLEAR = "\033[2J"
C_RESET = "\033[0m"
C_NOWRAP = "\033[?7l"
C_WRAP = "\033[?7h"


def check_key():
    """Tugmalarni non-blocking o'qish."""
    if sys.platform == "win32":
        try:
            import msvcrt
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in (b"\x00", b"\xe0"):
                    ch2 = msvcrt.getch()
                    if ch2 == b"K": return "left"
                    if ch2 == b"M": return "right"
                    if ch2 == b"H": return "up"
                    if ch2 == b"P": return "down"
                try:
                    return ch.decode("utf-8").lower()
                except Exception:
                    return ""
        except Exception:
            return None
    return None


def get_terminal_dims():
    try:
        size = os.get_terminal_size()
        cols, rows = size.columns, size.lines
    except Exception:
        cols, rows = 100, 36
    # Hech qanday sun'iy cheklovlarsiz: kichik derazadan to 4K to'liq ekrangacha
    cols = max(45, cols)
    rows = max(14, rows)
    return cols, rows


def prompt_register_name(memory, camera, voice):
    """Foydalanuvchi tanilmaganda yoki yangi ism kiritmoqchi bo'lganda interaktiv dialog."""
    sys.stdout.write(C_SHOW + C_CLEAR + C_HOME)
    sys.stdout.flush()

    print("\033[38;2;0;255;255m")
    print(" ╭────────────────────────────────────────────────────────────────────────╮")
    print(" │  APPLE FACE ID // BIOMETRIC IDENTITY ENROLLMENT                       │")
    print(" ╰────────────────────────────────────────────────────────────────────────╯")
    print("\033[0m")
    print(f" Hozirgi qayd etilgan operator: \033[38;2;255;255;255m{memory.name}\033[0m")
    print(" Yangi ismni kiriting (yoki davom ettirish uchun to'g'ridan-to'g'ri ENTER bosing):")
    
    try:
        new_name = input("\033[38;2;0;255;255m > \033[0m").strip()
    except Exception:
        new_name = ""

    if not new_name:
        new_name = memory.name

    # Yangi rasm va xesh olish
    photo_path, dna_hash = camera.capture_biometric_photo()
    memory.register_new_operator(new_name, dna_hash=dna_hash)

    print(f"\n \033[38;2;50;255;120m[✓] Face ID muvaffaqiyatli saqlandi: {new_name}\033[0m")
    print(f" [✓] Retinal 3D xesh: {dna_hash}")
    voice.speak(f"Biometric profile enrolled. Welcome, {new_name}.")
    time.sleep(1.2)

    sys.stdout.write(C_HIDE + C_CLEAR)
    sys.stdout.flush()


def main():
    # 1. Modullarni ishga tushirish
    memory = BiometricMemory(default_name="Boss")
    scanner = CyberScannerHUD(memory)
    eye = EyeEngine()
    voice = CyberVoice(enabled=True)
    camera = CameraTracker(camera_index=0, enabled=True)

    # Boshlanishida: biometrik tahlil boshlangani haqida sokin xabar berish
    voice.speak("Initiating biometric depth scan.")

    # Kursor yashirish, avto-wrapni o'chirish va terminal tozalash
    sys.stdout.write(C_HIDE + C_NOWRAP + C_CLEAR)
    sys.stdout.flush()

    start_time = time.perf_counter()
    last_frame_time = start_time
    target_fps = 30.0
    frame_interval = 1.0 / target_fps
    last_warn_voice = 0.0
    prev_cols, prev_rows = 0, 0

    try:
        while True:
            t0 = time.perf_counter()
            dt = t0 - last_frame_time
            last_frame_time = t0
            current_time = t0 - start_time

            # Tugmalarni tekshirish
            key = check_key()
            if key:
                if key == "q" or key == "\x1b":  # 'q' yoki ESC
                    break
                elif key == " ":  # Space: Ko'zni silliq yumib-ochish (Blink)
                    eye.trigger_blink()
                elif key == "f":  # F: ANIME HYPER-FOCUS (OVOZSIZ - SOF VIZUAL FOKUS)
                    eye.toggle_squint()
                elif key == "s":  # S: UCHIHA SHARINGAN (3-TOMOE OCULAR JUTSU)
                    active = eye.toggle_sharingan()
                    if active:
                        voice.speak("Sharingan awakened. Three Tomoe ocular jutsu engaged.")
                    else:
                        voice.speak("Sharingan deactivated.")
                elif key == "c":  # C: Iris rangini almashtirish
                    eye.next_theme()
                elif key == "k":  # K: Veb-kamera AI yoqish/o'chirish
                    is_on = camera.toggle()
                    if not is_on:
                        eye.auto_gaze = True
                elif key == "i":  # I: Yo'nalishni almashtirish (Invert Tracking)
                    camera.toggle_invert_x()
                elif key == "l":  # L: Apple Face ID 3D Skanerlash
                    scanner.trigger_scan()
                    _, new_hash = camera.capture_biometric_photo()
                    if new_hash:
                        memory.profile["retinal_dna_hash"] = new_hash
                        memory.save()
                    voice.speak("Re-scanning biometric depth profile. Look directly at the sensor.")
                elif key == "r":  # R: Yangi ism kiritish / qayta ro'yxatga olish
                    prompt_register_name(memory, camera, voice)
                    scanner.state = "RECOGNIZED"
                    scanner.is_match = True
                elif key == "v":  # V: Ovozni yoqish/o'chirish
                    voice.toggle_mute()
                elif key == "a":  # A: Avto-nigoh
                    eye.auto_gaze = not eye.auto_gaze
                # Strelkalar orqali qorachiqni boshqarish
                elif key == "left":
                    eye.auto_gaze = False
                    eye.target_gaze_x = max(-16.0, eye.target_gaze_x - 3.0)
                elif key == "right":
                    eye.auto_gaze = False
                    eye.target_gaze_x = min(16.0, eye.target_gaze_x + 3.0)
                elif key == "up":
                    eye.auto_gaze = False
                    eye.target_gaze_y = max(-3.0, eye.target_gaze_y - 1.2)
                elif key == "down":
                    eye.auto_gaze = False
                    eye.target_gaze_y = min(3.0, eye.target_gaze_y + 1.2)

            # 2. VEB-KAMERA AI KUZATUVI (Keng diapazonli kuchli kuzatuv)
            if camera.enabled and camera.has_camera:
                if camera.person_detected:
                    eye.auto_gaze = False
                    eye.target_gaze_x = camera.target_gaze_x
                    eye.target_gaze_y = camera.target_gaze_y
                else:
                    eye.auto_gaze = True

            # 3. Fizika va Skanerni yangilash
            eye.update(dt, current_time)
            scanner.update(dt, current_time, camera=camera)

            # 3.1. Skanerlash va yuzni analiz qilish yakunlanganda tabiiy va toza ovoz
            if scanner.just_completed:
                scanner.just_completed = False
                if scanner.state == "RECOGNIZED":
                    voice.speak(f"Biometric match confirmed. Welcome back, {memory.name}. Access granted.")
                else:
                    voice.speak("Biometric mismatch detected. Subject unknown. Press R to register.")

            # Agar noma'lum odam aniqlansa, vaqti-vaqti bilan ogohlantirish
            if scanner.state == "UNKNOWN_ALERT" and (current_time - last_warn_voice > 12.0):
                voice.speak("Identity required. Please press R to register your name.")
                last_warn_voice = current_time

            # 4. Terminal o'lchamlari va render
            cols, rows = get_terminal_dims()

            # Agar terminal o'lchami o'zgartirilsa, ekranni darhol tozalash (Resize handling)
            if cols != prev_cols or rows != prev_rows:
                sys.stdout.write(C_CLEAR)
                prev_cols, prev_rows = cols, rows

            # Ko'zni chizish
            frame_lines = eye.render_base_frame(cols, rows, current_time, scanner=scanner)

            # Apple Face ID UI, nom va tugmalarni chizish
            final_lines = scanner.render_overlay(frame_lines, cols, rows, current_time, camera=camera, eye=eye)

            # Qatorlar soni terminal qatorlaridan oshib ketmasligini kafolatlash (Zero Scroll)
            # Har bir qator oxiridagi bo'shliqlarni tozalash (o'ng tomondan wrap bo'lmasligi uchun)
            clean_lines = [l.rstrip() for l in final_lines[:rows]]
            if len(clean_lines) < rows:
                clean_lines.extend([""] * (rows - len(clean_lines)))

            # Ekranga bir zumda chizish (hech qanday miltillash va siljishsiz)
            sys.stdout.write(C_HOME + "\n".join(clean_lines))
            sys.stdout.flush()

            # FPS boshqaruvi
            t_render = time.perf_counter() - t0
            sleep_time = frame_interval - t_render
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    except Exception:
        pass
    finally:
        camera.stop()
        voice.stop()
        sys.stdout.write(C_SHOW + C_WRAP + C_RESET + "\n")
        sys.stdout.flush()
        sys.exit(0)


if __name__ == "__main__":
    main()
