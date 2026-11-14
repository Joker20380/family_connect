#ifndef FC_COMPACT_PROTOCOL_H
#define FC_COMPACT_PROTOCOL_H

#define FC_VERSION 3
#define FC_RING_BYTES 32768
#define FC_KINDS 32
#define FC_CPUS 2
#define FC_RETAINED 4096
#define FC_MAGIC 0x3f000000

struct fc_header {
    unsigned long long mono_ns;
    unsigned int sequence;
    unsigned char version, kind, cpu, bytes;
};

struct fc_record {
    struct fc_header header;
    unsigned long long payload[4];
};

struct fc_stats {
    unsigned long long hits, attempted, submitted, failed, discarded, overflow, sequence;
};

struct fc_config {
    unsigned int target, enabled;
};

static inline unsigned int fc_size(unsigned int kind)
{
    switch (kind) {
    case 24: case 25: return 16;
    case 1: case 2: case 3: case 4: case 5: case 8: case 9:
    case 17: case 18: case 19: case 23: return 24;
    case 6: case 7: case 16: case 27: case 28: case 29: return 32;
    case 10: case 14: case 26: return 40;
    case 11: case 12: case 13: case 15: return 48;
    default: return 0;
    }
}

_Static_assert(sizeof(struct fc_header) == 16, "wire header");
_Static_assert(sizeof(struct fc_record) == 48, "maximum record");
_Static_assert(_Alignof(struct fc_record) == 8, "record alignment");
_Static_assert(sizeof(struct fc_stats) == 56, "per-CPU terminal map value");
#endif
