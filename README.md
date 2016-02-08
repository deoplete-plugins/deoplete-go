# deoplete-go
Go [deoplete.nvim](https://github.com/Shougo/deoplete.nvim) source for [gocode](https://github.com/nsf/gocode).


## Required

### Neovim
https://github.com/neovim/neovim/

### deoplete.nvim
https://github.com/Shougo/deoplete.nvim

### gocode
https://github.com/nsf/gocode


## Install

```vim
NeoBundle 'zchee/deoplete-go', {'build': {'unix': 'make'}}
" or
Plug 'zchee/deoplete-go', { 'do': 'make'}
```

## Settings

### Class Aligning
By default the classes (var, func, type, const) are not aligned in the popup menu.

First is unaligned, second is aligned.

![Unaligned vs Aligned classes](images/align_class.png)

If you would like them aligned just set:

```vim
let g:deoplete#sources#go#align_class = 1
```

### Class Sorting and Ignore
By befault, the completion list is in the sort order of gocode.  
If you want to change it to an arbitrary order, set it in `g:deoplete#sources#go#sort_class`.

Available values are `package`, `func`, `type`, `var`, `const`.  
If you do not include any value, will be always hidden in the completion list.

e.g.
```vim
let g:deoplete#sources#go#sort_class = ['package', 'func', 'type', 'var', 'const']
```

Test it in the `os` package.

### `gocode` binary
`deoplete-go` will directly call `gocode`.  
By default, `$PATH` is used to find the gocode binary.
If you want to use a different binary, set

```vim
let g:deoplete#sources#go#gocode_binary = '/path/to/gocode'
```

### Package Period
By default no period is inserted after a package name. If you would prefer adding a period then set:

```vim
let g:deoplete#sources#go#package_dot = 1
```

## Sample init.vim

```vim
" neocomplete like
" https://github.com/Shougo/deoplete.nvim/blob/master/doc/deoplete.txt
set completeopt+=noinsert

" Set before than deoplete
" deoplete#mappings#_set_completeopt() in
" https://github.com/Shougo/deoplete.nvim/blob/master/autoload/deoplete/mappings.vim
" https://github.com/Shougo/deoplete.nvim/blob/master/rplugin/python3/deoplete/deoplete.py
set completeopt+=noselect

" Path to python interpreter for neovim
let g:python3_host_prog  = '/path/to/python3'
" Skip the check of neovim module
let g:python3_host_skip_check = 1

let g:deoplete#enable_at_startup = 1
```


## Deoplete Settings

The source settings are by default set to `rank = 100` and `input_pattern = '[^. \t0-9]\.\w*'`.  
If you want to customize those variables, insert the following into your `init.vim` after setting `runtimepath`.  
e.g. if you want the `rank = 9999`,

```vim
call deoplete#custom#set('go', 'rank', 9999)
```

Available settings and their corresponding values

| setting                 | `deoplete.nvim` default                   | `deoplete-go` default       |
|-------------------------|-------------------------------------------|-----------------------------|
| `name`                  | -                                         | go                          |
| `mark`                  | -                                         | `[go]`                      |
| `filetype`              | all filetypes                             | go                          |
| `rank`                  | `100`                                     | 500                         |
| `min_pattern_length`    | `g:deoplete#auto_completion_start_length` | -                           |
| `input-pattern`         | -                                         | `'[^. \t0-9]\.\w*'`         |
| `is_byteopts`           | `False`                                   | -                           |
| `matchers`              | `deoplete-filter-matcher_default`         | -                           |
| `sorters`               | `deoplete-filter-sorter_default`          | -                           |
| `converters`            | `deoplete-filter-converter_default`       | -                           |

Also, see 

```vim
:help deoplete-source-attributes
```


TODO:
-----
- [ ] Parse included cgo (C,C++ language) headers
 - `ctags` will be blocking `deoplete.nvim`
- [ ] ~~Support Go stdlib package `import "***"` name completion~~
 - ~~Retain the static api text? or parse?~~
 - See https://github.com/zchee/deoplete-go/pull/19
- [x] Execute `gocode` binary instead of call vim function
- [x] Get and parse completion list of json format. such as `ycm`
- [x] When there is no candidate infomation, deoplete will cause an error
- [x] Support fizzy matching
