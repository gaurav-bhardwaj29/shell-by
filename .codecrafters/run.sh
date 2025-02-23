#!/bin/sh
#
# This script is used to run your program on CodeCrafters
# 
# This runs after .codecrafters/compile.sh
#
# Learn more: https://codecrafters.io/program-interface

# Exit early if any commands fail
set -e

# Compile the C program
# gcc -o your_program your_program.c -lreadline

# Execute the compiled program
# exec ./your_program "$@"
exec pipenv run python3 -u -m app.main "$@"
