if exists('g:loaded_deoplete_go')
  finish
endif
let g:loaded_deoplete_go = 1

if !exists("g:deoplete#sources#go#align_class")
  let g:deoplete#sources#go#align_class = 0
endif

if !exists("g:deoplete#sources#go#gocode_binary")
  let g:deoplete#sources#go#gocode_binary = ''
endif

if !exists("g:deoplete#sources#go#package_dot")
  let g:deoplete#sources#go#package_dot = 0
endif

if !exists("g:deoplete#sources#go#sort_class")
  let g:deoplete#sources#go#sort_class = []
endif
