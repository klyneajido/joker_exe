# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import tensorflow
import cv2
import PyInstaller.config

PyInstaller.config.CONF['distpath'] = os.path.abspath('./dist')

block_cipher = None

# Get OpenCV path and binary
opencv_dir = os.path.dirname(cv2.__file__)
binaries = []
# Add OpenCV binary explicitly to avoid extraction issues
binaries.append((os.path.join(opencv_dir, 'cv2.pyd'), '.'))

# Prepare datas list
datas = [
    ('laugh.mp3', '.'),
    ('cat.png', '.'),
    ('photo_viewer.py', '.'),
    ('scream.mp3', '.'),
    ('weights/facial_expression_model_weights.h5', 'weights'),  # Specific model file
    ('weights/*', 'weights'),  # Other DeepFace weights
    (os.path.join(opencv_dir, 'data'), 'cv2/data'),  # OpenCV data
]

# Add TensorFlow and Tcl/Tk data
tf_dir = os.path.dirname(tensorflow.__file__)
tf_keras_dir = os.path.join(tf_dir, 'keras') if os.path.exists(os.path.join(tf_dir, 'keras')) else None
if tf_keras_dir:
    datas.append((tf_keras_dir, 'tensorflow/keras'))

# Fix Tcl/Tk path detection
try:
    import tkinter
    import os
    tcl_dir = os.path.dirname(tkinter.__file__)
    tcl8_dir = os.path.join(tcl_dir, 'tcl8')
    tk8_dir = os.path.join(tcl_dir, 'tk8')
    if not os.path.exists(tcl8_dir):
        import _tkinter
        tcl_tk_dir = os.path.dirname(_tkinter.__file__)
        tcl8_dir = os.path.join(tcl_tk_dir, 'tcl8.6')
        tk8_dir = os.path.join(tcl_tk_dir, 'tk8.6')
    
    # If still not found, try Python's DLLs directory
    if not os.path.exists(tcl8_dir):
        python_dir = os.path.dirname(os.path.dirname(tcl_dir))
        tcl8_dir = os.path.join(python_dir, 'tcl', 'tcl8.6')
        tk8_dir = os.path.join(python_dir, 'tcl', 'tk8.6')
    
    if os.path.exists(tcl8_dir) and os.path.exists(tk8_dir):
        datas.append((tcl8_dir, 'tcl8.6'))
        datas.append((tk8_dir, 'tk8.6'))
    else:
        print(f"Warning: Could not find Tcl/Tk directories")
except Exception as e:
    print(f"Warning: Could not find Tcl/Tk directories: {e}")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,  # Add the binaries we defined above
    datas=datas,
    hiddenimports=[
        'PIL', 
        'PIL._imagingtk', 
        'PIL._tkinter_finder', 
        'winsound', 
        'cv2', 
        'deepface',
        'deepface.commons',
        'deepface.detectors',
        'deepface.detectors.opencv',
        'deepface.detectors.ssd',
        'deepface.detectors.mtcnn',
        'deepface.detectors.retinaface',
        'deepface.detectors.mediapipe',
        'deepface.detectors.yolov8',
        'deepface.models',
        'deepface.models.Age',
        'deepface.models.Gender',
        'deepface.models.Race',
        'deepface.models.Emotion',
        'deepface.models.Facial_Attributes',
        'deepface.basemodels',
        'deepface.extendedmodels',
        'deepface.commons.functions',
        'deepface.commons.distance',
        'pygame',
        'numpy',
        'tensorflow',
        'pandas',
        'gdown',
        'tqdm',
        'requests',
        'user_stats',
        'story_manager',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Terminal_Enigma',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='mp4.ico',
)




