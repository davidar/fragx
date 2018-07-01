#!/bin/sh

SOURCE_DIR=$PWD/glslang
BUILD_DIR=$SOURCE_DIR/build

cd $SOURCE_DIR
git clone https://github.com/google/googletest.git External/googletest
./update_glslang_sources.py
mkdir -p $BUILD_DIR
cd $BUILD_DIR
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$(pwd)/install" $SOURCE_DIR
make -j4 install
ctest
cd $SOURCE_DIR/Test && ./runtests
