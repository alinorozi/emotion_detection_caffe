# (c) 2015 Zedge Inc.
#

CC=g++
#CFLAGS=-c -fpic -Wall -I/usr/include/python2.6 -O3
#LDFLAGS=-shared -lpython2.6 `pkg-config --libs --cflags opencv` -lrt

CFLAGS=-c -fpic -Wall -I/opt/anaconda/include/python2.7 -O3 \
       -DCPU_ONLY \
       -I/var/caffe/include \
       -I/var/caffe/src \
       -I/var/caffe/.build_release/src -fopenmp
LDFLAGS=-shared -L/opt/anaconda/lib -lpython2.7 `pkg-config --libs --cflags opencv` -lprotobuf -lglog -L/usr/local/lib/ -L/var/caffe/build/lib/ -lcaffe -lrt 

SOURCES=zedge_caffe.cc
OBJECTS=$(SOURCES:.cc=.o)
FINALLIB=zcaffe.so

all: $(SOURCES) $(FINALLIB) 
#link

.PHONY: clean link

$(FINALLIB): $(OBJECTS)
	$(CC) $(LDFLAGS) $(OBJECTS) -o $(FINALLIB)

.cc.o:
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f $(OBJECTS) $(FINALLIB)

link:
	ln -sf ../$(FINALLIB) ./$(FINALLIB)

