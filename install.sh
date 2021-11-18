#!/bin/bash

FTDETECT="vim/ftdetect/cpp.vim"
SYNTAX="vim/syntax/cpp.vim"
CPPCOMPLETE="bin/cppcomplete.py"


function here()
{
    echo "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
}


function usage()
{
    echo "USAGE: $(basename "$0") [-s|-u]"            >&2
    echo "  -s : Install with symlinks to repo files" >&2
    echo "  -u : Uninstall"                           >&2
}


function install()
{
    local symlinks=$1

    for d in "${HOME}/bin" "${HOME}/.vim/syntax" "${HOME}/.vim/ftdetect"
    do
        test -e "$d" || mkdir -p "$d" || return 1
    done

    for f in "$HOME/.$SYNTAX" "$HOME/.$FTDETECT" "$HOME/$CPPCOMPLETE"
    do
        test -e "$f" && rm -f "$f"
    done

    local path="$(here)"

    cd "$path"

    chmod +x "$CPPCOMPLETE" || return 1

    if [[ -n $symlinks ]]
    then
        ln -sf "$path/$SYNTAX"      "$HOME/.$SYNTAX"     || return 1
        ln -sf "$path/$FTDETECT"    "$HOME/.$FTDETECT"   || return 1
        ln -sf "$path/$CPPCOMPLETE" "$HOME/$CPPCOMPLETE" || return 1
    else
        cp -f $SYNTAX      "$HOME/.$SYNTAX"     || return 1
        cp -f $FTDETECT    "$HOME/.$FTDETECT"   || return 1
        cp -f $CPPCOMPLETE "$HOME/$CPPCOMPLETE" || return 1
    fi

    echo "Installed:"
    for f in "$HOME/.$SYNTAX" "$HOME/.$FTDETECT" "$HOME/$CPPCOMPLETE"
    do
        test -e "$f" && echo "  $f"
    done
}


function uninstall()
{
    for f in "$HOME/.$SYNTAX" "$HOME/.$FTDETECT" "$HOME/$CPPCOMPLETE"
    do
        if [[ -e "$f" ]]
        then
            local d="$(dirname "$f")"

            rm -f "$f" || continue    && echo "removed: $f"
            rmdir -p "$d" 2>/dev/null && echo "removed: $d"
        fi
    done
}


function run()
{
    if [[ $# -gt 0 ]]
    then
        if [ $# -ne 1 ]; then usage && return 1; fi
        case $1 in
            '-s')
                local symlinks=true
            ;;
            '-u')
                local uninstall=true
            ;;
            *)
                usage && return 1
            ;;
        esac
    fi

    if [[ -n $uninstall ]]
    then
        uninstall
    else
        install $symlinks
    fi
}


run "$@"
