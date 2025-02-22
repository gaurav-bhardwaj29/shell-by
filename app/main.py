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

def ensure_parent_directory(filepath):
    """Ensure that the parent directory of the given file exists."""
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)

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
            # Use shlex.split to properly handle quotes and spaces.
            parts = shlex.split(command)
        except Exception as e:
            print(f"Error parsing command: {e}", file=sys.stderr)
            continue

        if not parts:
            continue

        # Parse redirection tokens.
        # Supported:
        # stdout: ">" or "1>"
        # stderr: "2>"
        redir_stdout = None
        redir_stderr = None
        command_tokens = []
        i = 0
        while i < len(parts):
            token = parts[i]
            if token in (">", "1>"):
                if i + 1 >= len(parts):
                    print("Redirection operator without target file", file=sys.stderr)
                    break
                redir_stdout = parts[i+1]
                i += 2
                continue
            elif token == "2>":
                if i + 1 >= len(parts):
                    print("Redirection operator without target file", file=sys.stderr)
                    break
                redir_stderr = parts[i+1]
                i += 2
                continue
            else:
                command_tokens.append(token)
                i += 1

        if not command_tokens:
            continue

        cmd, *args = command_tokens

        # Helper functions for output and error redirection.
        def output_result(result):
            if redir_stdout:
                try:
                    ensure_parent_directory(redir_stdout)
                    with open(redir_stdout, "w") as f:
                        f.write(result)
                except Exception as e:
                    print(f"Error writing to {redir_stdout}: {e}", file=sys.stderr)
            elif redir_stderr:
                # When only stderr redirection is specified, print to terminal
                # and also write to the stderr target.
                print(result)
                try:
                    ensure_parent_directory(redir_stderr)
                    with open(redir_stderr, "w") as f:
                        f.write(result)
                except Exception as e:
                    print(f"Error writing to {redir_stderr}: {e}", file=sys.stderr)
            else:
                print(result)

        def output_error(message):
            if redir_stderr:
                try:
                    ensure_parent_directory(redir_stderr)
                    with open(redir_stderr, "w") as f:
                        f.write(message)
                except Exception as e:
                    print(f"Error writing to {redir_stderr}: {e}", file=sys.stderr)
            else:
                print(message, file=sys.stderr)

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
                    # With shlex.split the quotes are already removed.
                    if os.path.isfile(arg):
                        try:
                            with open(arg, 'r') as f:
                                contents.append(f.read().strip())
                        except Exception as e:
                            output_error(f"cat: {arg}: Error reading file: {e}")
                    else:
                        output_error(f"cat: {arg}: No such file or directory")
                output_result(" ".join(contents))
            case _:
                # For external commands, check if cmd is a file or in PATH.
                executable_path = cmd if os.path.isfile(cmd) else find_in_path(cmd)
                if executable_path:
                    stdout_file = None
                    stderr_file = None
                    try:
                        if redir_stdout:
                            ensure_parent_directory(redir_stdout)
                            stdout_file = open(redir_stdout, "w")
                        if redir_stderr:
                            ensure_parent_directory(redir_stderr)
                            stderr_file = open(redir_stderr, "w")
                        subprocess.run([cmd, *args], executable=executable_path,
                                       stdout=stdout_file, stderr=stderr_file)
                    except Exception as e:
                        output_error(f"Failed to execute {cmd}: {e}")
                    finally:
                        if stdout_file is not None:
                            stdout_file.close()
                        if stderr_file is not None:
                            stderr_file.close()
                else:
                    output_error(f"{cmd}: command not found")

if __name__ == "__main__":
    main()
