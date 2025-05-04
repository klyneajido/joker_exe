import sys
import os
from terminal import PowerShellTerminal

def main():
    try:
        terminal = PowerShellTerminal()
        terminal.run()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if os.path.exists("joker.pid"):
            os.remove("joker.pid")
        sys.exit(1)

if __name__ == "__main__":
    main()