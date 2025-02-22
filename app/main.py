import sys
from os import chdir, environ, getcwd, path
import shlex
from contextlib import redirect_stdout, redirect_stderr
from subprocess import run, PIPE
all_builtin_cmd = ["exit", "echo", "type", "pwd", "cd"]
def main():
    sys.stdout.write("$ ")
    # Wait for user input
    cmd = input()
    match shlex.split(cmd):
        case [*run_cmd, ">>", file] | [*run_cmd, "1>>", file]:
            with open(file, "a") as out_file:
                with redirect_stdout(out_file):
                    handle_cmd(" ".join(run_cmd))
        case [*run_cmd, ">", file] | [*run_cmd, "1>", file]:
            with open(file, "w") as out_file:
                with redirect_stdout(out_file):
                    handle_cmd(" ".join(run_cmd))
        case [*run_cmd, "2>>", file]:
            with open(file, "a") as err_file:
                with redirect_stderr(err_file):
                    handle_cmd(" ".join(run_cmd))
        case [*run_cmd, "2>", file]:
            with open(file, "w") as err_file:
                with redirect_stderr(err_file):
                    handle_cmd(" ".join(run_cmd))
        case _:
            handle_cmd(cmd)
    main()
def handle_cmd(cmd):
    match shlex.split(cmd):
        case ["exit", "0"]:
            sys.exit(0)
        case ["echo", *args]:
            print(*args)
        case ["type", arg]:
            print(type_cmd(arg)[1])
        case ["pwd"]:
            print(getcwd())
        case ["cd", arg]:
            cd_cmd(arg)
        case [found_cmd, *args] if type_cmd(found_cmd)[0]:
            process = run(shlex.split(cmd), stdout=PIPE, stderr=PIPE, text=True)
            print(process.stdout, end="")
            if process.stderr:
                print(process.stderr, file=sys.stderr, end="")
        case [found_cmd] if type_cmd(found_cmd)[0]:
            process = run(shlex.split(cmd), stdout=PIPE, stderr=PIPE, text=True)
            print(process.stdout, end="")
            if process.stderr:
                print(process.stderr, file=sys.stderr, end="")
        case _:
            print(f"{cmd}: command not found", file=sys.stderr)
def type_cmd(cmd):
    if cmd in all_builtin_cmd:
        return False, f"{cmd} is a shell builtin"
    PATH_ENV = environ["PATH"].split(":")
    for path_dir in PATH_ENV:
        file_path = path.join(path_dir, cmd)
        if path.isfile(file_path):
            return True, f"{cmd} is {file_path}"
    return False, f"{cmd}: not found"
def cd_cmd(arg):
    try:
        chdir(path.expanduser(arg))
    except OSError:
        print(f"cd: {arg}: No such file or directory", file=sys.stderr)
if __name__ == "__main__":
    main()
