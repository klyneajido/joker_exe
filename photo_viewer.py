import tkinter as tk
from tkinter import ttk
import cv2
import threading
import time
import sys
import os
import argparse
from PIL import Image, ImageTk
import pygame
from datetime import datetime
from resource_helper import resource_path, play_sound

class MinimalPhotoViewer:
    def __init__(self, root):
        # Initialize main window
        self.root = root
        self.root.title("Terminal Enigma")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        self.root.configure(bg='#f5f5f5')
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize pygame for audio
        pygame.mixer.init()
        
        # Initialize color scheme - minimal and modern
        self.colors = {
            "bg_main": "#f5f5f5",
            "bg_panel": "#ffffff",
            "accent": "#3498db",
            "text_primary": "#333333",
            "text_secondary": "#666666",
            "border": "#e0e0e0"
        }
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=self.colors["bg_main"])
        self.style.configure('Panel.TFrame', background=self.colors["bg_panel"])
        
        # Main container
        self.main_frame = ttk.Frame(self.root, style='TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Simple header
        self.create_header()
        
        # Webcam panel
        self.webcam_panel = ttk.Frame(self.main_frame, style='Panel.TFrame')
        self.webcam_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        webcam_header = tk.Label(
            self.webcam_panel,
            text="Live Feed",
            font=('Helvetica', 12, 'bold'),
            bg=self.colors["bg_panel"],
            fg=self.colors["text_primary"]
        )
        webcam_header.pack(pady=(10, 15))
        
        # Simple webcam display
        self.webcam_container = ttk.Frame(self.webcam_panel, style='Panel.TFrame')
        self.webcam_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.webcam_label = tk.Label(
            self.webcam_container,
            bg=self.colors["bg_panel"],
            bd=1,
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=0
        )
        self.webcam_label.pack(fill=tk.BOTH, expand=True)
        
        # Prepare cat window
        self.cat_window = None
        
        # Start webcam
        self.cap = cv2.VideoCapture(0)
        self.webcam_active = True
        self.placeholder_shown = False
        self.webcam_thread = threading.Thread(target=self.update_webcam, daemon=True)
        self.webcam_thread.start()
        
        # Schedule cat appearance
        self.root.after(2000, self.show_cat_with_laugh)

    def create_header(self):
        """Create simple header"""
        header_frame = ttk.Frame(self.main_frame, style='TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            header_frame, 
            text="Terminal Enigma", 
            font=('Helvetica', 18, 'bold'),
            bg=self.colors["bg_main"],
            fg=self.colors["text_primary"]
        )
        title_label.pack(side=tk.LEFT)
        
        # Simple timestamp
        self.time_label = tk.Label(
            header_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=('Helvetica', 12),
            bg=self.colors["bg_main"],
            fg=self.colors["text_secondary"]
        )
        self.time_label.pack(side=tk.RIGHT)
        self.update_clock()

    def update_clock(self):
        """Update the clock every second"""
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self.update_clock)

    def update_webcam(self):
        """Simple webcam update without effects"""
        while self.webcam_active:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None and not frame.size == 0:
                    # Convert to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image
                    img = Image.fromarray(frame_rgb)
                    
                    # Resize to fit display area
                    img = img.resize((640, 480), Image.Resampling.LANCZOS)
                    
                    # Create photo image
                    photo = ImageTk.PhotoImage(img)
                    
                    # Update label
                    self.webcam_label.config(image=photo)
                    self.webcam_label.image = photo
                    self.placeholder_shown = False
                else:
                    # If webcam fails, show a placeholder
                    if not self.placeholder_shown:
                        self.placeholder_shown = True
                        self.webcam_label.config(text="Webcam not available", 
                                               font=('Arial', 18), fg='black',
                                               bg=self.colors["bg_panel"])
            except Exception as e:
                print(f"Error in webcam update: {str(e)}")
                # If error occurs, show a placeholder
                if not self.placeholder_shown:
                    self.placeholder_shown = True
                    self.webcam_label.config(text="Webcam error", 
                                           font=('Arial', 18), fg='black',
                                           bg=self.colors["bg_panel"])
                    
            time.sleep(0.03)  # ~30 FPS

    def show_cat_with_laugh(self):
        """Cat popup with looping laugh sound"""
        try:
            # Play laugh sound on loop
            sound_path = resource_path("laugh.mp3")
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            
            # Show cat image if exists
            cat_path = resource_path("cat.png")
            if os.path.exists(cat_path):
                # Create a simple window without title bar
                self.cat_window = tk.Toplevel(self.root)
                self.cat_window.title("Surprise")
                self.cat_window.geometry("300x250")
                self.cat_window.configure(bg=self.colors["bg_panel"])
                self.cat_window.attributes('-topmost', True)  # Keep on top
                
                # Remove title bar
                self.cat_window.overrideredirect(True)
                
                # Center the window
                window_width = self.root.winfo_width()
                window_height = self.root.winfo_height()
                x = self.root.winfo_x() + int(window_width/2 - 150)
                y = self.root.winfo_y() + int(window_height/2 - 125)
                self.cat_window.geometry(f"+{x}+{y}")
                
                # Simple container
                cat_frame = ttk.Frame(self.cat_window, style='Panel.TFrame')
                cat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Load and display cat image
                cat_img = Image.open(cat_path)
                cat_img = cat_img.resize((250, 180), Image.LANCZOS)
                photo = ImageTk.PhotoImage(cat_img)
                
                cat_label = tk.Label(
                    cat_frame,
                    image=photo,
                    bg=self.colors["bg_panel"]
                )
                cat_label.image = photo
                cat_label.pack(pady=5)
                
                # Simple message
                message_label = tk.Label(
                    cat_frame,
                    text="Bro was terrified",
                    font=('Helvetica', 14, 'bold'),
                    bg=self.colors["bg_panel"],
                    fg=self.colors["accent"]
                )
                message_label.pack(pady=5)
                
                # Don't close cat window when clicked
                self.cat_window.protocol("WM_DELETE_WINDOW", lambda: None)
        except Exception as e:
            print(f"Error in show_cat_with_laugh: {str(e)}")

    def on_close(self):
        """Clean up on close"""
        self.webcam_active = False
        if self.cap.isOpened():
            self.cap.release()
        
        # Stop music
        pygame.mixer.music.stop()
        
        # Close cat window if exists
        if self.cat_window and self.cat_window.winfo_exists():
            self.cat_window.destroy()
            
        self.root.destroy()

def main():
    parser = argparse.ArgumentParser(description='Minimal Photo Viewer')
    # We'll keep the --images argument for compatibility, but we won't use it
    parser.add_argument('--images', nargs='+', help='List of image files to display (ignored)')
    args = parser.parse_args()
    
    root = tk.Tk()
    app = MinimalPhotoViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()



