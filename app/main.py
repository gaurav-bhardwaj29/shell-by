import sys
import os
import subprocess
import shlex  # for proper parsing of quoted strings

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

        try:
            command = input().strip()
        except EOFError:
            break

        if not command:
            continue

        try:
            # Use shlex.split to properly handle quotes and spaces
            parts = shlex.split(command)
        except Exception as e:
            print(f"Error parsing command: {e}")
            continue

        if not parts:
            continue

        # Check for redirection operator: '>' or '1>'
        redir_file = None
        for i, token in enumerate(parts):
            if token in (">", "1>"):
                if i + 1 >= len(parts):
                    print("Redirection operator without target file", file=sys.stderr)
                    parts = parts[:i]
                    break
                redir_file = parts[i + 1]
                parts = parts[:i]  # command tokens are before the redirection operator
                break

        if not parts:
            continue

        cmd, *args = parts

        # Helper function: output to file if redirection is active, otherwise to stdout.
        def output_result(result):
            if redir_file:
                try:
                    with open(redir_file, "w") as f:
                        f.write(result)
                except Exception as e:
                    print(f"Error writing to {redir_file}: {e}", file=sys.stderr)
            else:
                print(result)

        match cmd:
            case "exit":
                if args == ["0"]:
                    exit(0)
            case "echo":
                result = " ".join(args)
                output_result(result)
            case "type":
                if len(args) == 1 and args[0] in {"echo", "exit", "type", "pwd", "cd", "cat"}:
                    result = f"{args[0]} is a shell builtin"
                    output_result(result)
                else:
                    location = find_in_path(args[0])
                    if location:
                        result = f"{args[0]} is {location}"
                        output_result(result)
                    else:
                        result = f"{' '.join(args)} not found"
                        output_result(result)
            case "pwd":
                result = os.getcwd()
                output_result(result)
            case "cd":
                if not args:
                    continue
                target = os.path.abspath(os.path.expanduser(args[0]))
                if os.path.isdir(target):
                    try:
                        os.chdir(target)
                    except Exception as e:
                        print(f"cd: {args[0]}: No such file or directory", file=sys.stderr)
                else:
                    print(f"cd: {args[0]}: No such file or directory", file=sys.stderr)
            case "cat":
                if not args:
                    continue
                contents = []
                for arg in args:
                    # With shlex.split quotes are already removed.
                    if os.path.isfile(arg):
                        try:
                            with open(arg, 'r') as f:
                                contents.append(f.read().strip())
                        except Exception as e:
                            print(f"cat: {arg}: Error reading file: {e}", file=sys.stderr)
                    else:
                        print(f"cat: {arg}: No such file or directory", file=sys.stderr)
                result = "".join(contents)
                output_result(result)
            case _:
                # For non-builtins, check if cmd is a file or in PATH.
                executable_path = cmd if os.path.isfile(cmd) else find_in_path(cmd)
                if executable_path:
                    try:
                        if redir_file:
                            with open(redir_file, "w") as f:
                                subprocess.run([cmd, *args], executable=executable_path, stdout=f)
                        else:
                            subprocess.run([cmd, *args], executable=executable_path)
                    except Exception as e:
                        print(f"Failed to execute {cmd}: {e}", file=sys.stderr)
                else:
                    print(f"{cmd}: command not found", file=sys.stderr)

if __name__ == "__main__":
    main()
