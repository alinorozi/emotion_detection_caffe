// (c) 2015 Zedge Inc.
//

// include Python.h first to get of the _POSIX_C_SOURCE warning
#include <Python.h>
#include <iostream>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include "caffe/caffe.hpp"
#include "caffe/util/io.hpp"
#include "caffe/blob.hpp"
#include "zedge_caffe.h"

using namespace caffe;

class Convnet {
 public:
  Convnet(char* deploy_file, char* trained_model, char* layer)
      : deploy_file_(deploy_file),
        trained_model_(trained_model),
        layer_(layer),
        net_(NULL) {
  }

  bool Init() {
    net_ = new Net<float>(deploy_file_, caffe::TEST);
    net_->CopyTrainedLayersFrom(trained_model_);
    mem_data_layer_ = boost::dynamic_pointer_cast<MemoryDataLayer<float> >(
        net_->layers()[0]);
    return mem_data_layer_.get() != NULL;
  }

  ~Convnet() {
    delete net_;
  }

  PyObject* PredictImage(char* filename) {
    cv::Mat image = cv::imread(filename, CV_LOAD_IMAGE_COLOR);
    if (image.empty()) {
      char error[300];
      snprintf(error, 300, "Failed to load image %s", filename);
      PyErr_SetString(PyExc_IOError, error);
      return NULL;
    }
    const int width = image.size().width;
    const int height = image.size().height;
    const float ratio = std::min(width, height) / 300.0;
    const int interpolation =
        ratio == 1 ? cv::INTER_LINEAR :
        ratio > 1 ? cv::INTER_CUBIC : cv::INTER_AREA;
    const int new_w = ceil(width / ratio);
    const int new_h = ceil(height / ratio);
    cv::Mat resized;
    cv::resize(image, resized, cv::Size(new_w, new_h), 0, 0, interpolation);
    int shift_h = 0, shift_w = 0;
    if (new_w > new_h) {
      shift_w = (new_w - new_h) / 2;
    } else {
      shift_h = (new_h - new_w) / 2;
    }
    cv::Rect crop(shift_w, shift_h, 300, 300);
    resized = resized(crop);
    if (resized.size().height != 300 || resized.size().width != 300) {
      char error[300];
      snprintf(error, 300, "Resized image's size should be (300,300): %s (%d,%d)",
               filename, resized.size().height, resized.size().width);
      PyErr_SetString(PyExc_IOError, error);
      return NULL;
    }
    const int d[4][2] = {{0,0},{44,0},{0,44},{44,44}};
    std::vector<cv::Mat> images;
    std::vector<int> labels;
    for (int i = 0; i < 4; ++i) {
      cv::Rect crop(d[i][0], d[i][1], 256, 256);
      cv::Mat cropped_img = resized(crop);
      if (cropped_img.size().height != 256 || cropped_img.size().width != 256) {
        char error[300];
        snprintf(error, 300, "Cropped image's size should be (256,256): %s (%d,%d)",
                 filename, cropped_img.size().height, cropped_img.size().width);
        PyErr_SetString(PyExc_IOError, error);
        return NULL;
      }
      images.push_back(cropped_img);
      labels.push_back(0);
    }
    cv::resize(resized, resized, cv::Size(256, 256), 0, 0, cv::INTER_CUBIC);
    if (resized.size().height != 256 || resized.size().width != 256) {
      char error[300];
      snprintf(error, 300, "Resized image's size should be (256,256): %s (%d,%d)",
               filename, resized.size().height, resized.size().width);
      PyErr_SetString(PyExc_IOError, error);
      return NULL;
    }
    images.push_back(resized);
    labels.push_back(0);
    mem_data_layer_->AddMatVector(images, labels);
    float loss;
    net_->ForwardPrefilled(&loss);
    boost::shared_ptr<Blob<float> > prob = net_->blob_by_name(layer_);
    if (prob->count() != 10) {
      char error[300];
      snprintf(error, 300, "Expected 10 outputs got %d", prob->count());
      PyErr_SetString(PyExc_IOError, error);
      return NULL;
    }
    float p[2] = {0};
    int c[2] = {0};
    for (int i = 0; i < prob->count(); ++i) {
      p[i&1] += prob->cpu_data()[i];
      c[i&1]++;
    }
    PyObject* col = PyList_New(2);
    if (!col) {
      return NULL;
    }
    for (int i = 0; i < 2; ++i) {
      PyObject* v = PyFloat_FromDouble(p[i]/c[i]);
      if (!v) {
        Py_DECREF(col);
        return NULL;
      }
      PyList_SET_ITEM(col, i, v);
    }
    return col;
  }

 private:
  char* deploy_file_;
  char* trained_model_;
  char* layer_;
  Net<float>* net_;
  boost::shared_ptr<MemoryDataLayer<float> > mem_data_layer_;
};

static PyMethodDef zcaffeMethods[] = {
  {"init_convnet", initConvNet, METH_VARARGS},
  {"free_convnet", freeConvNet, METH_VARARGS},
  {"predict", predictImage, METH_VARARGS},
  {NULL, NULL}
};

void initzcaffe() {
  (void) Py_InitModule("zcaffe", zcaffeMethods);
}

PyObject* initConvNet(PyObject* self, PyObject* args) {
  Caffe::set_mode(Caffe::CPU);
  char* deploy_file;
  char* trained_model;
  char* layer;
  if (!PyArg_ParseTuple(args, "sss", &deploy_file, &trained_model, &layer)) {
    return NULL;
  }
  Convnet* convnet(new Convnet(deploy_file, trained_model, layer));
  if (!convnet->Init()) {
    char error[300];
    snprintf(error, 300, "the first layer should be MemoryDataLayer");
    PyErr_SetString(PyExc_IOError, error);
    return NULL;
  }
  return PyLong_FromVoidPtr(reinterpret_cast<void*>(convnet));
}

PyObject* freeConvNet(PyObject* self, PyObject* args) {
  PyObject* ptr;
  if (!PyArg_ParseTuple(args, "O", &ptr)) {
    return NULL;
  }
  delete reinterpret_cast<Convnet*>(PyLong_AsVoidPtr(ptr));
  Py_RETURN_NONE;
}

PyObject* predictImage(PyObject* self, PyObject* args) {
  PyObject* ptr;
  char* filename;
  if (!PyArg_ParseTuple(args, "Os", &ptr, &filename)) {
    return NULL;
  }
  Convnet* convnet = reinterpret_cast<Convnet*>(PyLong_AsVoidPtr(ptr));
  return convnet->PredictImage(filename);
}
