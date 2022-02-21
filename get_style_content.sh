#! /bin/bash
#
# 
#
# author : jclaude
# date : 2022/02/19

filename=$1

# need for sed
separator="::::::::::"

# need for grep
no_lines=$(wc -l "$filename" | cut -f1 -d' ')

cat "$filename" |\
    # take everything between the style tag
    grep -A "$no_lines" "<style.*>" | grep -B "$no_lines" "</style>" |\
    # put everything on the same line
    sed -z "s/\n/$separator/g" |\
    # get everything in between the first and last tag
    cut -f2- -d ">" | rev | cut -f2- -d "<" | rev |\
    # put the newlines back
    sed -z "s/$separator/\n/g"