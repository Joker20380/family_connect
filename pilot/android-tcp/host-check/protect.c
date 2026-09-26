#include <stdint.h>
int fcProtect(uintptr_t owner, int fd) { return 1; }
void fcRelease(uintptr_t owner) {}
