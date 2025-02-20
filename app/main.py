import sys
import os
import subprocess


def find_in_path(param):
    path = os.environ['PATH']
    for directory in path.split(":"):
        executable_path = os.path.join(directory, param)
        if os.path.isfile(executable_path) and os.access(executable_path, os.X_OK):
            return executable_path
    return None


def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        command = input().strip()

        if not command:
            continue

        parts = command.split()
        if not parts:
            continue

        cmd, *args = parts

        match cmd:
            case "exit":
                if args == ["0"]:
                    exit(0)
            case "echo":
                print(" ".join(args))
            case "type":
                if len(args) == 1 and args[0] in {"echo", "exit", "type"}:
                    print(f"${args[0]} is a shell builtin")
                else:
                    location = find_in_path(args[0])
                    if location:
                        print(f"${args[0]} is {location}")
                    else:
                        print(f"{' '.join(args)} not found")
            case _:
                # Check if cmd is a path to a file or look it up in PATH
                executable_path = cmd if os.path.isfile(cmd) else find_in_path(cmd)

                if executable_path:
                    try:
                        subprocess.run([cmd, *args], executable=executable_path)
                    except Exception as e:
                        print(f"Failed to execute {cmd}: {e}")
                else:
                    print(f"{cmd}: command not found")


if __name__ == "__main__":
    main()
