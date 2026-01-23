# simple_ui.py

import sys
import threading
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QTextEdit, QLabel, QCheckBox, QHBoxLayout)
from PyQt6.QtCore import pyqtSignal, QObject, Qt, QTimer

from voice_service import VoiceService
from llm_service import online_llm_text

class WorkerSignals(QObject):
    update_log = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    init_finished = pyqtSignal()

class SaraShowcase(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.is_running = False
        self.voice_service = None
        self.thread = None
        self.signals = WorkerSignals()
        self.signals.update_log.connect(self.log_message)
        self.signals.status_changed.connect(self.update_status)
        self.signals.init_finished.connect(self.on_init_finished)

        # Start loading VoiceService (and Whisper model) in background
        self.update_status("Loading Whisper Model... (Please Wait)")
        self.start_btn.setEnabled(False)
        threading.Thread(target=self.load_voice_service, daemon=True).start()

    def initUI(self):
        self.setWindowTitle("SARA - Offline Whisper STT")
        self.setGeometry(100, 100, 400, 500)
        
        layout = QVBoxLayout()
        
        # Status Label
        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.status_label)

        # Chat Log
        self.chat_log = QTextEdit()
        self.chat_log.setReadOnly(True)
        layout.addWidget(self.chat_log)

        # Engine Toggle
        self.elevenlabs_check = QCheckBox("Use ElevenLabs (High Quality)")
        layout.addWidget(self.elevenlabs_check)

        # Buttons
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Listening")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        self.start_btn.clicked.connect(self.start_loop)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px;")
        self.stop_btn.clicked.connect(self.stop_loop)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_voice_service(self):
        try:
            self.voice_service = VoiceService()
            self.signals.init_finished.emit()
        except Exception as e:
            self.signals.update_log.emit(f"Error loading model: {e}")

    def on_init_finished(self):
        self.update_status("Model Loaded. Ready.")
        self.start_btn.setEnabled(True)
        self.log_message("--- System Ready (Whisper Small) ---")

    def log_message(self, text):
        self.chat_log.append(text)

    def update_status(self, text):
        self.status_label.setText(f"Status: {text}")

    def start_loop(self):
        if self.is_running: return
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.thread = threading.Thread(target=self.run_process)
        self.thread.start()

    def stop_loop(self):
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.update_status("Stopping...")

    def run_process(self):
        self.signals.update_log.emit("--- Started ---")
        
        while self.is_running:
            self.signals.status_changed.emit("Listening...")
            user_text = self.voice_service.listen()
            
            if not self.is_running: break

            if user_text:
                self.signals.update_log.emit(f"User: {user_text}")
                self.signals.status_changed.emit("Thinking...")
                
                # Simple LLM Call
                prompt = f"Respond to: {user_text}"
                response = online_llm_text(prompt)
                
                self.signals.update_log.emit(f"SARA: {response}")
                self.signals.status_changed.emit("Speaking...")
                
                engine = "elevenlabs" if self.elevenlabs_check.isChecked() else "google"
                self.voice_service.speak(response, engine=engine)
            else:
                pass 
            
        self.signals.status_changed.emit("Idle")
        self.signals.update_log.emit("--- Stopped ---")

    def closeEvent(self, event):
        self.is_running = False
        if self.voice_service:
            self.voice_service.cleanup()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SaraShowcase()
    window.show()
    sys.exit(app.exec())
