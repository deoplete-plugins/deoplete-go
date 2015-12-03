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
let g:deoplete#auto_completion_start_length = 0
let g:deoplete#sources#go = 'vim-go'
```
