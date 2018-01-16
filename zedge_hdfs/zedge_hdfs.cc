// (c) 2013 Zedge Inc.
//

// include Python.h first to get of the _POSIX_C_SOURCE warning
#include <Python.h>

#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>
#include <hdfs.h>
#include "zedge_hdfs.h"

// persistant connection to the local file system
static hdfsFS local_fs;

static PyMethodDef zhdfsMethods[] = {
  {"connect", connectHdfs, METH_VARARGS},
  {"disconnect", disconnectHdfs, METH_VARARGS},
  {"get", getHdfs, METH_VARARGS},
  {"get_timeout", getHdfsTimeOut, METH_VARARGS},
  {"test", testException, METH_VARARGS},
  {NULL, NULL}
};

void initzhdfs() {
  (void) Py_InitModule("zhdfs", zhdfsMethods);
}

class StderrHandler {
  public:
   StderrHandler()  { closeStderr(); }
   ~StderrHandler() { openStderr();  }
  private:
   void closeStderr() {
     int fd = open("/dev/null", O_WRONLY);
     // redirect the standard error to /dev/null
     dup2(fd, 2);
     close(fd);
   }

   void openStderr() {
     int fd = open("/dev/tty", O_WRONLY);
     dup2(2, fd);
     close(fd);
   }
};

PyObject* connectHdfs(PyObject* self, PyObject* args) {
  char* host;
  int port;
  if (!PyArg_ParseTuple(args, "si", &host, &port)) {
    return NULL;
  }
  hdfsFS remote_fs = hdfsConnect(host, port);
  if (!remote_fs) {
    PyErr_Format(PyExc_SystemError, "Failed to connect %s %d", host, port);
    return NULL;
  }
  local_fs = hdfsConnect(NULL, 0);
  if (!local_fs) {
    PyErr_Format(PyExc_SystemError, "Failed to connect local filesystem");
    return NULL;
  }
  return PyLong_FromVoidPtr(reinterpret_cast<void*>(remote_fs));
}

PyObject* disconnectHdfs(PyObject* self, PyObject* args) {
  PyObject* ptr;
  if (!PyArg_ParseTuple(args, "O", &ptr)) {
    return NULL;
  }
  hdfsFS remote_fs = reinterpret_cast<hdfsFS>(PyLong_AsVoidPtr(ptr));
  StderrHandler handler;
  if (hdfsDisconnect(remote_fs) != -1 &&
      hdfsDisconnect(local_fs) != -1) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
}

PyObject* getHdfs(PyObject* self, PyObject* args) {
  PyObject* ptr;
  char* remote_path;
  char* local_path;
  if (!PyArg_ParseTuple(args, "Oss", &ptr, &remote_path, &local_path)) {
    return NULL;
  }
  hdfsFS remote_fs = reinterpret_cast<hdfsFS>(PyLong_AsVoidPtr(ptr));
  StderrHandler handler;
  if (hdfsCopy(remote_fs, remote_path, local_fs, local_path) == -1) {
    PyErr_Format(PyExc_IOError, "getHdfs: failed to get %s", remote_path);
    return NULL;
  }
  Py_RETURN_NONE;
}

class CopyThread {
 public:
  CopyThread(hdfsFS& remote_fs, hdfsFS& local_fs,
             char* remote_path, char* local_path)
      : remote_fs(remote_fs), local_fs(local_fs),
        remote_path(remote_path), local_path(local_path) {
  }

  static void* copy_helper(void* context) {
    return reinterpret_cast<CopyThread*>(context)->copy();
  }

 private:
  void* copy() {
    return reinterpret_cast<void*>(
        hdfsCopy(remote_fs, remote_path, local_fs, local_path));
  }

  hdfsFS& remote_fs;
  hdfsFS& local_fs;
  const char* remote_path;
  const char* local_path;
};

PyObject* getHdfsTimeOut(PyObject* self, PyObject* args) {
  PyObject* ptr;
  char* remote_path;
  char* local_path;
  int time_limit;      // by seconds
  if (!PyArg_ParseTuple(args, "Ossi", &ptr, &remote_path,
                        &local_path, &time_limit)) {
    return NULL;
  }
  if (time_limit <= 0) {
    PyErr_Format(PyExc_SystemError, "time_limit (%d) <= 0", time_limit);
    return NULL;
  }
  hdfsFS remote_fs = reinterpret_cast<hdfsFS>(PyLong_AsVoidPtr(ptr));

  struct timespec ts;
  if (clock_gettime(CLOCK_REALTIME, &ts) == -1) {
    PyErr_Format(PyExc_IOError,
                 "getHdfsTimeOut(%s): clock_gettime", remote_path);
    return NULL;
  }
  ts.tv_sec += time_limit;

  CopyThread cp(remote_fs, local_fs, remote_path, local_path);
  pthread_t thread;
  StderrHandler handler;
  if (pthread_create(&thread, NULL, &CopyThread::copy_helper, &cp) != 0) {
    PyErr_Format(PyExc_IOError,
                 "getHdfsTimeOut(%s): pthread_create", remote_path);
    return NULL;
  }

  int status = -1;
  // this function is designed only for Linux
  if (pthread_timedjoin_np(thread, reinterpret_cast<void**>(&status), &ts) != 0) {
    PyErr_Format(PyExc_IOError,
                 "getHdfsTimeOut(%s): failed to get", remote_path);
    return NULL;
  }

  if (status != 0) {
    PyErr_Format(PyExc_IOError,
                 "getHdfsTimeOut: failed to get %s", remote_path);
    return NULL;
  }

  Py_RETURN_NONE;
}

PyObject* testException(PyObject* self, PyObject* args) {
  PyErr_SetString(PyExc_IOError, "exception testing");
  return NULL;   // to raie an exception we should return NULL!
}

