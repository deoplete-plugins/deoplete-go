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
By default the classes (var, func, type, const, package) are not aligned in the popup menu.

First image is unaligned, second is aligned.

<img src="class-align.png">

If you would like them aligned just set:

```vim
let g:deoplete#sources#go#align_class = 1
```

### Class Sorting
By befault, the completion list is in the sort order of gocode.
If you want to change it to a arbitrary order, set it in `g:deoplete#sources#go#sort_class`.

Available values are `package`, `func`, `type`, `var`, `const`.
`g:deoplete#sources#go#sort_class` **value must include all class.**

e.g.
```vim
let g:deoplete#sources#go#sort_class = ['package', 'func', 'type', 'var', 'const']
```

Test it in `os` package.

### `gocode` binary
`deoplete-go` will directly call the `gocode`.
By default, the first `gocode` binary in the `$PATH`.
If you want to use a different `gocode`, set

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
" https://github.com/Shougo/deoplete.nvim/blob/master/doc/deoplete.txt#L594-L599
set completeopt+=noinsert

" Disable auto selection
set completeopt+=noselect

" for neovim python-client
let g:python3_host_prog  = '/path/to/python3'

" deoplete config
let g:deoplete#enable_at_startup = 1
```


## Deoplete Settings

`deoplete-go` sets the source settings to `rank = 100` and `input_pattern = '[^. \t0-9]\.\w*'`by default.
If you want to customize those variables, insert the following into your `init.vim` after setting `runtimepath`.
e.g. `rank` is `9999`,

```vim
call deoplete#custom#set('go', 'rank', 9999)
```

If you want to the same motion as the `omnifunc`, set

```vim
call deoplete#custom#set('go', 'min_pattern_length', 1000)
```

Available setting values

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

Also see

```vim
:help deoplete-source-attributes
```


## Why `deoplete` also `deoplete-go` are not use `omnifunc`?
When deoplete calls `omnifunc`, it blocks the user interface a little bit.
This is a specification of `vim` and also `neovim`.
We can not call `omnifunc` asynchnously.

If we use the `deoplete` source implementation, `deoplete` can get a dictionary completion word list asynchnously.
If `deoplete-go` (and other `deoplete` source plugins) pass exactly the same dictionary word list as `omnifunc` to `deoplete`, we do not need a `omnifunc`.
This is the advantage of this plugin.

Also see https://github.com/zchee/deoplete-go/issues/4#issuecomment-172412821 .


Todo:
-----
- [x] Execute `gocode` binary instead of call vim function
- [x] Get and parse completion list of json format. such as `ycm`
- [ ] Support Go stdlib package `import "***"` name completion
 - Retain the static api text? or parse?
- [ ] When there is no candidate infomation, deoplete will cause an error
- [ ] Support fizzy matching
- [ ] Parse included cgo (C,C++ language) headers
 - `ctags` will be blocking deoplete
