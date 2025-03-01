import os
import sys
import shlex
import subprocess
import readline

builtin = ["echo", "exit", "pwd", "cd", "type"]
tab_press_count=0
last_text=""
def get_executables(prefix):
    matches=set()
    for cmd in builtin:
        if cmd.startswith(prefix):
            matches.add(cmd)
    # custom executables autocompletion
    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.isdir(path):
            for file in os.listdir(path):
                full_path=os.path.join(path, file)
                if file.startswith(prefix) and os.access(full_path, os.X_OK):
                    matches.add(file)
    return sorted(matches)


def longest_common_prefix(strs):
    if not strs:
        return ""
    shortest = min(strs, key=len)
    for i, char in enumerate(shortest):
        for other in strs:
            if other[i]!=char:
                return shortest[:i]
    return shortest

def completer(text, state):
    global tab_press_count, last_text
    if text != last_text:
        tab_press_count=0
        last_text=text
    matches = get_executables(text)
    if not matches:
        return None
        
    if tab_press_count==0:
        
        if len(matches)>1:
            lcp = longest_common_prefix(matches)
            if lcp!=text:
                readline.insert_text(lcp[len(text):])
                readline.redisplay()
                last_text = lcp
            tab_press_count+=1
            sys.stdout.write("\a")
            sys.stdout.flush()
            return None
        elif len(matches) == 1:
            completed = matches[0] + " "
            readline.insert_text(completed[len(text):])
            readline.redisplay()
            return None
    elif state == 0 and tab_press_count == 1:
        if len(matches)>1:
            print("\n"+"  ".join(matches))
            sys.stdout.write(f"$ {text}")
            sys.stdout.flush()
            tab_press_count=0
            return None
    return matches[state]+ " " if state<len(matches) else None

def main():
    PATH = os.environ.get('PATH')
    HOME = os.environ.get('HOME')
    
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        
        try:
            command_line = input().strip()
            if not command_line:
                continue
                
            # stderr redirection (2>>)
            
            if "2>>" in command_line:
                parts = shlex.split(command_line)
                split_index = parts.index("2>>")
                command_args = parts[:split_index]
                error_file = parts[split_index+1]
                
                with open(error_file, "a") as f:
                    result = subprocess.run(command_args, stdout=subprocess.PIPE, stderr=f, text=True)
                if result.stdout:
                    sys.stdout.write(result.stdout)
                    sys.stdout.flush()
                readline.set_pre_input_hook(lambda: readline.insert_text(""))
                continue
                
            
            # stdout redirection (>>) or (1>>)
            
            if ">>" in command_line or "1>>" in command_line:
                parts = shlex.split(command_line)
                if ">>" in parts:
                    split_index = parts.index(">>")
                    
                else:
                    split_index = parts.index("1>>")
                    
                command_args = parts[:split_index]
                output_file = parts[split_index+1]
                with open(output_file, "a") as f:
                    result = subprocess.run(command_args, stdout = f, stderr = subprocess.PIPE, text = True)
                
                if result.stderr:
                    sys.stderr.write(result.stderr)
                    sys.stdout.flush()
                continue
                
            # stderr redirection (2>)
            
            if "2>" in command_line:
                parts = shlex.split(command_line)
                if "2>" in parts:
                    split_index = parts.index("2>")
                command_args = parts[:split_index]
                output_file = parts[split_index+1]
                with open(output_file, "a") as f:
                    result = subprocess.run(command_args, stdout = subprocess.PIPE, stderr = f, text = True)
                    
                if result.stdout:
                    sys.stdout.write(result.stdout)
                    sys.stdout.flush()
                continue
                
            # stdout redirection (1>) or (>)
            
            if ">" in command_line or "1>" in command_line:
                parts = shlex.split(command_line)
                if ">" in parts:
                    split_index = parts.index(">")
                else:
                    split_index = parts.index("1>")
                    
                command_args = parts[:split_index]
                output_file = parts[split_index+1]
                
                with open(output_file, "w") as f:
                    result = subprocess.run(command_args, stdout=f, stderr=subprocess.PIPE, text = True
                                            )
                if result.stderr:
                    sys.stderr.write(result.stderr)
                    sys.stderr.flush()
                continue
            args = shlex.split(command_line)
            command = args[0]
            
            if command == "exit":
                sys.exit(0)
            elif command == "echo":
                output = " ".join(args[1:])
                sys.stdout.write(output + '\n')
                sys.stdout.flush()
                
            elif command == "pwd":
                sys.stdout.write(os.getcwd() + '\n')
                sys.stdout.flush()
            elif command == "cd":
                directory = args[1] if len(args)>1 else HOME
                
                if directory == "~":
                    directory = HOME
                try:
                    os.chdir(directory)
                except FileNotFoundError:
                    sys.stderr.write(f"cd: {directory}: No such file or directory\n")
                except PermissionError:
                    sys.stderr.write(f"cd: {directory}: Permission denied\n")
                except Exception as e:
                    sys.stderr.write(f"cd: {directory}: {str(e)}\n")
                sys.stdout.flush()
                
            elif command == "type":
                if len(args) <2:
                    sys.stderr.write("type: missing argument\n")
                else:
                    new_command = args[1]
                    cmd_path = None
                    
                    for path in PATH.split(os.pathsep):
                        full_path = os.path.join(path, new_command)
                        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                            cmd_path = full_path
                            break
                    if new_command in builtin:
                        sys.stdout.write(f"{new_command} is a shell builtin\n")
                    elif cmd_path:
                        sys.stdout.write(f"{new_command} is {cmd_path}\n")
                    else:
                        sys.stderr.write(f"{new_command}: not found\n")
                sys.stdout.flush()
            
            # Handle external commands
            else:
                cmd_path = None
                for path in PATH.split(os.pathsep):
                    full_path = os.path.join(path, command)
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        cmd_path = full_path
                        break
                if cmd_path:
                    try:
                        result = subprocess.run(args, capture_output=True, text=True)
                        
                        sys.stdout.write(result.stdout)
                        sys.stderr.write(result.stderr)
                    except Exception as e:
                        sys.stderr.write(f"Error executing command: {e}\n")
                else:
                    sys.stderr.write(f"{command}: command not found\n")
                sys.stdout.flush()
            readline.set_pre_input_hook(lambda: readline.insert_text(""))
        except EOFError:
            sys.stdout.write("\n")
            break
            
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stdout.flush()
            
            
if __name__ == "__main__":
    main()
    
                        
                            
            
                
                
