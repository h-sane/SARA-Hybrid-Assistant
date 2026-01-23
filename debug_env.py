import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Current Working Directory: {os.getcwd()}")
print("System Path:")
for p in sys.path:
    print(f"  - {p}")

try:
    import gtts
    print(f"gTTS imported successfully from: {gtts.__file__}")
except ImportError as e:
    print(f"gTTS Import Failed: {e}")

try:
    import pygame
    print(f"Pygame imported successfully from: {pygame.__file__}")
except ImportError as e:
    print(f"Pygame Import Failed: {e}")
