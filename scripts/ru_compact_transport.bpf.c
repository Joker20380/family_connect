#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include "ru_compact_protocol.h"

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, FC_RING_BYTES);
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, FC_KINDS);
    __type(key, unsigned int);
    __type(value, struct fc_stats);
} counters SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, unsigned int);
    __type(value, struct fc_config);
} config SEC(".maps");

struct syscall_enter {
    unsigned long long common;
    long number;
    unsigned long arguments[6];
};

SEC("tracepoint/syscalls/sys_enter_getpgid")
int transport(struct syscall_enter *context)
{
    unsigned int zero = 0;
    struct fc_config *settings = bpf_map_lookup_elem(&config, &zero);
    if (!settings || !settings->enabled || (bpf_get_current_pid_tgid() >> 32) != settings->target)
        return 0;
    unsigned int argument = context->arguments[0];
    if ((argument & 0xffffff00) != FC_MAGIC)
        return 0;
    unsigned int kind = argument & 255;
    struct fc_stats *global = bpf_map_lookup_elem(&counters, &zero);
    if (!global)
        return 0;
    unsigned int bytes = fc_size(kind);
    if (!bytes) {
        global->overflow = 1;
        return 0;
    }
    struct fc_stats *stats = bpf_map_lookup_elem(&counters, &kind);
    if (!stats) {
        global->overflow = 1;
        return 0;
    }
    if (stats->hits == ~0ULL) {
        global->overflow = 1;
        return 0;
    }
    stats->hits++;
    unsigned int cpu = bpf_get_smp_processor_id();
    if (cpu >= FC_CPUS || global->sequence >= 0xffffffffULL) {
        stats->overflow++;
        global->overflow = 1;
        return 0;
    }
    stats->attempted++;
    global->sequence++;
    struct fc_record record = {};
    record.header.mono_ns = bpf_ktime_get_ns();
    record.header.sequence = global->sequence;
    record.header.version = FC_VERSION;
    record.header.kind = kind;
    record.header.cpu = cpu;
    record.header.bytes = bytes;
    record.payload[0] = global->sequence;
    record.payload[1] = kind;
    long result = bpf_ringbuf_output(&events, &record, bytes, 0);
    if (result == 0)
        stats->submitted++;
    else
        stats->failed++;
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
