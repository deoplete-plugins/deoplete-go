if exists('g:loaded_deoplete_go')
  finish
endif
let g:loaded_deoplete_go = 1


let g:deoplete#sources#go#align_class =
      \ get( g:, 'deoplete#sources#go#align_class', 0 )

let g:deoplete#sources#go#gocode_binary =
      \ get( g:, 'deoplete#sources#go#gocode_binary', '' )

let g:deoplete#sources#go#package_dot =
      \ get( g:, 'deoplete#sources#go#package_dot', 0 )

let g:deoplete#sources#go#sort_class =
      \ get( g:, 'deoplete#sources#go#sort_class', [] )
