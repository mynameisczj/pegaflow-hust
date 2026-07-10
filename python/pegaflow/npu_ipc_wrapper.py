"""CANN IPC Wrapper for cross-process NPU memory sharing.

This module provides a wrapper class for PyTorch NPU tensors that enables
cross-process NPU memory sharing via CANN IPC keys. The wrapper can be
serialized (via pickle) and sent across process boundaries.

This is the Ascend equivalent of CudaIPCWrapper (ipc_wrapper.py).

The IPC primitives are implemented via two paths:
1. C extension (``npu_ipc_bindings._npu_ipc``) — preferred for lower overhead.
2. ctypes fallback against ``libascendcl.so`` — always available.
"""

import ctypes
import threading

import torch


# ---------------------------------------------------------------------------
# CANN IPC constants
# ---------------------------------------------------------------------------

ACL_SUCCESS = 0
ACL_RT_IPC_MEM_EXPORT_FLAG_DEFAULT = 0x0
ACL_RT_IPC_MEM_IMPORT_FLAG_DEFAULT = 0x0
NPU_IPC_MAX_KEY_LEN = 256


# ---------------------------------------------------------------------------
# CANN IPC C-level bindings via ctypes (fallback path)
# ---------------------------------------------------------------------------

def _load_libascendcl():
    """Locate and load libascendcl.so from CANN runtime."""
    import os

    cann_home = os.environ.get("ASCEND_HOME_PATH")
    if cann_home:
        paths = [os.path.join(cann_home, "lib64", "libascendcl.so")]
    else:
        paths = ["libascendcl.so"]

    for p in paths:
        try:
            return ctypes.CDLL(p)
        except OSError:
            continue
    raise RuntimeError(
        "Cannot load libascendcl.so. Set ASCEND_HOME_PATH or ensure the CANN runtime "
        "is in LD_LIBRARY_PATH."
    )


_libascendcl = None
_libascendcl_lock = threading.Lock()


def _lib():
    global _libascendcl
    with _libascendcl_lock:
        if _libascendcl is None:
            _libascendcl = _load_libascendcl()
            _libascendcl.aclrtIpcMemGetExportKey.argtypes = [
                ctypes.c_void_p,
                ctypes.c_size_t,
                ctypes.c_char_p,
                ctypes.c_size_t,
                ctypes.c_uint64,
            ]
            _libascendcl.aclrtIpcMemGetExportKey.restype = ctypes.c_int
            _libascendcl.aclrtIpcMemImportByKey.argtypes = [
                ctypes.POINTER(ctypes.c_void_p),
                ctypes.c_char_p,
                ctypes.c_uint64,
            ]
            _libascendcl.aclrtIpcMemImportByKey.restype = ctypes.c_int
            _libascendcl.aclrtIpcMemClose.argtypes = [
                ctypes.c_char_p,
            ]
            _libascendcl.aclrtIpcMemClose.restype = ctypes.c_int
        return _libascendcl


def _npu_ipc_export_key_ctypes(dev_ptr: int, size: int) -> bytes:
    """Export a CANN IPC key for the given NPU memory region (ctypes path).

    Returns the key as bytes suitable for serialisation.
    """
    key_buf = ctypes.create_string_buffer(NPU_IPC_MAX_KEY_LEN)
    ret = _lib().aclrtIpcMemGetExportKey(
        ctypes.c_void_p(dev_ptr),
        ctypes.c_size_t(size),
        key_buf,
        ctypes.c_size_t(NPU_IPC_MAX_KEY_LEN),
        ctypes.c_uint64(ACL_RT_IPC_MEM_EXPORT_FLAG_DEFAULT),
    )
    if ret != ACL_SUCCESS:
        raise RuntimeError(
            f"aclrtIpcMemGetExportKey failed with error {ret}"
            f" for dev_ptr={hex(dev_ptr)} size={size}"
        )
    return key_buf.value


def _npu_ipc_import_key_ctypes(key: bytes) -> int:
    """Import NPU memory via a CANN IPC key (ctypes path).

    Returns the device virtual address (integer) of the imported memory.
    """
    dev_ptr = ctypes.c_void_p()
    ret = _lib().aclrtIpcMemImportByKey(
        ctypes.byref(dev_ptr),
        ctypes.c_char_p(key),
        ctypes.c_uint64(ACL_RT_IPC_MEM_IMPORT_FLAG_DEFAULT),
    )
    if ret != ACL_SUCCESS:
        raise RuntimeError(
            f"aclrtIpcMemImportByKey failed with error {ret} for key={key!r}"
        )
    return dev_ptr.value or 0


def _npu_ipc_close_ctypes(key: bytes) -> None:
    """Release a CANN IPC key (ctypes path). Idempotent."""
    _lib().aclrtIpcMemClose(ctypes.c_char_p(key))


# ---------------------------------------------------------------------------
# Try the C extension for lower overhead
# ---------------------------------------------------------------------------

_C_EXT_AVAILABLE = False
try:
    from npu_ipc_bindings._npu_ipc import (  # type: ignore[import-untyped]
        export_key as _npu_ipc_export_key_c,
        import_key as _npu_ipc_import_key_c,
        close_key as _npu_ipc_close_key_c,
    )
    _C_EXT_AVAILABLE = True
except ImportError:
    pass

_npu_ipc_export_key = _npu_ipc_export_key_c if _C_EXT_AVAILABLE else _npu_ipc_export_key_ctypes
_npu_ipc_import_key = _npu_ipc_import_key_c if _C_EXT_AVAILABLE else _npu_ipc_import_key_ctypes
_npu_ipc_close = _npu_ipc_close_key_c if _C_EXT_AVAILABLE else _npu_ipc_close_ctypes


# ---------------------------------------------------------------------------
# NpuIPCWrapper
# ---------------------------------------------------------------------------


class NpuIPCWrapper:
    """Wrapper for CANN IPC key with tensor metadata.

    This class wraps a PyTorch NPU tensor and extracts its CANN IPC key,
    allowing the tensor memory to be reconstructed in another process via
    ``aclrtIpcMemImportByKey``.  The wrapper is pickle-serialisable so it
    travels through gRPC ``register_context_batch`` unchanged.

    Because CANN IPC relies on memory allocated via ``aclrtMallocPhysical``
    (which vllm-ascend-hust's ``camem_allocator`` provides to PyTorch's
    PluggableAllocator), the wrapped tensor **must** have been allocated by
    that allocator.  Standard ``torch.npu.empty`` tensors allocated through
    the default CANN allocator are **not** IPC-exportable.

    The wrapper stores the NPU device index directly (rather than using
    UUID-based discovery).  Ascend NPU UUIDs may be non-unique (e.g. all
    zero), so UUID-based remapping is unreliable.  This is safe because
    both the vLLM worker and the pegaflow-server process share the same
    ``ASCEND_VISIBLE_DEVICES`` environment variable and device ordering.

    Attributes:
        key: CANN IPC export key bytes (C string from aclrtIpcMemGetExportKey).
        dtype: PyTorch dtype of the tensor.
        shape: Shape tuple of the tensor.
        stride: Stride tuple of the tensor.
        storage_offset: Storage offset (must be zero).
        device_index: NPU device index (relative to ASCEND_VISIBLE_DEVICES).
    """

    # ------------------------------------------------------------------
    # Core IPC export / import
    # ------------------------------------------------------------------

    def __init__(self, tensor: torch.Tensor):
        """Create an IPC wrapper from an NPU tensor.

        The tensor must be allocated through ``camem_allocator`` (i.e. via
        ``aclrtMallocPhysical``), otherwise ``aclrtIpcMemGetExportKey`` will
        fail.
        """
        if tensor.storage_offset() != 0:
            raise ValueError("Tensor must have zero storage offset")

        storage = tensor.untyped_storage()
        ptr = storage.data_ptr()
        nbytes = storage.nbytes()

        if ptr == 0:
            raise RuntimeError("Cannot export IPC key for a tensor with data_ptr() == 0")

        self.key = _npu_ipc_export_key(ptr, nbytes)
        self.dtype = tensor.dtype
        self.shape = tensor.shape
        self.stride = tensor.stride()
        self.storage_offset = tensor.storage_offset()

        # Store the device index directly.  Unlike CUDA where
        # CUDA_VISIBLE_DEVICES remapping requires UUID-based discovery,
        # Ascend NPU UUIDs are often non-unique (e.g. all zero).  Both
        # the vLLM worker and pegaflow-server share the same
        # ASCEND_VISIBLE_DEVICES environment, so the raw index is stable.
        self.device_index = tensor.device.index

    def to_tensor(self) -> torch.Tensor:
        """Reconstruct a tensor that shares the original NPU memory.

        Calls ``aclrtIpcMemImportByKey`` with the key exported in
        ``__init__``, then constructs a ``torch.Tensor`` that points to
        the imported device virtual address.
        """
        device = self.device_index

        dev_ptr = _npu_ipc_import_key(self.key)

        if dev_ptr == 0:
            raise RuntimeError("aclrtIpcMemImportByKey returned NULL pointer")

        numel = 1
        for s in self.shape:
            numel *= s
        elem_size = self.dtype.itemsize
        total_bytes = numel * elem_size

        t = torch.tensor([], device=f"npu:{device}", dtype=self.dtype)
        stride = getattr(self, "stride", None)
        storage_offset = getattr(self, "storage_offset", 0)

        # TODO(pegaflow-hust): torch_npu does not expose a public API
        # equivalent to `torch.UntypedStorage._new_shared_cuda`.  When
        # torch_npu adds `_new_shared_npu`, replace the raw-pointer
        # construction below.
        ptr_as_int = dev_ptr
        storage = torch.UntypedStorage.from_buffer(
            (ctypes.c_uint8 * total_bytes).from_address(ptr_as_int),
            byte_order="native",
        )

        if stride is None:
            t.set_(storage, storage_offset)
            return t.view(self.shape)
        t.set_(storage, storage_offset, self.shape, stride)
        return t

    # ------------------------------------------------------------------
    # Pickle protocol
    # ------------------------------------------------------------------

    def __getstate__(self):
        return (
            self.key,
            self.dtype,
            self.shape,
            self.stride,
            self.storage_offset,
            self.device_index,
        )

    def __setstate__(self, state):
        (
            self.key,
            self.dtype,
            self.shape,
            self.stride,
            self.storage_offset,
            self.device_index,
        ) = state

    def __eq__(self, other) -> bool:
        if not isinstance(other, NpuIPCWrapper):
            return False
        return (
            self.key == other.key
            and self.dtype == other.dtype
            and self.shape == other.shape
            and getattr(self, "stride", None) == getattr(other, "stride", None)
            and getattr(self, "storage_offset", 0) == getattr(other, "storage_offset", 0)
            and self.device_index == other.device_index
        )

    def __repr__(self) -> str:
        return (
            f"NpuIPCWrapper(shape={self.shape}, dtype={self.dtype}, "
            f"stride={getattr(self, 'stride', None)}, "
            f"device_index={self.device_index})"
        )


__all__ = ["NpuIPCWrapper"]