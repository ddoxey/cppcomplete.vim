#!/bin/bash

FTDETECT="vim/ftdetect/cpp.vim"
SYNTAX="vim/syntax/cpp.vim"
CPPCOMPLETE="bin/cppcomplete.py"


function here()
{
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
}


function install()
{
    for d in "${HOME}/.vim/ftdetect" "${HOME}/.vim/syntax" "${HOME}/bin"
    do
        test -e "$d" || mkdir -p "$d" || return 1
    done

    for f in "$HOME/.$FTDETECT" "$HOME/.$SYNTAX" "$HOME/$CPPCOMPLETE"
    do
        test -e "$f" && rm -f "$f"
    done

    cd $(here)

    cp -f $FTDETECT    "$HOME/.$FTDETECT"   || return 1
    cp -f $SYNTAX      "$HOME/.$SYNTAX"     || return 1
    cp -f $CPPCOMPLETE "$HOME/$CPPCOMPLETE" || return 1

    chmod +x "$HOME/$CPPCOMPLETE" || return 1

    echo "Installed:"
    for f in "$HOME/.$FTDETECT" "$HOME/.$SYNTAX" "$HOME/$CPPCOMPLETE"
    do
        test -e "$f" && echo "  $f"
    done
}

install "$@"
