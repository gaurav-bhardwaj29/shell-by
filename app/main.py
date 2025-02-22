import sys
import os
import subprocess
import shlex


def parent_dir(filepath):
    parent = os.path.dirname(filepath)
    if parent:
        os.makedirs(parent, exist_ok=True)


def find_in_path(param):
    path = os.environ.get('PATH', '')
    for directory in path.split(":"):
        executable_path = os.path.join(directory, param)
        if os.path.isfile(executable_path) and os.access(executable_path, os.X_OK):
            return executable_path
    return None


def output_error(message):
    print(message, file=sys.stderr)


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
            parts = shlex.split(command)
        except Exception as e:
            output_error(f"Error parsing command: {e}")
            continue

        if not parts:
            continue

        redir_stdout = None
        redir_stdout_append = None
        redir_stderr = None
        redir_stderr_append = None
        command_tokens = []
        i = 0
        while i < len(parts):
            token = parts[i]
            if token in (">", "1>"):
                if i + 1 >= len(parts):
                    output_error("Redirection operator without target file")
                    break
                redir_stdout = parts[i + 1]
                i += 2
                continue
            elif token in (">>", "1>>"):
                if i + 1 >= len(parts):
                    output_error("Redirection operator without target file")
                    break
                redir_stdout_append = parts[i + 1]
                i += 2
                continue
            elif token == "2>":
                if i + 1 >= len(parts):
                    output_error("Redirection operator without target file")
                    break
                redir_stderr = parts[i + 1]
                i += 2
                continue
            elif token == "2>>":
                if i + 1 >= len(parts):
                    output_error("Redirection operator without target file")
                    break
                redir_stderr_append = parts[i + 1]
                i += 2
                continue
            else:
                command_tokens.append(token)
                i += 1

        if not command_tokens:
            continue

        cmd, *args = command_tokens

        match cmd:
            case "exit":
                if args == ["0"]:
                    sys.exit(0)
            case "echo":
                result = " ".join(args)
                try:
                    if redir_stdout_append:
                        parent_dir(redir_stdout_append)
                        with open(redir_stdout_append, "a") as f:
                            f.write(result + "\n")
                    elif redir_stdout:
                        parent_dir(redir_stdout)
                        with open(redir_stdout, "w") as f:
                            f.write(result + "\n")
                    else:
                        print(result)
                except Exception as e:
                    output_error(f"Error handling output: {e}")
            case "type":
                if len(args) == 1 and args[0] in {"echo", "exit", "type", "pwd", "cd"}:
                    result = f"{args[0]} is a shell builtin"
                    try:
                        if redir_stdout_append:
                            parent_dir(redir_stdout_append)
                            with open(redir_stdout_append, "a") as f:
                                f.write(result + "\n")
                        elif redir_stdout:
                            parent_dir(redir_stdout)
                            with open(redir_stdout, "w") as f:
                                f.write(result + "\n")
                        else:
                            print(result)
                    except Exception as e:
                        output_error(f"Error handling output: {e}")
                else:
                    location = find_in_path(args[0])
                    if location:
                        result = f"{args[0]} is {location}"
                        try:
                            if redir_stdout_append:
                                parent_dir(redir_stdout_append)
                                with open(redir_stdout_append, "a") as f:
                                    f.write(result + "\n")
                            elif redir_stdout:
                                parent_dir(redir_stdout)
                                with open(redir_stdout, "w") as f:
                                    f.write(result + "\n")
                            else:
                                print(result)
                        except Exception as e:
                            output_error(f"Error handling output: {e}")
                    else:
                        output_error(f"{' '.join(args)} not found")
            case "pwd":
                result = os.getcwd()
                try:
                    if redir_stdout_append:
                        parent_dir(redir_stdout_append)
                        with open(redir_stdout_append, "a") as f:
                            f.write(result + "\n")
                    elif redir_stdout:
                        parent_dir(redir_stdout)
                        with open(redir_stdout, "w") as f:
                            f.write(result + "\n")
                    else:
                        print(result)
                except Exception as e:
                    output_error(f"Error handling output: {e}")
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
                    if os.path.isfile(arg):
                        try:
                            with open(arg, 'r') as f:
                                contents.append(f.read().strip())
                        except Exception as e:
                            output_error(f"cat: {arg}: Error reading file: {e}")
                    else:
                        output_error(f"cat: {arg}: No such file or directory")
                result = "".join(contents)
                try:
                    if redir_stdout_append:
                        parent_dir(redir_stdout_append)
                        with open(redir_stdout_append, "a") as f:
                            f.write(result)
                    elif redir_stdout:
                        parent_dir(redir_stdout)
                        with open(redir_stdout, "w") as f:
                            f.write(result)
                    else:
                        sys.stdout.write(result)
                        sys.stdout.flush()
                except Exception as e:
                    output_error(f"Error handling output: {e}")
            case _:
                executable_path = cmd if os.path.isfile(cmd) else find_in_path(cmd)
                if executable_path:
                    try:
                        result = subprocess.run(
                            [cmd, *args],
                            executable=executable_path,
                            stdout=subprocess.PIPE if redir_stdout or redir_stdout_append else None,
                            stderr=subprocess.PIPE if redir_stderr or redir_stderr_append else None,
                            text=True
                        )
                        try:
                            # Handle stdout redirection
                            if redir_stdout_append:
                                parent_dir(redir_stdout_append)
                                with open(redir_stdout_append, "a") as f:
                                    if result.stdout:
                                        f.write(result.stdout)
                            elif redir_stdout:
                                parent_dir(redir_stdout)
                                with open(redir_stdout, "w") as f:
                                    if result.stdout:
                                        f.write(result.stdout)
                            elif result.stdout:
                                sys.stdout.write(result.stdout)
                                sys.stdout.flush()

                            # Handle stderr redirection
                            if redir_stderr_append:
                                parent_dir(redir_stderr_append)
                                with open(redir_stderr_append, "a") as f:
                                    if result.stderr:
                                        f.write(result.stderr)
                            elif redir_stderr:
                                parent_dir(redir_stderr)
                                with open(redir_stderr, "w") as f:
                                    if result.stderr:
                                        f.write(result.stderr)
                            elif result.stderr:
                                sys.stderr.write(result.stderr.rstrip('\n') + '\n')
                                sys.stderr.flush()
                        except Exception as e:
                            output_error(f"Failed to handle output redirection: {e}")
                    except Exception as e:
                        output_error(f"Failed to execute {cmd}: {e}")
                else:
                    output_error(f"{cmd}: command not found")


if __name__ == "__main__":
    main()
