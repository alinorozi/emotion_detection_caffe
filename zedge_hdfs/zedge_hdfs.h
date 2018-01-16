// (c) 2013 Zedge Inc.
//

#ifndef _ZEDGE_HDFS_H_
#define _ZEDGE_HDFS_H_

extern "C" void initzhdfs();

PyObject* connectHdfs(PyObject* self, PyObject* args);
PyObject* disconnectHdfs(PyObject* self, PyObject* args);
PyObject* getHdfs(PyObject* self, PyObject* args);
PyObject* getHdfsTimeOut(PyObject* self, PyObject* args);
PyObject* testException(PyObject* self, PyObject* args);

#endif      // _ZEDGE_HDFS_H_

