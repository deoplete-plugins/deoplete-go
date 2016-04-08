TARGET = ./rplugin/python3/deoplete/ujson.so

CURRENT := $(shell pwd)
RPLUGIN_HOME := $(CURRENT)/rplugin/python3
PYTHON3 := $(shell which python3)
GIT := $(shell which git)

RPLUGIN_PATH := ./rplugin/python3/deoplete/sources/
MODULE_NAME := deoplete_go.py


all : $(TARGET)

build/:
	$(GIT) submodule update --init
	cd ./rplugin/python3/deoplete/ujson; $(PYTHON3) setup.py build --build-base=$(CURRENT)/build --build-lib=$(CURRENT)/build

rplugin/python3/deoplete/ujson.so: build/
	cp $(shell find $(CURRENT)/build -name ujson*.so) $(RPLUGIN_HOME)/deoplete/ujson.so

test: lint

lint: flake8

flake8: test_modules
	flake8 -v --config=$(PWD)/.flake8 ${RPLUGIN_PATH}${MODULE_NAME} || true

test_modules:
	pip3 install -U -r ./tests/requirements.txt

clean:
	$(RM) -rf $(CURRENT)/build $(RPLUGIN_HOME)/deoplete/ujson.so

.PHONY: test lint flake8 test_modules clean
