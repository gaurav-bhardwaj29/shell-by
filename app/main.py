import os
import sys
import shlex
import subprocess
import readline

def get_executables(prefix):
    matches = set()
    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.exists(path) and os.path.is_dir(path):
            for file in os.listdir(path):
                full_path = os.path.join(path, file)
                if file.startswith(prefix) and os.path.is_executable(full_path) and os.path.is_file(full_path):
                    matches.add(file)
    return sorted(matches)

def completer(text, state):
    begidx = readline.get_begidx()
    endidx = readline.get_endidx()
    current_word = text[begidx:endidx]
    if begidx == 0 or text[:begidx].strip() == '':
        matches = get_executables(current_word)
        try:
            return matches[state] + " "
        except IndexError:
            return None
    return None

def handle_redirection(command_line):
    parts = shlex.split(command_line)
    if not parts:
        return None, None, None
    
    stdout_file = stderr_file = None
    stdout_mode = stderr_mode = None
    cmd_args = parts[:]

    for i, part in enumerate(parts):
        if part == ">":
            stdout_file = parts[i + 1]
            stdout_mode = "w"
            cmd_args = parts[:i]
            break
        elif part == ">>":
            stdout_file = parts[i + 1]
            stdout_mode = "a"
            cmd_args = parts[:i]
            break
        elif part == "2>":
            stderr_file = parts[i + 1]
            stderr_mode = "w"
            cmd_args = parts[:i]
            break
        elif part == "2>>":
            stderr_file = parts[i + 1]
            stderr_mode = "a"
            cmd_args = parts[:i]
            break
    
    return cmd_args, stdout_file, stderr_file, stdout_mode, stderr_mode

def main():
    builtins = {"echo", "exit", "pwd", "cd", "type"}
    HOME = os.environ.get("HOME", "/")

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set show-all-if-ambiguous Off")

    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        try:
            command_line = input().strip()
            if not command_line:
                continue

            # Parse redirection
            args, stdout_file, stderr_file, stdout_mode, stderr_mode = handle_redirection(command_line)
            if not args:
                continue

            command = args[0]

            # Builtins
            if command == "exit":
                sys.exit(0)
            elif command == "echo":
                output = " ".join(args[1:])
                sys.stdout.write(output + "\n")
                sys.stdout.flush()
            elif command == "pwd":
                sys.stdout.write(os.getcwd() + "\n")
                sys.stdout.flush()
            elif command == "cd":
                directory = args[1] if len(args) > 1 else HOME
                if directory.startswith("~"):
                    directory = os.path.join(HOME, directory[1:].lstrip("/"))
                try:
                    os.chdir(directory)
                except FileNotFoundError:
                    sys.stderr.write(f"cd: {directory}: No such file or directory\n")
                except PermissionError:
                    sys.stderr.write(f"cd: {directory}: Permission denied\n")
                sys.stderr.flush()
            elif command == "type":
                if len(args) < 2:
                    sys.stderr.write("type: missing argument\n")
                else:
                    target = args[1]
                    cmd_path = None
                    for path in os.environ["PATH"].split(os.pathsep):
                        full_path = os.path.join(path, target)
                        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                            cmd_path = full_path
                            break
                    if target in builtins:
                        sys.stdout.write(f"{target} is a shell builtin\n")
                    elif cmd_path:
                        sys.stdout.write(f"{target} is {cmd_path}\n")
                    else:
                        sys.stderr.write(f"{target}: not found\n")
                sys.stdout.flush()
            # External commands with redirection
            else:
                try:
                    stdout = subprocess.PIPE if not stdout_file else open(stdout_file, stdout_mode or "w")
                    stderr = subprocess.PIPE if not stderr_file else open(stderr_file, stderr_mode or "w")
                    result = subprocess.run(args, stdout=stdout, stderr=stderr, text=True)
                    
                    if stdout == subprocess.PIPE and result.stdout:
                        sys.stdout.write(result.stdout)
                    if stderr == subprocess.PIPE and result.stderr:
                        sys.stderr.write(result.stderr)
                    
                    if stdout != subprocess.PIPE:
                        stdout.close()
                    if stderr != subprocess.PIPE:
                        stderr.close()
                    
                    sys.stdout.flush()
                    sys.stderr.flush()
                except FileNotFoundError:
                    sys.stderr.write(f"{command}: command not found\n")
                    sys.stderr.flush()
                except Exception as e:
                    sys.stderr.write(f"Error: {e}\n")
                    sys.stderr.flush()

        except EOFError:
            sys.stdout.write("\n")
            break
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
