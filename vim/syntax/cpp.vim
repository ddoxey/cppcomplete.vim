let s:cppsearch = $HOME . "/bin/cppcomplete.py"

function! CompleteCPP(findstart, base)
    if a:findstart
        let line = getline('.')
        let start = col('.') - 1
        " locate the start of the word
        while start > 0 && match(line[start - 1], '[A-Za-z0-9_.]') == 0
            let start -= 1
        endwhile
        return start
    else
        let s:filename = expand('%')
        let s:hits = system(s:cppsearch . " '" . s:filename . "' '" . a:base . "'")
        return split(s:hits)
    endif
endfun

setlocal completefunc=CompleteCPP
