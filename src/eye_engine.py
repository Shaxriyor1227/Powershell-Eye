# -*- coding: utf-8 -*-
"""
Haqiqiy Inson Ko'zi Anatomiyasi, Binar Kiber-Iris (0 va 1) va 3D Nigoh Dvigateli
(Foydalanuvchi talabiga ko'ra: atrofidagi barcha fon artefaktlari to'liq yo'qotilgan,
kamalak pardaga esa 0 va 1 binar oqimi mukammal integratsiya qilingan)
"""

import math
import random

C_RESET = "\033[0m"

# Bayer 4x4 Matritsasi (Sclera va relyef uchun)
BAYER_4X4 = [
    [ 0,  8,  2, 10],
    [12,  4, 14,  6],
    [ 3, 11,  1,  9],
    [15,  7, 13,  5]
]

# Sclera uchun toza zichlik belgilari
CHARS = [' ', '.', ':', '-', '+', '*', '%', '#', '@']

# Haqiqiy inson ko'zi rang palitralari
REAL_EYE_THEMES = [
    {
        "name": "Fotorealistik Monoxrom (Rasmdagidek)",
        "iris_core": (210, 225, 240),
        "iris_mid": (150, 165, 180),
        "iris_deep": (85, 98, 112),
        "iris_limbal": (35, 42, 50),
        "pupil": (4, 5, 7),
        "glint": (255, 255, 255),
        "sclera": (220, 226, 232),
        "skin": (110, 120, 132),
    },
    {
        "name": "Tabiiy Jigarrang (Natural Hazel Brown)",
        "iris_core": (245, 180, 90),
        "iris_mid": (185, 120, 48),
        "iris_deep": (120, 65, 24),
        "iris_limbal": (45, 22, 10),
        "pupil": (6, 5, 4),
        "glint": (255, 250, 240),
        "sclera": (235, 232, 228),
        "skin": (135, 105, 88),
    },
    {
        "name": "Moviy Ko'k (Ocean Sapphire)",
        "iris_core": (110, 215, 255),
        "iris_mid": (40, 150, 240),
        "iris_deep": (18, 85, 165),
        "iris_limbal": (10, 35, 75),
        "pupil": (4, 7, 11),
        "glint": (255, 255, 255),
        "sclera": (228, 234, 242),
        "skin": (115, 122, 135),
    },
    {
        "name": "Zumrad Yashil (Natural Emerald)",
        "iris_core": (155, 240, 130),
        "iris_mid": (75, 185, 88),
        "iris_deep": (30, 115, 52),
        "iris_limbal": (12, 45, 22),
        "pupil": (5, 8, 5),
        "glint": (255, 255, 255),
        "sclera": (230, 235, 230),
        "skin": (118, 125, 118),
    },
    {
        "name": "Kiber Firuza (Cyber Cyan)",
        "iris_core": (85, 255, 255),
        "iris_mid": (0, 205, 240),
        "iris_deep": (0, 125, 170),
        "iris_limbal": (0, 45, 70),
        "pupil": (3, 9, 12),
        "glint": (255, 255, 255),
        "sclera": (220, 235, 245),
        "skin": (95, 120, 135),
    },
]

def lerp_c(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )

def rgb(c):
    return f"\033[38;2;{c[0]};{c[1]};{c[2]}m"


class EyeEngine:
    def __init__(self):
        self.theme_idx = 0
        self.auto_gaze = True
        
        # Sakkadik va silliq nigoh koordinatalari
        self.gaze_x = 0.0
        self.gaze_y = 0.0
        self.target_gaze_x = 0.0
        self.target_gaze_y = 0.0
        self.next_saccade = 1.5
        self.gaze_step = 0
        
        # Fokus va diqqat (Anime Focus / Squint)
        self.squint_state = 0.0
        self.manual_squint = False
        
        # Uchiha Sharingan (3-Tomoe Ocular Jutsu)
        self.is_sharingan = False
        self.sharingan_angle = 0.0
        self.sharingan_spin_speed = 1.15
        self.sharingan_spin_boost = 0.0
        
        # Tabiiy pirpirash (Blinking)
        self.blink_state = 0.0
        self.manual_blink = 0.0
        self.blink_interval = 4.2
        self.blink_duration = 0.22

    def trigger_blink(self):
        self.manual_blink = 0.24

    def next_theme(self):
        self.theme_idx = (self.theme_idx + 1) % len(REAL_EYE_THEMES)

    def toggle_squint(self):
        self.manual_squint = not self.manual_squint
        return self.manual_squint

    def toggle_sharingan(self):
        self.is_sharingan = not self.is_sharingan
        if self.is_sharingan:
            # Yangi uyg'onganda tezkor aylanish (Awakening chakra spin burst)
            self.sharingan_spin_boost = 7.5
        return self.is_sharingan

    def update(self, dt, current_time):
        # 0. Sharingan aylanish dinamikasi (Chakra Spin)
        if self.is_sharingan:
            if self.sharingan_spin_boost > 0.0:
                self.sharingan_spin_boost = max(0.0, self.sharingan_spin_boost - dt * 4.2)
            eff_speed = self.sharingan_spin_speed + self.sharingan_spin_boost
            if self.manual_squint:
                eff_speed *= 1.7
            self.sharingan_angle += dt * eff_speed

        # 1. Tabiiy ko'z nigohi (Saccades & Fixations)
        if self.auto_gaze:
            if current_time >= self.next_saccade:
                self.gaze_step += 1
                cycle = self.gaze_step % 5
                if cycle == 0:
                    self.target_gaze_x = 0.0
                    self.target_gaze_y = 0.0
                    pause = random.uniform(2.5, 3.8)
                elif cycle == 1:
                    self.target_gaze_x = random.uniform(-9.0, -13.0)
                    self.target_gaze_y = random.uniform(-0.8, 0.4)
                    pause = random.uniform(1.2, 2.0)
                elif cycle == 2:
                    self.target_gaze_x = random.uniform(-1.0, 1.0)
                    self.target_gaze_y = random.uniform(-0.4, 0.4)
                    pause = random.uniform(2.0, 2.8)
                elif cycle == 3:
                    self.target_gaze_x = random.uniform(9.0, 13.0)
                    self.target_gaze_y = random.uniform(-0.6, 0.5)
                    pause = random.uniform(1.2, 2.0)
                else:
                    self.target_gaze_x = random.uniform(-3.0, 3.0)
                    self.target_gaze_y = random.uniform(-1.5, 1.2)
                    pause = random.uniform(1.2, 1.8)

                self.next_saccade = current_time + pause

        # Yumshoq amortizatsiyali kuzatuv
        smooth = min(1.0, dt * 9.0)
        self.gaze_x += (self.target_gaze_x - self.gaze_x) * smooth
        self.gaze_y += (self.target_gaze_y - self.gaze_y) * smooth

        # 2. Fokus / Squint fizikasi
        target_sq = 0.55 if self.manual_squint else 0.0
        self.squint_state += (target_sq - self.squint_state) * min(1.0, dt * 8.0)

        # 3. Ko'z qisish (Blink)
        if self.manual_blink > 0:
            self.manual_blink -= dt
            progress = 1.0 - (self.manual_blink / 0.24)
            if progress < 0.45:
                self.blink_state = math.sin((progress / 0.45) * (math.pi / 2.0))
            else:
                open_p = (progress - 0.45) / 0.55
                self.blink_state = 1.0 - math.sin(open_p * (math.pi / 2.0))
        else:
            t_mod = current_time % self.blink_interval
            b_dur = self.blink_duration
            if t_mod > (self.blink_interval - b_dur):
                t_b = (t_mod - (self.blink_interval - b_dur)) / b_dur
                if t_b < 0.42:
                    self.blink_state = math.sin((t_b / 0.42) * (math.pi / 2.0))
                elif t_b < 0.54:
                    self.blink_state = 1.0
                else:
                    open_t = (t_b - 0.54) / 0.46
                    self.blink_state = 1.0 - math.sin(open_t * (math.pi / 2.0))
            else:
                self.blink_state = 0.0

        self.blink_state = max(0.0, min(1.0, self.blink_state))

    def render_base_frame(self, cols, rows, current_time, scanner=None):
        pal = REAL_EYE_THEMES[self.theme_idx]

        cx = cols / 2.0
        cy = rows / 2.0
        aspect = 2.05  # Terminal belgilarining bo'y-en nisbati

        # 1. Ko'zning barqaror o'lchamlari (hech qanday miltillash yoki qotishsiz)
        avail_h = max(10.0, rows - 6.0)
        base_h = min(12.0, avail_h * 0.40)
        w_eye = min(44.0, cols * 0.38, base_h * 3.5)
        if self.is_sharingan:
            w_eye = min(48.0, cols * 0.42, base_h * 3.8)

        # Fokus va qisilish: qovoqlar tabiiy darajada yaqinlashadi
        squint_factor = 1.0 - self.squint_state * 0.52
        h_top_open = base_h * 1.14 * squint_factor
        h_bot_open = base_h * 0.88 * squint_factor

        lid_lag = self.gaze_y * 0.28
        h_top_open -= lid_lag
        b = self.blink_state

        # Iris va qorachiq o'lchamlari
        r_iris = base_h * aspect * (0.78 if self.is_sharingan else 0.72)
        if self.is_sharingan:
            hippus = 0.23 if self.manual_squint else 0.26
        else:
            hippus = 0.24 if self.manual_squint else (0.34 + 0.02 * math.sin(current_time * 1.8))
        r_pupil = r_iris * hippus

        # Qorachiq va irisning harakatlanuvchi markazi
        max_gx = max(4.0, w_eye * 0.30)
        max_gy = max(1.2, base_h * 0.20)
        clamped_gx = max(-max_gx, min(max_gx, self.gaze_x))
        clamped_gy = max(-max_gy, min(max_gy, self.gaze_y))

        iris_cx = cx + clamped_gx
        iris_cy = cy + clamped_gy

        # Shoxparda nuri (Glint catchlight) - 3D yorug'lik refleksi
        glint_cx = iris_cx - r_iris * 0.22
        glint_cy = iris_cy - (r_iris / aspect) * 0.22

        lines = []

        for y in range(rows):
            line_chars = []
            dy = (y - cy)
            is_laser = scanner.is_laser_on_row(y, cy, h_top_open + h_bot_open) if scanner else False

            for x in range(cols):
                dx = (x - cx)
                u = dx / w_eye

                # Ko'z chegarasidan tashqarida: mutlaq toza qora fon
                if abs(u) >= 1.05:
                    line_chars.append(" ")
                    continue

                # Haqiqiy anatomik qovoq egri chiziqlari (Asimmetrik tabiiy bodom shakli)
                arch = math.sqrt(max(0.0, 1.0 - min(1.0, u * u)))
                y_top_rest = -h_top_open * arch * (1.0 - 0.16 * u)
                y_bot_rest = h_bot_open * arch * (0.94 + 0.10 * u)

                # Burun tomonidagi ko'z yoshi yo'li (Medial canthus / Caruncle)
                if u < -0.85:
                    tear_t = (-u - 0.85) / 0.40
                    y_top_rest = y_top_rest * (1.0 - tear_t * 0.48)
                    y_bot_rest = y_bot_rest * (1.0 - tear_t * 0.38)

                # Qovoq yumilishi (Blinking)
                y_top_curr = y_top_rest * (1.0 - b) + (y_bot_rest * 0.94) * b
                y_bot_curr = y_bot_rest * (1.0 - 0.10 * b)

                # -----------------------------------------------------------------
                # A. KO'ZNING ICHKI MAYDONI: Sclera, Iris, Pupil va Glint
                # -----------------------------------------------------------------
                if y_top_curr <= dy <= y_bot_curr:
                    dist_lid = dy - y_top_curr
                    cast_shadow = min(1.0, max(0.38, 0.38 + 0.62 * (dist_lid / 3.2)))

                    idx = (x - iris_cx)
                    idy = (y - iris_cy) * aspect
                    r_dist = math.sqrt(idx * idx + idy * idy)

                    if r_dist <= r_iris:
                        # 1. Glint Catchlight (Yorug'lik refleksi)
                        dist_glint = math.sqrt((x - glint_cx) ** 2 + ((y - glint_cy) * aspect) ** 2)
                        if dist_glint < (r_pupil * 0.40):
                            char = "*"
                            cell_col = pal["glint"]
                            bright = 1.00
                        elif dist_glint < (r_pupil * 0.70) and r_dist <= r_pupil:
                            char = "·"
                            cell_col = pal["glint"]
                            bright = 0.65
                        elif r_dist <= r_pupil:
                            # 2. Qop-qora tabiiy qorachiq
                            line_chars.append(" ")
                            continue
                        elif self.is_sharingan:
                            # =========================================================
                            # 3. UCHIHA SHARINGAN (3-TOMOE + ORBITAL RING + MATRIX BINARY)
                            # =========================================================
                            span = (r_iris - r_pupil)
                            s = (r_dist - r_pupil) / span
                            theta = math.atan2(idy, idx)

                            r_orbit = r_pupil + 0.50 * span
                            r_head = 0.21 * span
                            tail_len = 0.95

                            in_tomoe = False
                            for k in range(3):
                                phi = self.sharingan_angle + k * (2.0 * math.pi / 3.0)
                                hx = r_orbit * math.cos(phi)
                                hy = r_orbit * math.sin(phi)
                                dh = math.hypot(idx - hx, idy - hy)
                                if dh <= r_head:
                                    in_tomoe = True
                                    break
                                dth = (theta - phi) % (2.0 * math.pi)
                                if 0.0 <= dth <= tail_len:
                                    t = dth / tail_len
                                    rt = r_orbit - 0.18 * span * (t ** 1.3)
                                    wt = r_head * ((1.0 - t) ** 0.85)
                                    if abs(r_dist - rt) <= wt:
                                        in_tomoe = True
                                        break

                            in_ring = abs(r_dist - r_orbit) <= (0.045 * span)

                            # Konsentrik binar xalqalar bo'ylab aylanuvchi 0 va 1
                            track = int(s * 8.0)
                            num_digits = 18.0 + track * 6.0
                            angular_pos = ((theta + math.pi) / (2.0 * math.pi)) * num_digits + current_time * 2.8
                            char = "1" if (int(angular_pos) % 2 == 0) else "0"

                            if is_laser:
                                # Laser scan chizig'i
                                line_chars.append(f"\033[38;2;0;255;255m{char}{C_RESET}")
                                continue

                            if in_tomoe:
                                # Tomoe ichi: aniq qoramtir binar raqamlar va obsidian fon
                                # Raqamlar sezilib turadi, tomoe shakli esa 100% tiniq ajralib turadi
                                line_chars.append(f"\033[48;2;8;1;2m\033[38;2;48;6;10m{char}{C_RESET}")
                                continue
                            elif in_ring:
                                # Tomoelarni tutashtiruvchi nozik orbital doira
                                line_chars.append(f"\033[38;2;75;8;14m{char}{C_RESET}")
                                continue
                            elif s > 0.88:
                                # Tashqi qora halqa (Limbal ring)
                                line_chars.append(f"\033[38;2;25;3;6m{char}{C_RESET}")
                                continue
                            else:
                                # Qip-qizil olovli Sharingan Kamalak pardasi (Scarlet Crimson Matrix)
                                chakra_pulse = 0.88 + 0.12 * math.sin(current_time * 6.5 + theta * 3.0)
                                r_val = int(min(255, 245 * chakra_pulse * cast_shadow))
                                g_val = int(24 * chakra_pulse * cast_shadow)
                                b_val = int(30 * chakra_pulse * cast_shadow)
                                line_chars.append(f"\033[38;2;{r_val};{g_val};{b_val}m{char}{C_RESET}")
                                continue
                        else:
                            # 3. Kamalak parda (Iris): Binar kiber-oqim (0 va 1)
                            s = (r_dist - r_pupil) / (r_iris - r_pupil)
                            theta = math.atan2(idy, idx)

                            # Konsentrik binar xalqalar bo'ylab aylanuvchi 0 va 1
                            speed_mult = 1.35 if self.manual_squint else 1.0
                            track = int(s * 6.0)
                            num_digits = 14.0 + track * 8.0
                            stream_speed = (2.2 if track % 2 == 0 else -1.8) * speed_mult
                            angular_pos = ((theta + math.pi) / (2.0 * math.pi)) * num_digits + current_time * stream_speed
                            char = "1" if (int(angular_pos) % 2 == 0) else "0"

                            fibers = math.cos(22.0 * theta + math.sin(5.0 * theta))
                            collarette = math.exp(-((s - 0.40) / 0.16) ** 2)
                            limbal = 1.0 - (0.65 * ((s - 0.82) / 0.18) if s > 0.82 else 0.0)

                            raw_b = (0.35 + 0.22 * fibers + 0.35 * collarette) * limbal * cast_shadow
                            bright = max(0.08, min(1.0, raw_b))

                            if s > 0.85:
                                cell_col = pal["iris_limbal"]
                            elif s < 0.20:
                                cell_col = lerp_c(pal["iris_mid"], pal["iris_core"], 0.7)
                            elif collarette > 0.45:
                                cell_col = pal["iris_core"]
                            else:
                                cell_col = lerp_c(pal["iris_deep"], pal["iris_mid"], bright)

                    else:
                        # 4. Sclera (Ko'z oqi - 3D sferik relyef va qovoq soyasi)
                        sphere_rad_x = w_eye * 1.15
                        sphere_rad_y = h_top_open * 1.6
                        s_dx = dx / sphere_rad_x
                        s_dy = (dy * aspect) / sphere_rad_y
                        sphere_val = math.sqrt(max(0.0, 1.0 - min(1.0, s_dx * s_dx + s_dy * s_dy)))

                        bright = (0.45 + 0.42 * sphere_val) * cast_shadow

                        if u < -0.82:
                            bright = 0.22 + 0.16 * sphere_val
                            cell_col = lerp_c(pal["skin"], pal["sclera"], 0.35)
                        else:
                            cell_col = (236, 215, 218) if self.is_sharingan else pal["sclera"]

                        bayer_threshold = (BAYER_4X4[y % 4][x % 4] + 0.5) / 16.0
                        dithered_val = bright + (bayer_threshold - 0.5) * 0.22
                        char_idx = int(max(0.0, min(1.0, dithered_val)) * (len(CHARS) - 1))
                        char = CHARS[char_idx]

                    # Apple Face ID skanerlash chizig'i (FAQAT KO'ZNING ICHIDA CHIZILADI!)
                    if is_laser:
                        cell_col = (0, 255, 255)
                        bright = min(1.0, bright + 0.35)

                    final_col = (
                        int(cell_col[0] * bright),
                        int(cell_col[1] * bright),
                        int(cell_col[2] * bright),
                    )
                    line_chars.append(f"{rgb(final_col)}{char}{C_RESET}")

                # -----------------------------------------------------------------
                # B. QOVOQDAN TASHQARI: Mutlaq toza, qop-qora fon!
                # -----------------------------------------------------------------
                else:
                    # Qovoqdan tashqarida aslo hech qanday artefakt chizilmaydi: sof qora!
                    line_chars.append(" ")

            lines.append("".join(line_chars).rstrip())

        return lines
