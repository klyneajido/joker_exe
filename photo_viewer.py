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

class MinimalPhotoViewer:
    def __init__(self, root, captured_images=None):
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
        
        # Simple two-panel layout
        self.content_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left panel for thumbnails
        self.gallery_panel = ttk.Frame(self.content_frame, style='Panel.TFrame')
        self.gallery_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=0, ipadx=10, ipady=10)
        
        gallery_label = tk.Label(
            self.gallery_panel,
            text="Gallery",
            font=('Helvetica', 12, 'bold'),
            bg=self.colors["bg_panel"],
            fg=self.colors["text_primary"]
        )
        gallery_label.pack(pady=(10, 15))
        
        self.gallery_content = ttk.Frame(self.gallery_panel, style='Panel.TFrame')
        self.gallery_content.pack(fill=tk.BOTH, expand=True)
        
        # Right panel for webcam
        self.webcam_panel = ttk.Frame(self.content_frame, style='Panel.TFrame')
        self.webcam_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=0, pady=0, ipadx=10, ipady=10)
        
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
        
        # Load captured images if provided
        self.captured_photos = []
        if captured_images:
            self.load_captured_images(captured_images)
        else:
            self.check_for_observation_photos()
        
        # Start webcam
        self.cap = cv2.VideoCapture(0)
        self.webcam_active = True
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

    def load_captured_images(self, image_paths):
        """Load and display thumbnails in a simple list"""
        # Clear existing content
        for widget in self.gallery_content.winfo_children():
            widget.destroy()
        
        for img_path in image_paths:
            try:
                # Create a frame for each thumbnail
                thumb_frame = ttk.Frame(self.gallery_content, style='Panel.TFrame')
                thumb_frame.pack(fill=tk.X, pady=5, padx=5)
                
                # Load and resize image
                img = Image.open(img_path) if os.path.exists(img_path) else Image.new('RGB', (100, 75), color='gray')
                img.thumbnail((120, 90), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Store reference
                self.captured_photos.append(photo)
                
                # Display thumbnail
                img_label = tk.Label(
                    thumb_frame, 
                    image=photo, 
                    bg=self.colors["bg_panel"],
                    bd=1,
                    relief=tk.SOLID
                )
                img_label.pack(pady=2)
                
                # Simple label for the image name
                phase_name = os.path.basename(img_path).replace("observation_", "").replace(".jpg", "")
                phase_name = phase_name.replace("_", " ").title()
                
                name_label = tk.Label(
                    thumb_frame,
                    text=phase_name,
                    font=('Helvetica', 9),
                    bg=self.colors["bg_panel"],
                    fg=self.colors["text_secondary"]
                )
                name_label.pack()
                
            except Exception as e:
                print(f"Error loading image {img_path}: {str(e)}")

    def update_webcam(self):
        """Simple webcam update without effects"""
        while self.webcam_active:
            ret, frame = self.cap.read()
            if ret:
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
                
            time.sleep(0.03)  # ~30 FPS

    def show_cat_with_laugh(self):
        """Simple cat popup with laugh sound"""
        try:
            # Play laugh sound
            if os.path.exists("laugh.mp3"):
                pygame.mixer.music.load("laugh.mp3")
                pygame.mixer.music.play(loops=-1)  # Loop indefinitely
            
            # Show cat image if exists
            if os.path.exists("cat.png"):
                # Create a simple window
                self.cat_window = tk.Toplevel(self.root)
                self.cat_window.title("Surprise")
                self.cat_window.geometry("300x250")
                self.cat_window.configure(bg=self.colors["bg_panel"])
                self.cat_window.attributes('-topmost', True)  # Keep on top
                
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
                cat_img = Image.open("cat.png")
                cat_img = cat_img.resize((250, 180), Image.Resampling.LANCZOS)
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
        except Exception as e:
            print(f"Error in show_cat_with_laugh: {str(e)}")

    def check_for_observation_photos(self):
        """Check for observation photos"""
        observation_paths = []
        phases = ["game_start", "correct_answer", "wrong_answer", "final_reveal"]
        
        for phase in phases:
            potential_path = f"observation_{phase}.jpg"
            if os.path.exists(potential_path):
                observation_paths.append(potential_path)
        
        if observation_paths:
            self.load_captured_images(observation_paths)

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
    parser.add_argument('--images', nargs='*', help='List of image paths')
    args = parser.parse_args()
    
    root = tk.Tk()
    app = MinimalPhotoViewer(root, args.images)
    root.mainloop()

if __name__ == "__main__":
    main()