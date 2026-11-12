import ctypes
import os
import site

import numpy as np


def _preload_nvidia_libs() -> None:
    """Pre-load cuDNN/cuBLAS from nvidia-* uv/pip packages so onnxruntime-gpu can find them."""
    libs = [
        "nvidia/cudnn/lib/libcudnn.so.9",
        "nvidia/cublas/lib/libcublas.so.12",
        "nvidia/cufft/lib/libcufft.so.11",
    ]
    site_dirs = site.getsitepackages()
    try:
        site_dirs = site_dirs + [site.getusersitepackages()]
    except AttributeError:
        pass
    for lib in libs:
        for site_dir in site_dirs:
            path = os.path.join(site_dir, lib)
            if os.path.exists(path):
                try:
                    ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    pass
                break


_preload_nvidia_libs()

# Suppress flake8 error for import order, since onnxruntime must be imported after preloading nvidia libs
import onnxruntime as ort

from .hub import resolve_file


class Inference:
    def __init__(
        self,
        model_path: str | os.PathLike,
        input_name: str = "x",
        batch_size: int = 256,
    ):
        """Runs an ONNX model batch-wise.

        Args:
            model_path (str | os.PathLike): Path of the ONNX model, either local or on Hugging Face
                as hf://<namespace>/<name>[@<revision>]/<path>.
            input_name (str, optional): Name of the model input. Defaults to "x".
            batch_size (int, optional): The batch size to use. Defaults to 256.
        """
        # Set the thread count explicitly: otherwise onnxruntime tries to pin its threads to
        # the physical core ids, which fails with "pthread_setaffinity_np ... Invalid argument"
        # inside Slurm/cgroup CPU allocations.
        options = ort.SessionOptions()
        options.intra_op_num_threads = len(os.sched_getaffinity(0))
        self.model = ort.InferenceSession(
            resolve_file(model_path),
            sess_options=options,
            providers=self.__get_providers(),
        )
        self.input_name = input_name
        self.batch_size = batch_size

    def __get_providers(self):
        ort.set_default_logger_severity(4)  # suppress CUDA provider load errors
        available = ort.get_available_providers()
        ort.set_default_logger_severity(2)  # restore to WARNING
        if "CUDAExecutionProvider" in available:
            return ["CUDAExecutionProvider", "CPUExecutionProvider"]
        else:
            return ["CPUExecutionProvider"]

    def __call__(self, data: np.ndarray) -> np.ndarray:
        results = []
        for i in range(0, len(data), self.batch_size):
            batch = data[i : i + self.batch_size]
            results.append(self.model.run(None, {self.input_name: batch})[0])
        data = np.concatenate(results, axis=0)
        return data
