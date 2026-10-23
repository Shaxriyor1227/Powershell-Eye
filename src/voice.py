# -*- coding: utf-8 -*-
"""
Asinxron Kiber-Ovoz Tizimi (Premium AI Voice Engine)
Microsoft Zira tabiiy ovozi va 'Shaxriyor' ismining toza fonetik talaffuzi.
"""

import sys
import threading
import queue

class CyberVoice:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self._queue = queue.Queue()
        self._running = True
        self.voice_engine = None

        if sys.platform == "win32":
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def _init_sapi(self):
        """Microsoft Zira tabiiy ovozini tanlash va sozlash."""
        try:
            import win32com.client
            engine = win32com.client.Dispatch("SAPI.SpVoice")
            
            # Microsoft Zira ovozini topish (eng toza va tabiiy ovoz)
            zira_voice = None
            for i in range(engine.GetVoices().Count):
                desc = engine.GetVoices().Item(i).GetDescription()
                if "zira" in desc.lower():
                    zira_voice = engine.GetVoices().Item(i)
                    break
            
            if zira_voice:
                engine.Voice = zira_voice

            # Tabiiy, muloyim va sokin gapirish tezligi (Rate = 0: insoniy me'yor)
            engine.Rate = 0       # Tabiiy, shoshilmasdan sokin so'zlash
            engine.Volume = 100   # Aniq va jarangdor
            return engine
        except Exception:
            return None

    def _format_phonetics(self, text):
        """Ism va kiber so'zlarni xatosiz toza talaffuz qildirish."""
        # 'Shaxriyor' 'x' harfi ingliz ovozida 'k' yoki buzilib o'qilmasligi uchun 'Shahree-yor' ga o'giriladi
        clean = text
        for variant in ["Shaxriyor", "shaxriyor", "SHAXRIYOR", "Shakhriyor", "shakhriyor", "Shah-ri-yor", "Shahriyor", "shahriyor"]:
            clean = clean.replace(variant, "Shahree-yor")
        return clean

    def _worker(self):
        engine = self._init_sapi()
        
        while self._running:
            try:
                raw_text = self._queue.get(timeout=0.4)
                if not raw_text or not self.enabled:
                    continue

                text = self._format_phonetics(raw_text)

                if engine:
                    try:
                        # SVSFlagsAsync = 1 (fonda, animatsiyani to'xtatmasdan aytish)
                        engine.Speak(text, 0)
                    except Exception:
                        pass
                else:
                    # Zaxira (fallback) PowerShell orqali
                    import subprocess
                    clean = text.replace("'", "")
                    cmd = f"(New-Object -ComObject SAPI.SpVoice).Speak('{clean}')"
                    subprocess.run(
                        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    )
            except queue.Empty:
                continue
            except Exception:
                continue

    def speak(self, text):
        """Matnni fonga qo'shish."""
        if self.enabled:
            self._queue.put(text)

    def toggle_mute(self):
        self.enabled = not self.enabled
        return self.enabled

    def stop(self):
        self._running = False
