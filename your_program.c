#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <errno.h>
#include <dirent.h>
#include <readline/readline.h>
#include <readline/history.h>
#include <ctype.h>

#define MAX_PATH 4096
#define MAX_COMMAND 1024
#define MAX_ARGS 64
#define MAX_MATCHES 256


void execute_help();

static int tab_press_count = 0;
static char last_text[MAX_COMMAND] = "";
static char *builtin[] = {"echo", "exit", "pwd", "cd", "type", "help", NULL};

static char **custom_completion(const char *, int, int);
static char *completion_generator(const char *, int);

int starts_with(const char *str, const char *prefix) {
    return strncmp(str, prefix, strlen(prefix)) == 0;
}

char **get_executables(const char *prefix, int *count) {
    static char *matches[MAX_MATCHES];
    *count = 0;

    for (int i = 0; builtin[i] != NULL; i++) {
        if (starts_with(builtin[i], prefix)) {
            matches[*count] = strdup(builtin[i]);
            (*count)++;
        }
    }

    char *path = strdup(getenv("PATH"));
    char *dir = strtok(path, ":");
    
    while (dir != NULL && *count < MAX_MATCHES) {
        DIR *d = opendir(dir);
        if (d != NULL) {
            struct dirent *entry;
            while ((entry = readdir(d)) != NULL && *count < MAX_MATCHES) {
                if (starts_with(entry->d_name, prefix)) {
                    char full_path[MAX_PATH];
                    snprintf(full_path, sizeof(full_path), "%s/%s", dir, entry->d_name);
                    if (access(full_path, X_OK) == 0) {
                        matches[*count] = strdup(entry->d_name);
                        (*count)++;
                    }
                }
            }
            closedir(d);
        }
        dir = strtok(NULL, ":");
    }
    free(path);
    return matches;
}

char *longest_common_prefix(char **strs, int count) {
    if (count == 0) return strdup("");
    
    int min_len = strlen(strs[0]);
    for (int i = 1; i < count; i++) {
        int len = strlen(strs[i]);
        if (len < min_len) min_len = len;
    }

    char *result = malloc(min_len + 1);
    for (int i = 0; i < min_len; i++) {
        char current = strs[0][i];
        for (int j = 1; j < count; j++) {
            if (strs[j][i] != current) {
                result[i] = '\0';
                return result;
            }
        }
        result[i] = current;
    }
    result[min_len] = '\0';
    return result;
}

static char **custom_completion(const char *text, int start, int end) {
    rl_attempted_completion_over = 1;
    return rl_completion_matches(text, completion_generator);
}

static char *completion_generator(const char *text, int state) {
    static int list_index;
    static int matches_count;
    static char **matches;

    if (state == 0) {
        if (strcmp(text, last_text) != 0) {
            tab_press_count = 0;
            strncpy(last_text, text, sizeof(last_text) - 1);
        }

        matches = get_executables(text, &matches_count);
        list_index = 0;

        if (matches_count > 0 && tab_press_count == 0) {
            if (matches_count > 1) {
                char *lcp = longest_common_prefix(matches, matches_count);
                if (strlen(lcp) > strlen(text)) {
                    rl_insert_text(lcp + strlen(text));
                    rl_redisplay();
                    free(lcp);
                }
                tab_press_count++;
                printf("\a");
                fflush(stdout);
                return NULL;
            }
        } else if (matches_count > 1 && tab_press_count == 1) {
            printf("\n");
            for (int i = 0; i < matches_count; i++) {
                printf("%s  ", matches[i]);
            }
            printf("\n$ %s", text);
            fflush(stdout);
            tab_press_count = 0;
            return NULL;
        }
    }

    if (list_index < matches_count) {
        char *match = matches[list_index];
        list_index++;
        char *result = malloc(strlen(match) + 2);
        strcpy(result, match);
        strcat(result, " ");
        return result;
    }

    return NULL;
}


void initialize_readline() {
    rl_attempted_completion_function = custom_completion;
    rl_completer_word_break_characters = " \t\n\"\\'`@$><=;|&{(";
}


int execute_builtin(char **args) {
    if (strcmp(args[0], "exit") == 0) {
        exit(0);
    } else if (strcmp(args[0], "help") == 0) {
        execute_help();
        return 0;
    } else if (strcmp(args[0], "echo") == 0) {
        for (int i = 1; args[i] != NULL; i++) {
            printf("%s%s", args[i], args[i + 1] ? " " : "");
        }
        printf("\n");
    } else if (strcmp(args[0], "pwd") == 0) {
        char cwd[MAX_PATH];
        if (getcwd(cwd, sizeof(cwd)) != NULL) {
            printf("%s\n", cwd);
        }
    } else if (strcmp(args[0], "cd") == 0) {
        char *dir = args[1] ? args[1] : getenv("HOME");
        if (strcmp(dir, "~") == 0) dir = getenv("HOME");
        
        if (chdir(dir) != 0) {
            switch (errno) {
                case ENOENT:
                    fprintf(stderr, "cd: %s: No such file or directory\n", dir);
                    break;
                case EACCES:
                    fprintf(stderr, "cd: %s: Permission denied\n", dir);
                    break;
                default:
                    fprintf(stderr, "cd: %s: %s\n", dir, strerror(errno));
            }
        }
    } else if (strcmp(args[0], "type") == 0) {
        if (args[1] == NULL) {
            fprintf(stderr, "type: missing argument\n");
            return 1;
        }

        for (int i = 0; builtin[i] != NULL; i++) {
            if (strcmp(args[1], builtin[i]) == 0) {
                printf("%s is a shell builtin\n", args[1]);
                return 0;
            }
        }


        char *path = strdup(getenv("PATH"));
        char *dir = strtok(path, ":");
        int found = 0;
        
        while (dir != NULL) {
            char full_path[MAX_PATH];
            snprintf(full_path, sizeof(full_path), "%s/%s", dir, args[1]);
            if (access(full_path, X_OK) == 0) {
                printf("%s is %s\n", args[1], full_path);
                found = 1;
                break;
            }
            dir = strtok(NULL, ":");
        }
        
        free(path);
        if (!found) {
            fprintf(stderr, "%s: not found\n", args[1]);
            return 1;
        }
    }
    return 0;
}

void handle_redirection(char **args, int *argc) {
    for (int i = 0; i < *argc; i++) {
        if (strcmp(args[i], ">") == 0 || strcmp(args[i], "1>") == 0) {
            freopen(args[i + 1], "w", stdout);
            args[i] = NULL;
            *argc = i;
            break;
        } else if (strcmp(args[i], ">>") == 0 || strcmp(args[i], "1>>") == 0) {
            freopen(args[i + 1], "a", stdout);
            args[i] = NULL;
            *argc = i;
            break;
        } else if (strcmp(args[i], "2>") == 0) {
            freopen(args[i + 1], "w", stderr);
            args[i] = NULL;
            *argc = i;
            break;
        } else if (strcmp(args[i], "2>>") == 0) {
            freopen(args[i + 1], "a", stderr);
            args[i] = NULL;
            *argc = i;
            break;
        }
    }
}
void display_banner() {
    printf("\033[32m");  // Green color
    printf("   _____ __         ____    __          \n");
    printf("  / ___// /_  ___  / / /   / /_  __  __ \n");
    printf("  \\__ \\/ __ \\/ _ \\/ / /   / __ \\/ / / / \n");
    printf(" ___/ / / / /  __/ / /   / /_/ / /_/ /  \n");
    printf("/____/_/ /_/\\___/_/_/   /_.___/\\__, /   \n");
    printf("                              /____/     \n");
    printf("Welcome to the custom shell! Type 'help' for commands.\n");
    printf("\033[0m");  // Reset color
}
void execute_help() {
    printf("Built-in commands:\n");
    printf("  cd [dir]     - Change directory\n");
    printf("  echo [text]  - Print text\n");
    printf("  exit         - Exit the shell\n");
    printf("  help         - Show this help\n");
    printf("  pwd          - Print working directory\n");
    printf("  type [cmd]   - Show command type/location\n");
}
int main() {
    initialize_readline();
    display_banner();
    char *input;
    
    while ((input = readline("$ ")) != NULL) {
        if (strlen(input) > 0) {
            add_history(input);
            
  
            char *args[MAX_ARGS];
            int argc = 0;
            char *token = strtok(input, " \t\n");
            
            while (token != NULL && argc < MAX_ARGS - 1) {
                args[argc++] = token;
                token = strtok(NULL, " \t\n");
            }
            args[argc] = NULL;

            if (argc > 0) {
                int is_builtin = 0;
                for (int i = 0; builtin[i] != NULL; i++) {
                    if (strcmp(args[0], builtin[i]) == 0) {
                        is_builtin = 1;
                        execute_builtin(args);
                        break;
                    }
                }

                if (!is_builtin) {
                    pid_t pid = fork();
                    if (pid == 0) {
                        handle_redirection(args, &argc);
                        execvp(args[0], args);
                        fprintf(stderr, "%s: command not found\n", args[0]);
                        exit(1);
                    } else if (pid > 0) {
                        wait(NULL);
                    } else {
                        perror("fork");
                    }
                }
            }
        }
        free(input);
    }
    printf("\n");
    return 0;
}
