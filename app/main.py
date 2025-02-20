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
            case default:
                sys.stdout.write(f"{command}: command not found\n")
    
    return
     
if __name__ == "__main__":
    main()
