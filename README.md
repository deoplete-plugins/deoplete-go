# deoplete-go
Go [deoplete.nvim](https://github.com/Shougo/deoplete.nvim) source for [gocode](https://github.com/nsf/gocode) and [vim-go](https://github.com/fatih/vim-go).


## Required

### Neovim
https://github.com/neovim/neovim/

### deoplete.nvim
https://github.com/Shougo/deoplete.nvim

### gocode or vim-go
https://github.com/nsf/gocode
https://github.com/fatih/vim-go


## Install

```bash
NeoBundle 'zchee/deoplete-go'
# or
Plug 'zchee/deoplete-go'
```

## Usage
If you using the gocode, set

```vim
let g:deoplete#sources#go = 'gocode'
```

If you using the vim-go, set

```vim
let g:deoplete#sources#go = 'vim-go'
```


## Sample init.vim

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


## Settings

`deoplete` and `deoplete-go` will be source settings to `rank = 100` and `input_pattern = '[^. \t0-9]\.\w*'` set to default.  
If you want to customize that variable, insert your `init.vim` after set `runtimepath`.  
e.g. `rank` is `9999`,

```vim
call deoplete#custom#set('go', 'rank', 9999)
```

If you want to the same motion as the `omnifunc`, set

```vim
call deoplete#custom#set('go', 'min_pattern_length', 1000)
```

and available setting values,

| value                   | `deoplete.nvim` default                   | `deoplete-go` default       |
|-------------------------|-------------------------------------------|-----------------------------|
| `name`                  | -                                         | go                          |
| `mark`                  | -                                         | `[go]`                      |
| `filetype`              | all filetypes                             | go                          |
| `rank`                  | `100`                                     | -                           |
| `min_pattern_length`    | `g:deoplete#auto_completion_start_length` | -                           |
| `input-pattern`         | -                                         | `'[^. \t0-9]\.\w*'`         |
| `is_byteopts`           | `False`                                   | `True`                      |
| `matchers`              | `deoplete-filter-matcher_default`         | -                           |
| `sorters`               | `deoplete-filter-sorter_default`          | -                           |
| `converters`            | `deoplete-filter-converter_default`       | -                           |
| `get_complete_position` | `g:deoplete#keyword_patterns`             | `gocomplete#Complete(1, 0)` |
| `gather_candidates`     | -                                         | `gocomplete#Complete(1, 0)` |

See also 

```vim
:help deoplete-source-attributes
```


## Why `deoplete` also `deoplete-go` are not use `omnifunc`?
When deoplete call `omnifunc`, will block user interface a little bit.  
That is specification of `vim` also `neovim`.  
We can not call `omnifunc` asynchnously now.

If we use `deoplete` source implementation, `deoplete` can get a dictionary completion word list asynchnously.  
So, If `deoplete-go` (and other language `deoplete` source plugins) passes exactly the same as `omnifunc` dictionary word list to `deoplete`, We do not need a `omnifunc`.
The advantage of `deoplete` also `deoplete-go` is it.

See also https://github.com/zchee/deoplete-go/issues/4#issuecomment-172412821 .  

...BTW, `deoplete-go` is not implements this TODO.

> Execute `gocode` binary instead of call vim function

Perfect asynchronous will be done by implementing this.  
Please wait a little :)

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
