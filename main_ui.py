# main_ui.py

import sys
import json
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QObject

# --- Worker class to run the VoiceService in a background thread ---
class VoiceWorker(QObject):
    state_changed = pyqtSignal(str, str)
    command_transcribed = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, voice_service_class):
        super().__init__()
        self.voice_service_class = voice_service_class
        self.voice_service = None
        self._is_running = True

    def run(self):
        print("VoiceWorker thread started.")
        self.voice_service = self.voice_service_class()

        if not self.voice_service.porcupine:
            self.signals.error.emit("Voice service failed to initialize.")
            return
            
        while self._is_running:
            if self.voice_service.listen_for_wake_word():
                self.signals.state_changed.emit("active", "Yes, Master?")
                command = self.voice_service.listen_for_command()
                if command:
                    self.signals.command_transcribed.emit(command)
                else:
                    self.signals.state_changed.emit("inactive", "SARA is asleep.")
            QThread.msleep(20)
        
        if self.voice_service:
            self.voice_service.cleanup()
        print("VoiceWorker thread stopped.")

    def stop(self):
        self._is_running = False

# --- The Main UI Widget ---
class SaraWidget(QWidget):
    def __init__(self, host_agent_class):
        super().__init__()
        self.host_agent = host_agent_class()
        self.voice_thread = None
        self.voice_worker = None
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(100, 100, 200, 280)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.animation_label = QLabel(self)
        self.animation_label.setFixedSize(QSize(180, 180))
        self.layout.addWidget(self.animation_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.response_label = QLabel("Initializing...", self)
        self.response_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.response_label.setWordWrap(True)
        self.response_label.setStyleSheet("color: #e0e0e0; font-size: 12px; font-weight: bold;")
        self.layout.addWidget(self.response_label)
        
        self.input_textbox = QLineEdit(self)
        self.input_textbox.setPlaceholderText("Type command...")
        self.input_textbox.setStyleSheet("QLineEdit { background-color: rgba(37, 37, 37, 0.8); border: 1px solid #444; border-radius: 10px; color: #e0e0e0; padding: 5px; }")
        self.layout.addWidget(self.input_textbox)
        self.input_textbox.returnPressed.connect(self.process_text_command)
        
        self.movies = {
            "inactive": QMovie("resources/sara_orb.gif"), # Use GIF for all states
            "active": QMovie("resources/sara_orb.gif"),
            "listening": QMovie("resources/sara_orb.gif"),
            "speaking": QMovie("resources/sara_orb.gif")
        }
        self.set_state("inactive", "Initializing SARA...")

    def set_state(self, state: str, text: str = ""):
        current_movie = self.animation_label.movie()
        if current_movie: current_movie.stop()
        
        movie = self.movies.get(state)
        if movie:
            self.animation_label.setMovie(movie)
            if state != "inactive":
                movie.start() # Play animation for active states
            else:
                movie.jumpToFrame(0) # Show first frame for inactive state
        self.response_label.setText(text)

    def setup_backend_threads(self):
        from voice_service import VoiceService, speak
        self.speak_function = speak # Store the speak function
        
        self.voice_thread = QThread(self)
        self.voice_worker = VoiceWorker(VoiceService)
        self.voice_worker.moveToThread(self.voice_thread)
        
        self.voice_worker.signals.state_changed.connect(self.set_state)
        self.voice_worker.signals.command_transcribed.connect(self.process_command)
        self.voice_worker.signals.error.connect(lambda msg: self.set_state("inactive", msg))
        
        self.voice_thread.started.connect(self.voice_worker.run)
        self.voice_thread.start()
        self.set_state("inactive", "SARA is asleep.")

    def process_command(self, command: str):
        self.set_state("speaking", "Thinking...")
        response_data = self.host_agent.process_user_command(command)
        response_text = response_data.get("response", "I'm not sure how to respond.")
        
        self.speak_function(response_text)
        self.set_state("inactive", "SARA is asleep.")

    def process_text_command(self):
        command = self.input_textbox.text()
        if not command: return
        self.input_textbox.clear()
        self.process_command(command)

    def closeEvent(self, event):
        print("Closing widget, stopping threads...")
        if self.voice_thread:
            self.voice_worker.stop()
            self.voice_thread.quit()
            self.voice_thread.wait()
        event.accept()

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = event.globalPosition().toPoint() - self.oldPos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

# --- Main Application Entry Point ---
def main():
    # Step 1: Create the QApplication. This MUST be the absolute first step.
    app = QApplication(sys.argv)
    
    # Step 2: NOW it is safe to import our heavy backend modules.
    from host_agent import HostAgent
    
    # Step 3: Create and show the widget
    widget = SaraWidget(HostAgent())
    widget.show()
    
    # Step 4: Start the backend threads after the UI is visible
    widget.setup_backend_threads()
    
    # Step 5: Start the application's event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()