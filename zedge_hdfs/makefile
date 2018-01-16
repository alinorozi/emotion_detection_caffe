# (c) 2013 Zedge Inc.
#

CC=g++
CFLAGS=-c -fpic -Wall -I/opt/anaconda/include/python2.7 -O3
LDFLAGS=-shared -L/opt/anaconda/lib -lpython2.7 -lhdfs -L/usr/lib/jvm/java-1.7.0/jre/lib/amd64/server -lpthread     -ljvm      -lrt
SOURCES=zedge_hdfs.cc
OBJECTS=$(SOURCES:.cc=.o)
FINALLIB=zhdfs.so

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

