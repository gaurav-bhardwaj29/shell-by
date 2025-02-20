import sys


def main():
    while True:
    # Uncomment this block to pass the first stage
        sys.stdout.write("$ ")

    # Wait for user input
        command , *args = input().split(" ")
        match command:
            case "exit":
                break
            case "echo":
                print(" ".join(args))
            case "type":
                if(command == "echo" or command == "exit" or command == "type")
                sys.stdout.write(f"{command}: command is a builtin\n")
            case default:
                sys.stdout.write(f"{command}: not found\n")
    
    return
     
if __name__ == "__main__":
    main()
