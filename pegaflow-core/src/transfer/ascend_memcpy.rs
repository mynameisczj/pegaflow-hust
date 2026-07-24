//! Ascend DMA copy-engine backend.
//!
//! Submits copies via `aclrtMemcpyBatchAsync` (CANN 8.5+) in one batch call,
//! then synchronizes once.  This avoids both TS queue overflow (507001) and
//! the per-copy sync fallback that blocks for seconds on a busy NPU.

use std::sync::Arc;

use crate::device::{DeviceStream, ascend};

use super::{CopyDesc, TransferBackend};

pub struct AscendMemcpyBackend {
    device_id: i32,
}

impl AscendMemcpyBackend {
    pub fn new(device_id: i32) -> Self {
        Self { device_id }
    }
}

impl TransferBackend for AscendMemcpyBackend {
    fn h2d(&self, copies: &[CopyDesc], stream: &Arc<DeviceStream>) -> Result<(), String> {
        let ascend_stream = match stream.as_ref() {
            DeviceStream::Ascend(s) => s,
            _ => return Err("AscendMemcpyBackend::h2d called with non-Ascend stream".into()),
        };
        if copies.is_empty() { return Ok(()); }
        let batch: Vec<(u64, *mut u8, usize)> = copies.iter()
            .map(|c| (c.device, c.host, c.size)).collect();
        ascend::memcpy_batch_h2d(&batch, self.device_id, ascend_stream)
    }

    fn d2h(&self, copies: &[CopyDesc], stream: &Arc<DeviceStream>) -> Result<(), String> {
        let ascend_stream = match stream.as_ref() {
            DeviceStream::Ascend(s) => s,
            _ => return Err("AscendMemcpyBackend::d2h called with non-Ascend stream".into()),
        };
        if copies.is_empty() { return Ok(()); }
        let batch: Vec<(u64, *mut u8, usize)> = copies.iter()
            .map(|c| (c.device, c.host, c.size)).collect();
        ascend::memcpy_batch_d2h(&batch, self.device_id, ascend_stream)
    }

    fn name(&self) -> &'static str { "ascend_batch" }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn ascend_backend_name() {
        assert_eq!(AscendMemcpyBackend::new(0).name(), "ascend_batch");
    }
}
