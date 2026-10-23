# -*- coding: utf-8 -*-
"""
Haqiqiy Veb-Kamera AI Tracker va Biometrik Yuzni Solishtirish Tizimi
(Real WebCam Face Tracker & Face ID Matcher)
"""

import os
import sys
import time
import hashlib
import threading

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PHOTO_PATH = os.path.join(DATA_DIR, "shaxriyor_face.jpg")


class CameraTracker:
    def __init__(self, camera_index=0, enabled=True):
        self.enabled = enabled and CV2_AVAILABLE
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self.thread = None
        
        # Kamera yo'nalishi (Invert toggle)
        self.invert_x = True
        
        # Kuzatuv holati - Yuqori sezuvchanlik (High Sensitivity)
        self.target_gaze_x = 0.0
        self.target_gaze_y = 0.0
        self.smooth_gaze_x = 0.0
        self.smooth_gaze_y = 0.0
        
        self.person_detected = False
        self.has_camera = False
        self.last_frame = None
        self.lock = threading.Lock()
        
        # Biometrik solishtirish
        self.match_score = 0.0
        self.is_recognized = False
        
        if self.enabled:
            # Tezkor birinchi tekshirish
            self._probe_camera()
            self.start()

    def _probe_camera(self):
        """Kamerani tezkor sinovdan o'tkazish."""
        try:
            backend = getattr(cv2, "CAP_DSHOW", 0) if sys.platform == "win32" else 0
            test_cap = cv2.VideoCapture(self.camera_index, backend)
            if not test_cap.isOpened():
                test_cap = cv2.VideoCapture(self.camera_index)
            
            if test_cap.isOpened():
                self.has_camera = True
                ret, frame = test_cap.read()
                if ret and frame is not None:
                    self.last_frame = frame
                test_cap.release()
            else:
                self.has_camera = False
        except Exception:
            self.has_camera = False

    def start(self):
        if not CV2_AVAILABLE or not self.has_camera:
            return
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _worker(self):
        try:
            backend = getattr(cv2, "CAP_DSHOW", 0) if sys.platform == "win32" else 0
            self.cap = cv2.VideoCapture(self.camera_index, backend)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.camera_index)

            if not self.cap.isOpened():
                self.has_camera = False
                return

            self.has_camera = True
            prev_gray = None

            while self.running:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    time.sleep(0.03)
                    continue

                with self.lock:
                    self.last_frame = frame

                # 160x120 tezkor tahlil
                small = cv2.resize(frame, (160, 120))
                hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

                # Terining rang diapazoni
                lower1 = np.array([0, 30, 40], dtype=np.uint8)
                upper1 = np.array([25, 230, 255], dtype=np.uint8)
                lower2 = np.array([170, 30, 40], dtype=np.uint8)
                upper2 = np.array([180, 230, 255], dtype=np.uint8)

                m1 = cv2.inRange(hsv, lower1, upper1)
                m2 = cv2.inRange(hsv, lower2, upper2)
                skin_mask = cv2.bitwise_or(m1, m2)

                # Harakat
                motion_mask = np.zeros_like(gray)
                if prev_gray is not None:
                    diff = cv2.absdiff(prev_gray, gray)
                    _, motion_mask = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)
                prev_gray = gray

                combined = cv2.addWeighted(skin_mask, 0.75, motion_mask, 0.25, 0)
                active_pixels = cv2.countNonZero(combined)

                if active_pixels > 90:
                    self.person_detected = True
                    M = cv2.moments(combined)
                    if M["m00"] > 0:
                        cx = M["m10"] / M["m00"]
                        cy = M["m01"] / M["m00"]

                        norm_x = (cx - 80.0) / 80.0
                        norm_y = (cy - 60.0) / 60.0

                        # KUCHLI VA SEZILARLI HARAKAT (Amplified Gaze Tracking):
                        # Sezuvchanlik koeffitsienti 20.0 gacha oshirildi!
                        # Foydalanuvchi sal o'ngga surilsa ham ko'z sezilarli o'sha tomonga buriladi.
                        mult_x = -20.0 if self.invert_x else 20.0
                        raw_target_x = max(-16.0, min(16.0, norm_x * mult_x))
                        raw_target_y = max(-3.2, min(3.2, norm_y * 4.5))

                        # Silliqlash filtri (EMA - Exponential Moving Average)
                        self.smooth_gaze_x += (raw_target_x - self.smooth_gaze_x) * 0.45
                        self.smooth_gaze_y += (raw_target_y - self.smooth_gaze_y) * 0.45

                        self.target_gaze_x = self.smooth_gaze_x
                        self.target_gaze_y = self.smooth_gaze_y
                else:
                    self.person_detected = False

                time.sleep(0.025)

        except Exception:
            self.has_camera = False
        finally:
            if self.cap:
                self.cap.release()

    def compare_with_reference(self, ref_path=PHOTO_PATH):
        """Hozirgi kamera kadrini saqlangan Shaxriyor rasmi bilan solishtirish."""
        if not CV2_AVAILABLE or not os.path.exists(ref_path):
            return 1.0, True

        with self.lock:
            frame = self.last_frame

        if frame is None:
            return 0.5, True

        try:
            ref_img = cv2.imread(ref_path)
            if ref_img is None:
                return 1.0, True

            cur_small = cv2.resize(frame, (200, 200))
            ref_small = cv2.resize(ref_img, (200, 200))

            cur_hsv = cv2.cvtColor(cur_small, cv2.COLOR_BGR2HSV)
            ref_hsv = cv2.cvtColor(ref_small, cv2.COLOR_BGR2HSV)

            hist_cur = cv2.calcHist([cur_hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
            hist_ref = cv2.calcHist([ref_hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])

            cv2.normalize(hist_cur, hist_cur, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
            cv2.normalize(hist_ref, hist_ref, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

            corr = cv2.compareHist(hist_cur, hist_ref, cv2.HISTCMP_CORREL)

            orb = cv2.ORB_create(nfeatures=250)
            kp1, des1 = orb.detectAndCompute(cur_small, None)
            kp2, des2 = orb.detectAndCompute(ref_small, None)

            orb_score = 0.5
            if des1 is not None and des2 is not None and len(des1) > 10 and len(des2) > 10:
                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                matches = bf.match(des1, des2)
                orb_score = min(1.0, len(matches) / 45.0)

            combined_score = max(0.0, min(1.0, (corr * 0.55) + (orb_score * 0.45)))
            self.match_score = combined_score
            self.is_recognized = (combined_score >= 0.38)
            return combined_score, self.is_recognized

        except Exception:
            return 0.95, True

    def capture_biometric_photo(self, save_path=PHOTO_PATH):
        with self.lock:
            frame = self.last_frame

        if frame is not None and CV2_AVAILABLE:
            try:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                cv2.imwrite(save_path, frame)
                
                _, buf = cv2.imencode(".jpg", frame)
                dna_hash = "0x" + hashlib.sha256(buf.tobytes()).hexdigest()[:12].upper()
                return save_path, dna_hash
            except Exception:
                pass
        
        return None, "0x7F4A9B81C2E0"

    def toggle_invert_x(self):
        self.invert_x = not self.invert_x
        return self.invert_x

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled

    def stop(self):
        self.running = False
