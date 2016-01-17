deoplete-go
=======
Go deoplete source for gocode and vim-go.

Install:
--------

```bash
NeoBundle 'zchee/deoplete-go'
# or
Plug 'zchee/deoplete-go'
```

Usage:
------
If you using the gocode, set

```vim
let g:deoplete#sources#go = 'gocode'
```

If you using the vim-go, set

```vim
let g:deoplete#sources#go = 'vim-go'
```

Sample init.vim:
----------------

```vim
" neocomplete like
" https://github.com/Shougo/deoplete.nvim/blob/master/doc/deoplete.txt#L594-L599
set completeopt+=noinsert

" Disable auto selection
set completeopt+=noselect

" for neovim python-client
let g:python3_host_prog  = '/path/to/python3'

" deoplete config
let g:deoplete#enable_at_startup = 1
let g:deoplete#sources#go = 'vim-go'
```

`deoplete` also `deoplete-go` will be `min_pattern_length = 0` and `rank = 100` set to default.  
If you want to customize that variable, insert your `init.vim` after set `runtimepath`.  
e.g. `rank` is `9999`, `min_pattern_length` is `0`,

```vim
call deoplete#custom#set('go', 'rank', 9999)
call deoplete#custom#set('go', 'min_pattern_length', 0)
```

Todo:
-----
- [ ] Execute `gocode` binary instead of call vim function
- [ ] Get and parse completion list of json format. such as `ycm`
- [ ] Support Go stdlib package `import "***"` name completion
 - Retain the static api text? or parse?
- [ ] When there is no candidate infomation, deoplete will cause an error
- [ ] Support fizzy matching
- [ ] Parse included cgo (C,C++ language) headers
 - `ctags` will be blocking deoplete
