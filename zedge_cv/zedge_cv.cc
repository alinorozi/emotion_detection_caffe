// (c) 2014 Zedge Inc.
//

#include <stdio.h>
#include <vector>
#include <string>
#include <unistd.h>
#include <sys/stat.h>
#include <dirent.h>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/features2d/features2d.hpp>
#include <opencv2/objdetect/objdetect.hpp>
#include <Python.h>
#include "zedge_cv.h"

std::string getFullPath(const std::string& path, const std::string& file) {
  if (path.empty()) {
    return file;
  }
  return path[path.length() - 1] == '/' ? path + file : path + "/" + file;
}

class FaceDetector {
 public:
  bool loadCascades(const std::string& cascade_dir) {
    if (!cascade_face_.load(getFullPath(cascade_dir, "haarcascade_frontalface_alt.xml"))) {
      return false;
    }
    if (!cascade_eye_.load(getFullPath(cascade_dir, "haarcascade_eye.xml"))) {
      return false;
    }
    return true;
  }

  bool detect(cv::Mat& img) {
    const int min_neighbor = 2;
    const int flags = CV_HAAR_SCALE_IMAGE;
    std::vector<cv::Rect> faces;
    cascade_face_.detectMultiScale(
        img, faces, 1.1, min_neighbor, flags, cv::Size(30, 30));
    for (std::vector<cv::Rect>::const_iterator it = faces.begin();
         it != faces.end(); ++it) {
      cv::Mat face_region = img(*it);
      std::vector<cv::Rect> eyes;
      cascade_eye_.detectMultiScale(
          face_region, eyes, 1.1, min_neighbor, flags, cv::Size(10, 10));
      if (!eyes.empty()) {
        return true;
      }
    }
    return false;
  }

 private:
  cv::CascadeClassifier cascade_face_;
  cv::CascadeClassifier cascade_eye_;
};

const int kMaxHeightWidth = 1000;

void checkAndResize(cv::Mat& img) {
  if (img.rows > kMaxHeightWidth ||
      img.cols > kMaxHeightWidth) {
    float ratio = std::max(
        static_cast<float>(img.rows) / kMaxHeightWidth,
        static_cast<float>(img.cols) / kMaxHeightWidth);
    const int new_rows = cvRound(img.rows / ratio);
    const int new_cols = cvRound(img.cols / ratio);
    cv::Mat new_img;
    cv::resize(img, new_img, cv::Size(new_cols, new_rows));
    std::swap(img, new_img);
  }
}

static PyMethodDef zcvMethods[] = {
  {"init_cv_face_detector", initCvFaceDetector, METH_VARARGS},
  {"free_cv_face_detector", freeCvFaceDetector, METH_VARARGS},
  {"detect_face", detectFace, METH_VARARGS},
  {NULL, NULL}
};

void initzcv() {
  (void) Py_InitModule("zcv", zcvMethods);
}

PyObject* initCvFaceDetector(PyObject* self, PyObject* args) {
  char* cascade_dir;
  if (!PyArg_ParseTuple(args, "s", &cascade_dir)) {
    return NULL;
  }
  FaceDetector* detector = new FaceDetector;
  if (!detector->loadCascades(cascade_dir)) {
    delete detector;
    char error[300];
    snprintf(error, 300, "couldn't load face cascades from %s", cascade_dir);
    PyErr_SetString(PyExc_IOError, error);
    return NULL;
  }
  return PyLong_FromVoidPtr(reinterpret_cast<void*>(detector));
}

PyObject* freeCvFaceDetector(PyObject* self, PyObject* args) {
  PyObject* ptr;
  if (!PyArg_ParseTuple(args, "O", &ptr)) {
    return NULL;
  }
  delete reinterpret_cast<FaceDetector*>(PyLong_AsVoidPtr(ptr));
  Py_RETURN_NONE;
}

PyObject* detectFace(PyObject* self, PyObject* args) {
  PyObject* ptr;
  char* filename;
  if (!PyArg_ParseTuple(args, "Os", &ptr, &filename)) {
    return NULL;
  }
  FaceDetector* detector = reinterpret_cast<FaceDetector*>(PyLong_AsVoidPtr(ptr));
  cv::Mat img = cv::imread(filename, CV_LOAD_IMAGE_COLOR);
  if (img.empty()) {
    char error[300];
    snprintf(error, 300, "failed to load %s", filename);
    PyErr_SetString(PyExc_IOError, error);
    return NULL;
  }
  /*
  cv::Mat img_gray;
  cv::cvtColor(img, img_gray, CV_BGR2GRAY);
  cv::equalizeHist(img_gray, img_gray);
  std::swap(img, img_gray);
  */
  checkAndResize(img);
  if (detector->detect(img)) {
    Py_RETURN_TRUE;
  } else {
    Py_RETURN_FALSE;
  }
}

