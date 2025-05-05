import os
import tkinter

def find_tcl_tk():
    python_root = os.path.dirname(os.path.dirname(tkinter.__file__))
    possible_paths = [
        os.path.join(python_root, 'tcl', 'tcl8.6'),
        os.path.join(python_root, 'tcl', 'tk8.6'),
        os.path.join(python_root, 'DLLs', 'tcl8.6'),
        os.path.join(python_root, 'DLLs', 'tk8.6'),
        os.path.join(python_root, 'lib', 'tcl8.6'),
        os.path.join(python_root, 'lib', 'tk8.6'),
    ]
    found = []
    for path in possible_paths:
        if os.path.exists(path):
            found.append(path)
            print(f"Found: {path}")
    if not found:
        print("No Tcl/Tk directories found.")
    return found

find_tcl_tk()