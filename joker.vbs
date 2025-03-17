Set WshShell = CreateObject("WScript.Shell")

Do
    WshShell.Run "python joker.py", 1, True
Loop