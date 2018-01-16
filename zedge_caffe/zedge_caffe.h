// (c) 2014 Zedge Inc.
//
//

#ifndef _ZEDGE_CAFFE_H_
#define _ZEDGE_CAFFE_H_

extern "C" void initzcaffe();

PyObject* initConvNet(PyObject* self, PyObject* args);
PyObject* freeConvNet(PyObject* self, PyObject* args);
PyObject* predictImage(PyObject* self, PyObject* args);

#endif      // _ZEDGE_CAFFE_H_

