/* SPDX-License-Identifier: MIT */
#include "type.h"
#include <assert.h>
#include <stddef.h>

int main(void) {
    u16_range_t range;
    const char *invalid[] = {"65536", "4294967295", "65536-65537", "0-65536",
        "0-", "-0", "+1", " 1", "0--1", "2-1", "1x", "18446744073709551616"};
    for (size_t i = 0; i < sizeof(invalid)/sizeof(invalid[0]); ++i)
        assert(!u16_range_from_string(&range, invalid[i]));
    assert(u16_range_from_string(&range, "0"));
    assert(u16_range_lo(range) == 0 && u16_range_hi(range) == 0);
    assert(u16_range_from_string(&range, "65535"));
    assert(u16_range_lo(range) == 65535 && u16_range_hi(range) == 65535);
    assert(u16_range_from_string(&range, "0-65535"));
    assert(u16_range_lo(range) == 0 && u16_range_hi(range) == 65535);
    return 0;
}
