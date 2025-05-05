#!/usr/bin/env python3
import os
import sys
import shutil
import cv2
import site

def main():
    print("Preparing build environment...")
    
    # Create build directory
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_resources')
    os.makedirs(build_dir, exist_ok=True)
    
    # Copy OpenCV Haar cascade files
    print("Copying OpenCV Haar cascade files...")
    opencv_dir = os.path.dirname(cv2.__file__)
    opencv_data_dir = os.path.join(opencv_dir, 'data')
    
    if os.path.exists(opencv_data_dir):
        # Create target directory
        target_dir = os.path.join(build_dir, 'cv2', 'data')
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy all haarcascade files
        for file in os.listdir(opencv_data_dir):
            if file.startswith('haarcascade_'):
                src = os.path.join(opencv_data_dir, file)
                dst = os.path.join(target_dir, file)
                print(f"Copying {src} to {dst}")
                shutil.copy2(src, dst)
    else:
        print(f"WARNING: OpenCV data directory not found at {opencv_data_dir}")
        # Try to find it in alternative locations
        found = False
        for site_pkg in site.getsitepackages():
            alt_path = os.path.join(site_pkg, 'cv2', 'data')
            if os.path.exists(alt_path):
                print(f"Found alternative OpenCV data directory: {alt_path}")
                # Create target directory
                target_dir = os.path.join(build_dir, 'cv2', 'data')
                os.makedirs(target_dir, exist_ok=True)
                
                # Copy all haarcascade files
                for file in os.listdir(alt_path):
                    if file.startswith('haarcascade_'):
                        src = os.path.join(alt_path, file)
                        dst = os.path.join(target_dir, file)
                        print(f"Copying {src} to {dst}")
                        shutil.copy2(src, dst)
                found = True
                break
        
        if not found:
            print("ERROR: Could not find OpenCV data directory. Emotion detection may not work.")
    
    print("Build preparation complete!")

if __name__ == "__main__":
    main()