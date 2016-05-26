FROM golang:1.6.2-alpine
MAINTAINER zchee <k@zchee.io>

RUN set -ex \
	&& apk add --no-cache --virtual .build-deps \
		make \
		git \
		tar \
		python3 \
	\
	&& go get -u -v github.com/nsf/gocode

COPY ./ /deoplete-go

RUN cd /deoplete-go \
	&& make gen_json \
	\
	&& tar cf json_1.6.2_linux_amd64.tar.gz ./data/json/1.6.2/linux_amd64

CMD ["cat", "/deoplete-go/json_1.6.2_linux_amd64.tar.gz"]
