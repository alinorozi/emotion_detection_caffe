# (c) 2014 Zedge Inc.
#

CC=g++
#CFLAGS=-c -fpic -Wall -I/usr/include/python2.6 -O3
#LDFLAGS=-shared -lpython2.6 `pkg-config --libs --cflags opencv` -lrt

CFLAGS=-c -fpic -Wall -I/usr/include/python2.7 -O3
LDFLAGS=-shared -lpython2.7 `pkg-config --libs --cflags opencv` -lrt

SOURCES=zedge_cv.cc
OBJECTS=$(SOURCES:.cc=.o)
FINALLIB=zcv.so

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

