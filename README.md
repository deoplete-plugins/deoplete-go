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
" to point neovim to a specific python 3 interpreter
let g:python3_host_prog  = '/path/to/python3'

" deoplete config
let g:deoplete#enable_at_startup = 1
let g:deoplete#auto_completion_start_length = 1
let g:deoplete#sources#go = 'vim-go'
let g:deoplete#ignore_sources = {}
let g:deoplete#ignore_sources.go = ['omni']
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
