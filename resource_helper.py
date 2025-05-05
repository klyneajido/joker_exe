import os
import sys
import pygame

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def play_sound(sound_file):
    """Play a sound file using pygame"""
    try:
        sound_path = resource_path(sound_file)
        pygame.mixer.init()
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"DEBUG: Error playing sound {sound_file}: {str(e)}")

