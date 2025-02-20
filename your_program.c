#include <stdio.h>
#include <string.h>

#define buffer_size 1024
#define command_size 100

int main()
{
    char buffer[buffer_size];
    char command_name[command_size];
    while(1)
    {
        //printf("$ ");
        //fflush(stdout);
        if (fgets(buffer, buffer_size, stdin) == NULL)
        break;
        if (sscanf(buffer, "%99s", command_name)==1)
            printf("%s: command not found\n", command_name);
    }
    return 0;
}
