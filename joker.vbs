Set WshShell = CreateObject("WScript.Shell")

' Initialized index
Dim index
index = 0

' Runs 3 times and exits for testing purposes
Do While index <= 3
    WshShell.Run "python joker.py", 1, True
    index = index+1
Loop