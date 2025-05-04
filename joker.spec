# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import tensorflow
import tkinter
import PyInstaller.config

# Find Tcl/Tk directories - more robust approach
try:
    import tkinter
    tcl_dir = os.path.dirname(tkinter.__file__)
    tcl8_dir = os.path.join(tcl_dir, 'tcl8')
    tk8_dir = os.path.join(tcl_dir, 'tk8')
    
    # Check if directories exist, otherwise try alternative paths
    if not os.path.exists(tcl8_dir):
        # Try to find tcl directory in a different location
        base_dir = os.path.dirname(os.path.dirname(tcl_dir))
        tcl8_dir = os.path.join(base_dir, 'tcl', 'tcl8.6')
        tk8_dir = os.path.join(base_dir, 'tcl', 'tk8.6')
        
        # If still not found, try another common location
        if not os.path.exists(tcl8_dir):
            import _tkinter
            tcl_root = os.path.dirname(_tkinter.__file__)
            tcl8_dir = os.path.join(tcl_root, 'tcl8.6')
            tk8_dir = os.path.join(tcl_root, 'tk8.6')
except Exception as e:
    print(f"Warning: Could not find Tcl/Tk directories: {e}")
    tcl8_dir = None
    tk8_dir = None

# Find TensorFlow directories
tf_dir = os.path.dirname(tensorflow.__file__)
tf_keras_dir = None
try:
    # Try to find keras directory
    if os.path.exists(os.path.join(tf_dir, 'keras')):
        tf_keras_dir = os.path.join(tf_dir, 'keras')
    elif hasattr(tensorflow, 'keras') and hasattr(tensorflow.keras, '__file__'):
        tf_keras_dir = os.path.dirname(tensorflow.keras.__file__)
    
    print(f"TensorFlow directory: {tf_dir}")
    print(f"TensorFlow Keras directory: {tf_keras_dir}")
except Exception as e:
    print(f"Warning: Could not find TensorFlow Keras directory: {e}")

PyInstaller.config.CONF['distpath'] = os.path.abspath('./dist')

block_cipher = None

# Prepare datas list
datas = [
    # Include resource files
    ('laugh.mp3', '.'),
    ('cat.png', '.'),
    ('photo_viewer.py', '.'),
    ('scream.mp3', '.'),
]

# Add TensorFlow data files if found
if tf_keras_dir and os.path.exists(tf_keras_dir):
    datas.append((tf_keras_dir, 'tensorflow/keras'))

# Add Tcl/Tk data files if found
if tcl8_dir and os.path.exists(tcl8_dir):
    datas.append((tcl8_dir, 'tcl8'))
if tk8_dir and os.path.exists(tk8_dir):
    datas.append((tk8_dir, 'tk8'))

a = Analysis(
    ['main.py'],  # Main entry point
    pathex=[],
    binaries=[],
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
        'pygame',
        'numpy',
        'tensorflow',
        'tensorflow.python',
        'tensorflow.python.keras',
        'tensorflow.python.keras.engine',
        'tensorflow.python.keras.layers',
        'tensorflow.python.keras.models',
        'tensorflow.python.keras.utils',
        'tensorflow.python.keras.wrappers',
        'tensorflow.python.keras.applications',
        'tensorflow.python.keras.preprocessing',
        'tensorflow.python.feature_column',
        'tensorflow.python.layers',
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
    console=True,  # Set to True to see error messages during testing
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='mp4.ico',
)




