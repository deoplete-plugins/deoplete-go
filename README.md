# deoplete-go

|| **Status** |
|:---:|:---:|
| **Travis CI** |[![Build Status](https://travis-ci.org/zchee/deoplete-go.svg?branch=master)](https://travis-ci.org/zchee/deoplete-go)|
| **Gitter** |[![Join the chat at https://gitter.im/zchee/deoplete-go](https://badges.gitter.im/zchee/deoplete-go.svg)](https://gitter.im/zchee/deoplete-go?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)|

Go source for [deoplete.nvim](https://github.com/Shougo/deoplete.nvim) use [gocode](https://github.com/nsf/gocode).

## Overview
Asynchronous Go completion for Neovim.  
Use,

### deoplete.nvim
[Shougo/deoplete.nvim](https://github.com/Shougo/deoplete.nvim)

Dark powered asynchronous completion framework for neovim.  
Fastetst, Fully asynchronous, Nonblocking user interface, Customizable source for each languages, and more.  
The Nextgen word completion.

### gocode
[nsf/gocode](https://github.com/nsf/gocode)

An autocompletion daemon for the Go programming language.  
Fastest, Context-sesinive, Server/Client architecture, Result caching.  
The defact standard completion engine.

===

## Required

### Neovim and neovim/python-client
https://github.com/neovim/neovim  
https://github.com/neovim/python-client

### deoplete.nvim
https://github.com/Shougo/deoplete.nvim

### gocode
https://github.com/nsf/gocode

===

## How to install

### 1. Install Neovim
See Neovim wiki.

- [Installing Neovim](https://github.com/neovim/neovim/wiki/Installing-Neovim)
- [Following HEAD](https://github.com/neovim/neovim/wiki/Following-HEAD)
- [Building](https://github.com/neovim/neovim/wiki/Building-Neovim)

### 2. Install neovim/python-client
Neovim remonte client for python.  
See https://github.com/neovim/python-client

```bash
pip2 install --upgrade neovim
pip3 install --upgrade neovim
```

### 3. Install latest of gocode

```bash
go get -u github.com/nsf/gocode
```

### 4. Install plugin and Build ujson module
`deoplete-go` using [esnme/ultrajson](https://github.com/esnme/ultrajson) json module.  
It's Python bindings for C library. Need compiling.  
So, If you use Plugin manager supported build process, set `make` commmand.

```vim
" dein.vim
call dein#add('Shougo/deoplete.nvim')
call dein#add('zchee/deoplete-go', {'build': 'make'})

" NeoBundle
NeoBundle 'Shougo/deoplete.nvim'}
NeoBundle 'zchee/deoplete-go', {'build': {'unix': 'make'}}

" vim-plug
Plug 'Shougo/deoplete.nvim'
Plug 'zchee/deoplete-go', { 'do': 'make'}
```

===

## Available Settings

| Setting value                          | Default | Required      |
|:---------------------------------------|:-------:|:-------------:|
| `g:deoplete#sources#go#gocode_binary`  | `''`    | **Recommend** |
| `g:deoplete#sources#go#package_dot`    | `0`     | No            |
| `g:deoplete#sources#go#sort_class`     | `[]`    | **Recommend** |
| `g:deoplete#sources#go#use_cache`      | `0`     | **Recommend** |
| `g:deoplete#sources#go#json_directory` | `''`    | **Recommend** |
| `g:deoplete#sources#go#cgo`            | `0`     | *Any*         |
| `g:deoplete#sources#go#goos`           | `''`    | No            |

### `g:deoplete#sources#go#gocode_binary`
#### `gocode` Binary

| **Default**  | `''`                    |
|--------------|-------------------------|
| **Required** | **Recommend**           |
| **Type**     | string                  |
| **Example**  | `$GOPATH.'/bin/gocode'` |

`deoplete-go` will directly call `gocode`. Not vim bypass due to the omnifunc.  
By default(not set), Find the gocode binary in `$PATH` environment.  
This setting is **Recommend**.  
If you set it, `deoplete-go` spared look for the binary. It will improve performance.

Also, If you want to use a different from the first found `gocode` binary from `$PATH` then set:
```vim
let g:deoplete#sources#go#gocode_binary = '/path/to/gocode'
```

### `g:deoplete#sources#go#package_dot`
#### Automatically insert dot for after package name

| **Default**  | `0` |
|--------------|-----|
| **Required** | No  |
| **Type**     | int |
| **Example**  | `1` |

Automatically insert dot(period) when you select `package` name in popup menu.  
By default, no dot(period) is inserted after a package name.

If you would prefer adding a period then set:
```vim
let g:deoplete#sources#go#package_dot = 1
```

### `g:deoplete#sources#go#sort_class`
#### Class Sorting and Ignore

| **Default**  | `[]`               |
|--------------|--------------------|
| **Required** | **Recommend**      |
| **Type**     | list               |
| **Example**  | See bellow exmaple |

By befault, the completion word list is in the sort order of gocode. Same as omnifunc.  
If you want to change it to an arbitrary order, set it.

Available values are [`package`, `func`, `type`, `var`, `const`].  
If you did not include any value, it will always be hidden in the completion list.

To display all words while sorting, set:
```vim
let g:deoplete#sources#go#sort_class = ['package', 'func', 'type', 'var', 'const']
```

### `g:deoplete#sources#go#pointer`
#### Support pointer match

| **Default**  | `0`   |
|--------------|-------|
| **Required** | *Any* |
| **Type**     | int   |
| **Example**  | `1`   |

Support pointer(`*`) match.  
Example are bellow code. `|` is cursor.

```go
type Foo struct {
  FooName string
}

func NewFoo() *Foo {
  return &Foo{}
}

func (f *|
```

### `g:deoplete#sources#go#use_cache` `g:deoplete#sources#go#json_directory`
#### Static json caching

`g:deoplete#sources#go#use_cache`

| **Default**  | `0`           |
|--------------|---------------|
| **Required** | **Recommend** |
| **Type**     | int           |
| **Example**  | `1`           |

`g:deoplete#sources#go#json_directory`

| **Default**  | `''`                                   |
|--------------|----------------------------------------|
| **Required** | **Recommend**                          |
| **Type**     | string                                 |
| **Example**  | `'~/.cache/deoplete/go/$GOOS_$GOARCH'` |

Use static json caching Go stdlib package API.  
If matched name of stdlib and input package name, it returns the static json data without the use of gocode.  
and, Possible to get package API if have not `import` of current buffer.

Terms:

- Hook the insert of dot `.` (e.g. `fmt.|`)
- You typed package name have not `import` current buffer
- Match the typed package name and json file name

`deoplete-go` will parse `g:deoplete#sources#go#json_directory` directory. You can define of json data directory.  
Recommend is `~/.cache/deoplete/go/$GOOS_$GOARCH` because this directly use other deoplete sources(e.g. deoplete-deji).

Also, See [How to use static json caching](#how-to-use-static-json-caching)

```vim
let g:deoplete#sources#go#use_cache = 1
let g:deoplete#sources#go#json_directory = '/path/to/data_dir'
```

### `g:deoplete#sources#go#cgo`
#### cgo complete use libclang-python3

| **Default**  | `0`   |
|--------------|-------|
| **Required** | *Any* |
| **Type**     | int   |
| **Example**  | `1`   |

If current buffer have `import "C"` also `#include <foo.h>` and when you type `C.`, deoplete-go will be display the C function in the `foo.h`.

Simple example is below. `|` is cursor.

```go
package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"fmt"
)

func main() {
	fmt.Printf()
	C.|
}
```

Will return the `pid_t`, `malloc`, `free` and more.  

The real example use libgit2.

```go
package main

/*
#include <git2.h>
*/
import "C"
import (
	"log"
	"os"
	"path/filepath"

	"github.com/libgit2/git2go"
)

func main() {
	repoPath := filepath.Join(os.Getenv("GOPATH"), "src/github.com/libgit2/git2go")
	gitRepo, err := git.OpenRepository(repoPath)

	C.git_blame_|

	if err != nil {
		log.Fatal(err)
	}
	commitOid, err := gitRepo.Head()
	if err != nil {

	}
}
```

Will return the that completion list.  

![cgo_libgit2](images/cgo_libgit2.png)

Now support current buffer only.  
TODO: Support parses `.c`, `.h` file.

### `g:deoplete#sources#go#cgo#libclang_path`
#### libclang shared library path for cgo complete

| **Default**  | ` `                            |
|--------------|--------------------------------|
| **Required** | *Any*                          |
| **Type**     | string                         |
| **Example**  | `/opt/llvm/lib/libclang.dylib` |

libclang shared library path option.  
In darwin, `libclang.dylib`, In Linux, `libclang.so`.  

### `g:deoplete#sources#go#cgo#std`
#### C language standard version

| **Default**  | `c11`  |
|--------------|--------|
| **Required** | *Any*  |
| **Type**     | string |
| **Example**  | `c99`  |

C language standard version option.  
If not set, deoplete-go use `c11`(latest) version.

### `g:deoplete#sources#go#auto_goos`
#### Automatically set GOOS environment variable when calling `gocode`

| **Default**  | `0`     |
|--------------|---------|
| **Required** | No      |
| **Type**     | boolean |
| **Example**  | `1`     |

When enabled, deoplete-go will try to set `GOOS` by checking the file name for
`name_<OS>.go`.  If not found, the file will be checked for a `// +build <OS>`
directive.  If the file's OS doesn't match your OS (e.g.  `file_darwin.go`
while on `linux`), `CGO_ENABLED=0` will also be set.

**Note:** There may be a 5-10 second delay if `gocode` needs to compile the
platform-specific sources for the first time.

===

### How to use static json caching

| **Current Go version** | `1.7.3`           |
|------------------------|-------------------|
| `$GOOS`                | `darwin`, `linux` |
| `$GOARCH`              | `amd64`           |

Pre-generate json data is [data/json](./data/json).  
If you use it, `cp -r data/json/VERSION/$GOOS_$GOARCH /path/to/data_dir`.  
`/path/to/data_dir` is `g:deoplete#sources#go#json_directory`.

And, You can generate your Go environment. such as version is `devel`, GOARCH is `arm`.  
If you want to it, run `make gen_json`.  
Will generated json file to `./data/json/VERSION/$GOOS_$GOARCH`.

`make gen_json` command also will create `./data/stdlib.txt`. It same as `go tool api` result.  
In detail,
```bash
go tool api -contexts $GOOS-$GOARCH-cgo | grep -v 'golang.org/x/net/http2/hpack' | sed -e s/,//g | awk '{print $2}' | uniq > ./data/stdlib.txt
```

This api list used in the base for the generation of json file.


===

## Sample init.vim

```vim
" neocomplete like
set completeopt+=noinsert
" deoplete.nvim recommend
set completeopt+=noselect

" Path to python interpreter for neovim
let g:python3_host_prog  = '/path/to/python3'
" Skip the check of neovim module
let g:python3_host_skip_check = 1

" Run deoplete.nvim automatically
let g:deoplete#enable_at_startup = 1
" deoplete-go settings
let g:deoplete#sources#go#gocode_binary = $GOPATH.'/bin/gocode'
let g:deoplete#sources#go#sort_class = ['package', 'func', 'type', 'var', 'const']
let g:deoplete#sources#go#use_cache = 1
let g:deoplete#sources#go#json_directory = '/path/to/data_dir'
```

===

TODO:
-----
- [x] Parse included cgo (C, C++ language) headers on current buffer
  - `ctags` will be blocking `deoplete.nvim`
- [x] Support static json caching
  - See https://github.com/zchee/deoplete-go/pull/19
- [x] Support Go stdlib package `import "***"` name completion
  - This feature has been implemented in gocode. Thanks @nhooyr!
- [x] Execute `gocode` binary instead of call vim function
- [x] Get and parse completion list of json format. such as `ycm`
- [x] When there is no candidate infomation, deoplete will cause an error
- [x] Support fizzy matching
