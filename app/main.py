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

        # Parse for redirection tokens for stdout and stderr
        redir_stdout = None
        redir_stderr = None
        i = 0
        while i < len(parts):
            if parts[i] in (">", "1>"):
                if i + 1 >= len(parts):
                    print("Redirection operator without target file", file=sys.stderr)
                    parts = parts[:i]
                    break
                redir_stdout = parts[i+1]
                del parts[i:i+2]
                continue
            elif parts[i] == "2>":
                if i + 1 >= len(parts):
                    print("Redirection operator without target file", file=sys.stderr)
                    parts = parts[:i]
                    break
                redir_stderr = parts[i+1]
                del parts[i:i+2]
                continue
            i += 1

        if not parts:
            continue

        cmd, *args = parts

        # Helper functions for output redirection
        def output_result(result):
            if redir_stdout:
                try:
                    with open(redir_stdout, "w") as f:
                        f.write(result)
                except Exception as e:
                    output_error(f"Error writing to {redir_stdout}: {e}")
            else:
                print(result)

        def output_error(msg):
            if redir_stderr:
                try:
                    # Open in append mode so that multiple errors are written together
                    with open(redir_stderr, "a") as f:
                        f.write(msg + "\n")
                except Exception as e:
                    print(f"Error writing to {redir_stderr}: {e}", file=sys.stderr)
            else:
                print(msg, file=sys.stderr)

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
                        output_error(f"{' '.join(args)} not found")
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
                        output_error(f"cd: {args[0]}: No such file or directory")
                else:
                    output_error(f"cd: {args[0]}: No such file or directory")
            case "cat":
                if not args:
                    continue
                contents = []
                for arg in args:
                    # With shlex.split, quotes are already removed.
                    if os.path.isfile(arg):
                        try:
                            with open(arg, 'r') as f:
                                contents.append(f.read().strip())
                        except Exception as e:
                            output_error(f"cat: {arg}: Error reading file: {e}")
                    else:
                        output_error(f"cat: {arg}: No such file or directory")
                result = " ".join(contents)
                output_result(result)
            case _:
                # External command: check if cmd is a file or look it up in PATH.
                executable_path = cmd if os.path.isfile(cmd) else find_in_path(cmd)
                if executable_path:
                    try:
                        out_f = open(redir_stdout, "w") if redir_stdout else None
                        err_f = open(redir_stderr, "w") if redir_stderr else None
                        subprocess.run([cmd, *args], executable=executable_path, stdout=out_f, stderr=err_f)
                    except Exception as e:
                        output_error(f"Failed to execute {cmd}: {e}")
                    finally:
                        if out_f:
                            out_f.close()
                        if err_f:
                            err_f.close()
                else:
                    output_error(f"{cmd}: command not found")

if __name__ == "__main__":
    main()
