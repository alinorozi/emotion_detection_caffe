#!/bin/sh

export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/lib:/opt/anaconda/lib:/opt/xianyi-OpenBLAS-2b0d8a8:$JAVA_HOME/jre/lib/amd64:$JAVA_HOME/jre/lib/amd64/server:/var/zedge_convnet2/caffe/build/lib:/usr/local/cuda/targets/x86_64-linux/lib:$LD_LIBRARY_PATH

cd $(dirname $BASH_SOURCE)

nohup /opt/anaconda/bin/python zedge_classifier.py 1>>/var/log/zedge_convnet2/web.stderr 2>&1 &

