import tkinter as tk
import cv2
import threading
import time
import sys
import os
import argparse
from PIL import Image, ImageTk, ImageEnhance
import pygame

class PhotoViewer:
    def __init__(self, root, captured_images=None):
        self.root = root
        self.root.title("Terminal Enigma - Captured Moments")
        self.root.geometry("1000x800")
        self.root.configure(bg='#000')
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize pygame for audio
        pygame.mixer.init()
        
        # Main frame
        self.main_frame = tk.Frame(self.root, bg='#000')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(
            self.main_frame, 
            text="YOUR CAPTURED MOMENTS", 
            fg="#FF0000", 
            bg="#000", 
            font=('Arial', 24, 'bold')
        )
        title_label.pack(pady=20)
        
        # Frame for captured images
        self.images_frame = tk.Frame(self.main_frame, bg='#000')
        self.images_frame.pack(fill=tk.X, pady=10)
        
        # Load and display captured images if provided
        self.captured_photos = []
        if captured_images:
            self.load_captured_images(captured_images)
        
        # Frame for live webcam
        self.webcam_frame = tk.Frame(self.main_frame, bg='#000')
        self.webcam_frame.pack(fill=tk.X, pady=10)
        
        self.webcam_label = tk.Label(self.webcam_frame, bg='#000')
        self.webcam_label.pack(pady=10)
        
        # Frame for cat image
        self.cat_frame = tk.Frame(self.main_frame, bg='#000')
        self.cat_frame.pack(fill=tk.X, pady=10)
        
        self.cat_label = tk.Label(self.cat_frame, bg='#000')
        self.cat_label.pack(pady=10)
        
        # Start webcam
        self.cap = cv2.VideoCapture(0)
        self.webcam_active = True
        self.webcam_thread = threading.Thread(target=self.update_webcam, daemon=True)
        self.webcam_thread.start()
        
        # Schedule the cat image fade-in and laugh sound
        self.root.after(5000, self.show_cat_with_laugh)
    
    def load_captured_images(self, image_paths):
        images_container = tk.Frame(self.images_frame, bg='#000')
        images_container.pack(fill=tk.X)
        
        for i, img_path in enumerate(image_paths):
            try:
                # Create a frame for each image with label
                img_frame = tk.Frame(images_container, bg='#000')
                img_frame.grid(row=i//3, column=i%3, padx=10, pady=10)
                
                # Load and resize image
                img = Image.open(img_path) if os.path.exists(img_path) else Image.new('RGB', (200, 150), color='red')
                img = img.resize((200, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Store reference to prevent garbage collection
                self.captured_photos.append(photo)
                
                # Display image
                img_label = tk.Label(img_frame, image=photo, bg='#000')
                img_label.pack()
                
                # Add caption
                caption = tk.Label(
                    img_frame, 
                    text=f"Captured Moment {i+1}", 
                    fg="#FFFFFF", 
                    bg="#000", 
                    font=('Arial', 10)
                )
                caption.pack()
            except Exception as e:
                print(f"Error loading image {img_path}: {str(e)}")
    
    def update_webcam(self):
        while self.webcam_active:
            ret, frame = self.cap.read()
            if ret:
                # Convert to RGB and create PhotoImage
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((400, 300), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Update label
                self.webcam_label.config(image=photo)
                self.webcam_label.image = photo
            time.sleep(0.03)  # ~30 FPS
    
    def show_cat_with_laugh(self):
        try:
            # Play laugh sound
            pygame.mixer.music.load("laugh.mp3")
            pygame.mixer.music.play()
            
            # Load cat image
            if os.path.exists("cat.png"):
                cat_img = Image.open("cat.png")
                cat_img = cat_img.resize((400, 300), Image.Resampling.LANCZOS)
                
                # Fade in effect
                for alpha in range(0, 101, 5):
                    enhancer = ImageEnhance.Brightness(cat_img)
                    faded_img = enhancer.enhance(alpha/100)
                    photo = ImageTk.PhotoImage(faded_img)
                    self.cat_label.config(image=photo)
                    self.cat_label.image = photo
                    self.root.update()
                    time.sleep(0.05)
                
                # Add creepy message
                message_label = tk.Label(
                    self.cat_frame, 
                    text="I'LL BE WATCHING YOU", 
                    fg="#FF0000", 
                    bg="#000", 
                    font=('Arial', 16, 'bold')
                )
                message_label.pack(pady=10)
            else:
                print("Error: cat.png not found")
        except Exception as e:
            print(f"Error in show_cat_with_laugh: {str(e)}")
    
    def on_close(self):
        self.webcam_active = False
        if self.cap.isOpened():
            self.cap.release()
        self.root.destroy()

def main():
    parser = argparse.ArgumentParser(description='Photo Viewer')
    parser.add_argument('--images', nargs='*', help='List of image paths')
    args = parser.parse_args()
    
    root = tk.Tk()
    app = PhotoViewer(root, args.images)
    root.mainloop()

if __name__ == "__main__":
    main()