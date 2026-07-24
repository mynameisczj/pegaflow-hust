// C wrapper for aclrtMemcpyBatchAsync — avoids Rust FFI struct-layout issues.
// Compiled by cc and linked into pegaflow-core.
#include <acl/acl.h>
#include <stdint.h>
#include <stdlib.h>

int pega_aclrt_memcpy_batch_h2d(
    uint64_t *dsts,       // device addresses
    uint64_t *srcs,       // host addresses
    uint64_t *sizes,      // copy sizes
    uint64_t num_batches,
    int32_t device_id,
    aclrtStream stream)
{
    if (num_batches == 0) return ACL_SUCCESS;

    // Build location descriptors
    aclrtMemLocation host_loc = {.id = 0, .type = ACL_MEM_LOCATION_TYPE_HOST};
    aclrtMemLocation device_loc = {.id = (uint32_t)device_id, .type = ACL_MEM_LOCATION_TYPE_DEVICE};

    aclrtMemcpyBatchAttr attr = {.dstLoc = device_loc, .srcLoc = host_loc};
    size_t attr_index = 0;
    size_t fail_index = 0;

    return aclrtMemcpyBatchAsync(
        (void **)dsts, (size_t *)sizes,  // destMaxs = sizes (for H2D, dst is device, destMax >= size)
        (void **)srcs, (size_t *)sizes,
        (size_t)num_batches,
        &attr, &attr_index, 1,
        &fail_index, stream);
}

int pega_aclrt_memcpy_batch_d2h(
    uint64_t *srcs,       // device addresses (source)
    uint64_t *dsts,       // host addresses (destination)
    uint64_t *sizes,      // copy sizes
    uint64_t num_batches,
    int32_t device_id,
    aclrtStream stream)
{
    if (num_batches == 0) return ACL_SUCCESS;

    aclrtMemLocation host_loc = {.id = 0, .type = ACL_MEM_LOCATION_TYPE_HOST};
    aclrtMemLocation device_loc = {.id = (uint32_t)device_id, .type = ACL_MEM_LOCATION_TYPE_DEVICE};

    aclrtMemcpyBatchAttr attr = {.dstLoc = host_loc, .srcLoc = device_loc};
    size_t attr_index = 0;
    size_t fail_index = 0;

    return aclrtMemcpyBatchAsync(
        (void **)dsts, (size_t *)sizes,
        (void **)srcs, (size_t *)sizes,
        (size_t)num_batches,
        &attr, &attr_index, 1,
        &fail_index, stream);
}
