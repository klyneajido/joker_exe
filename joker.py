import time
import os
import sys
import threading
import subprocess
import psutil
import signal

# Safe word to exit the script
SAFE_WORD = "EXITNOW"
exit_flag = threading.Event()

# Command to relaunch during development (python joker.py)
EXE_PATH = [sys.executable, os.path.abspath(__file__)]


def check_safe_word():
    while not exit_flag.is_set():
        user_input = input("\n\033[93mType 'EXITNOW' anytime to quit: \033[0m").upper().strip()
        if user_input == SAFE_WORD:
            print("\033[92mSafe word detected. Exiting gracefully...\033[0m")
            exit_flag.set()
            break

def clean_exit():
    exit_flag.set()
    print("\033[92mTerminating threads and exiting...\033[0m")
    time.sleep(1)
    pid_file = "joker.pid"
    if os.path.exists(pid_file):
        os.remove(pid_file)
    os._exit(0)

def joker_virus():
    os.system("cls" if os.name == "nt" else "clear")
    print("\033[92m" + "HA HA HA HA HA!" + "\033[0m")
    print("I'm the Joker, Robin! You fell for the leaked pic trick!")
    print("No pics here—just ME! Close me if you dare—I’ll come back!")
    print("\nRiddle #1: What's yellow and bends?")

    hearts = 3
    while hearts > 0 and not exit_flag.is_set():
        try:
            print("\033[95m" + "Still here, fool? Answer or lose a life!" + "\033[0m")
            time.sleep(3)

            clue_1 = input("\nEnter your answer (or the kill code later): ").upper().strip()

            if clue_1 == "WHYSOSERIOUS":
                print("\033[92mHA! Fine, you win! The Joker retreats!\033[0m")
                clean_exit()
            if clue_1 == "BANANA":
                print("Correct! Check www.jokerquest2.com for the next riddle!")
                clean_exit()
            else:
                hearts -= 1
                print(f"Wrong! Lives left: {hearts}")

        except KeyboardInterrupt:
            print("\n\033[95mNice try, but you can’t escape that easily!\033[0m")
            continue

    if hearts == 0 and not exit_flag.is_set():
        print("\033[95mGame over, fool! I’m still here! HA HA!\033[0m")

def is_process_alive(pid):
    try:
        return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
    except psutil.NoSuchProcess:
        return False

def watchdog(main_pid):
    """Watchdog process to relaunch the main script if it dies."""
    while True:
        if not is_process_alive(main_pid):
            print("Main process died! Relaunching...")
            subprocess.Popen(EXE_PATH, creationflags=subprocess.DETACHED_PROCESS)
            sys.exit(0)
        time.sleep(1)

def main():
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    pid_file = "joker.pid"
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            old_pid = int(f.read().strip())
        if is_process_alive(old_pid):
            print("Joker is already running! I’ll let it be...")
            sys.exit(1)
        else:
            print("Found an old PID file. Cleaning up...")
            os.remove(pid_file)

    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    # Spawn watchdog process
    if len(sys.argv) == 1:  # Main mode
        watchdog_process = subprocess.Popen(EXE_PATH + ["watchdog", str(os.getpid())], 
                                           creationflags=subprocess.DETACHED_PROCESS)
        print(f"Watchdog spawned with PID: {watchdog_process.pid}")

    # Check if we're the watchdog
    if len(sys.argv) > 1 and sys.argv[1] == "watchdog":
        main_pid = int(sys.argv[2])
        watchdog(main_pid)
        sys.exit(0)

    # Main script logic
    try:
        safe_word_thread = threading.Thread(target=check_safe_word, daemon=True)
        safe_word_thread.start()

        joker_virus()

    except Exception as e:
        print(f"Error occurred: {e}")
        print("I’m coming back in 2 seconds...")
        time.sleep(2)
        subprocess.Popen(EXE_PATH, creationflags=subprocess.DETACHED_PROCESS)

    finally:
        if os.path.exists(pid_file):
            os.remove(pid_file)

if __name__ == "__main__":
    main()