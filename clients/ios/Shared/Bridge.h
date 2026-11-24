#include <stdint.h>

uint64_t fc_ios_start(void *config, int32_t size, int32_t mode);
int32_t fc_ios_state(uint64_t handle);
int32_t fc_ios_write(uint64_t handle, void *data, int32_t size, int32_t family);
int32_t fc_ios_read(uint64_t handle, void *output, int32_t capacity, int32_t *family, int32_t wait);
void fc_ios_cancel(uint64_t handle);
int32_t fc_ios_stop(uint64_t handle);
int32_t fc_ios_commit_start(uint64_t handle);
int32_t fc_ios_handles(void);
int32_t fc_ios_validate_material(void *data, int32_t size);
