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
                if args.startswith["'"] and args.endswith["'"]
                    print(args[6:-1])
                else:
                # Process each argument separately, preserving spaces within quotes
                    result = ""
                    i = 0
                    while i < len(args):
                        arg = args[i]
                        if arg.startswith("'") and arg.endswith("'"):
                            # Remove quotes and preserve internal content
                            result += arg[1:-1]
                        else:
                            # Handle case where quotes might be adjacent
                            result += arg.strip("'")
                        i += 1
                    print(result)
            case "type":
                if len(args) == 1 and args[0] in {"echo", "exit", "type", "pwd", "cd", "cat"}:
                    print(f"{args[0]} is a shell builtin")
                else:
                    location = find_in_path(args[0])
                    if location:
                        print(f"{args[0]} is {location}")
                    else:
                        print(f"{' '.join(args)} not found")
            case "pwd":
                print(f"{os.getcwd()}")
            case "cd":
                if not args:
                    continue
                target = os.path.abspath(os.path.expanduser(args[0]))
                if os.path.isdir(target):
                    try:
                        os.chdir(target)
                    except Exception as e:
                        print(f"cd: {args[0]}: No such file or directory")
                else:
                    print(f"cd: {args[0]}: No such file or directory")
            case "cat":
                if not args:
                    continue
                try:
                    contents = []
                    for arg in args:
                        file = arg[1:-1] if arg.startswith("'") and arg.endswith("'") else arg
                        if os.path.isfile(file):
                            with open(file, 'r') as f:
                                contents.append(f.read().strip())
                        else:
                            print(f"cat: {arg}: No such file or directory")
                            break
                    else:
                        print(" ".join(contents))
                except Exception as e:
                    print(f"cat: Error reading files: {e}")
            
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
