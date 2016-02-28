TARGET = ./rplugin/python3/deoplete/ujson.so

CURRENT := $(shell pwd)
RPLUGIN_HOME := $(CURRENT)/rplugin/python3
PYTHON3 := $(shell which python3)
GIT := $(shell which git)

all : $(TARGET)

$(TARGET) : fetch build move

fetch:
	$(GIT) submodule update --init

build: fetch
	cd ./rplugin/python3/deoplete/ujson; $(PYTHON3) setup.py build --build-base=$(CURRENT)/build --build-lib=$(CURRENT)/build

move: build
	cp $(shell find $(CURRENT)/build -name ujson*.so) $(RPLUGIN_HOME)/deoplete/ujson.so

clean :
	$(RM) -rf $(CURRENT)/build $(RPLUGIN_HOME)/deoplete/ujson.so $(RPLUGIN_HOME)/deoplete/ujson

.PHONY: fetch build move clean
