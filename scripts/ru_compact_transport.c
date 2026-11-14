#define _GNU_SOURCE
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <errno.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include "ru_compact_protocol.h"

struct control {
    atomic_int ready, done, stop;
    unsigned long long baseline_throttled, begin_ns, end_ns, trigger_throttled;
    unsigned long long calls[FC_CPUS][FC_KINDS];
};

static struct control *control;
static struct fc_record retained[FC_RETAINED];
static unsigned long long received[FC_CPUS][FC_KINDS];
static unsigned int sequences[FC_CPUS], starts, ends;
static unsigned int started[FC_CPUS], ended[FC_CPUS];
static unsigned long long boundary_errors, occupied_bytes, drain_cpu;
static unsigned long long seen, decoded, invalid, evicted, gaps, previous_callback, max_pause;
static unsigned long long maximum_cpu, maximum_wall, violations;
static int mode;

static void require(int condition, const char *label)
{
    if (!condition) { fprintf(stderr, "transport_error:%s\n", label); exit(4); }
}

static unsigned long long clock_ns(clockid_t clock_id)
{
    struct timespec value;
    require(clock_gettime(clock_id, &value) == 0, "clock");
    return (unsigned long long)value.tv_sec * 1000000000ULL + value.tv_nsec;
}

static void guard(unsigned long long cpu, unsigned long long wall)
{
    cpu = clock_ns(CLOCK_PROCESS_CPUTIME_ID) - cpu;
    wall = clock_ns(CLOCK_MONOTONIC) - wall;
    if (cpu > maximum_cpu) maximum_cpu = cpu;
    if (wall > maximum_wall) maximum_wall = wall;
    if (cpu > 200000000ULL || wall > 10000000000ULL) violations = 1;
}

static unsigned long long throttled(void)
{
    FILE *stream = fopen("/sys/fs/cgroup/diagnostic/cpu.stat", "r");
    require(stream != NULL, "cpu_stat");
    char key[80];
    unsigned long long value, result = 0;
    while (fscanf(stream, "%79s %llu", key, &value) == 2)
        if (!strcmp(key, "nr_throttled")) result = value;
    fclose(stream);
    return result;
}

static int consume(void *unused, void *data, size_t size)
{
    (void)unused;
    unsigned long long now = clock_ns(CLOCK_MONOTONIC);
    if (previous_callback && now - previous_callback > max_pause) max_pause = now - previous_callback;
    previous_callback = now;
    seen++;
    if (size < sizeof(struct fc_header) || size > sizeof(struct fc_record)) { invalid++; return 0; }
    const struct fc_record *record = data;
    const struct fc_header *header = &record->header;
    if (header->version != FC_VERSION || header->cpu >= FC_CPUS || !header->sequence ||
        !header->mono_ns || header->bytes != size || fc_size(header->kind) != size) {
        invalid++; return 0;
    }
    decoded++;
    occupied_bytes += (size + 15) & ~7ULL;
    received[header->cpu][header->kind]++;
    if (header->sequence != sequences[header->cpu] + 1) gaps++;
    sequences[header->cpu] = header->sequence;
    if (ended[header->cpu] || (!started[header->cpu] && header->kind != 24)) boundary_errors++;
    if (header->kind == 24) {
        if (started[header->cpu]) boundary_errors++;
        started[header->cpu] = 1; starts++;
    }
    if (header->kind == 25) { ended[header->cpu] = 1; ends++; }
    if (decoded <= FC_RETAINED) memcpy(&retained[decoded - 1], data, size);
    else evicted++;
    if (mode == 4 && decoded >= 200) atomic_store(&control->stop, 1);
    return 0;
}

static void emit(unsigned int cpu, unsigned int kind)
{
    syscall(SYS_getpgid, FC_MAGIC | kind);
    if (kind < FC_KINDS) control->calls[cpu][kind]++;
}

static void pin(unsigned int cpu)
{
    cpu_set_t affinity;
    CPU_ZERO(&affinity); CPU_SET(cpu, &affinity);
    require(sched_setaffinity(0, sizeof(affinity), &affinity) == 0, "pin");
}

static void driver(int descriptor, unsigned int plan[FC_CPUS][FC_KINDS])
{
    FILE *group = fopen("/sys/fs/cgroup/writer1/cgroup.procs", "w");
    require(group != NULL, "workload_cgroup");
    fprintf(group, "%d", getpid()); fclose(group);
    char signal_byte;
    require(read(descriptor, &signal_byte, 1) == 1, "attach_barrier");
    close(descriptor);
    for (unsigned int cpu = 0; cpu < FC_CPUS; cpu++) { pin(cpu); emit(cpu, 24); }
    unsigned long long wait_start = clock_ns(CLOCK_MONOTONIC);
    while (!atomic_load(&control->ready)) {
        require(clock_ns(CLOCK_MONOTONIC) - wait_start < 3000000000ULL, "consumer_barrier");
        usleep(100);
    }
    if (mode == 1) {
        do {
            control->trigger_throttled = throttled();
            require(clock_ns(CLOCK_MONOTONIC) - wait_start < 3000000000ULL, "quota_trigger");
        } while (control->trigger_throttled <= control->baseline_throttled);
    }
    control->begin_ns = clock_ns(CLOCK_MONOTONIC);
    for (unsigned int cpu = 0; cpu < FC_CPUS; cpu++) {
        pin(cpu);
        for (unsigned int kind = 1; kind < FC_KINDS && !atomic_load(&control->stop); kind++) {
            if (kind == 24 || kind == 25) continue;
            for (unsigned int count = 0; count < plan[cpu][kind] && !atomic_load(&control->stop); count++)
                emit(cpu, kind);
        }
        if (mode == 3) syscall(SYS_getpgid, FC_MAGIC | 32);
    }
    control->end_ns = clock_ns(CLOCK_MONOTONIC);
    if (mode != 4)
        for (unsigned int cpu = 0; cpu < FC_CPUS; cpu++) { pin(cpu); emit(cpu, 25); }
    atomic_store(&control->done, 1);
    exit(0);
}

int main(int argc, char **argv)
{
    unsigned long long setup_cpu = clock_ns(CLOCK_PROCESS_CPUTIME_ID), setup_wall = clock_ns(CLOCK_MONOTONIC);
    require(argc == 4, "arguments");
    require(access("/run/fc-attribution-disposable-vm", F_OK) == 0, "isolated_vm_required");
    require(libbpf_num_possible_cpus() == FC_CPUS, "cpu_count");
    mode = atoi(argv[3]);
    require(mode >= 0 && mode <= 4, "mode");
    unsigned int plan[FC_CPUS][FC_KINDS] = {};
    FILE *input = fopen(argv[2], "r");
    require(input != NULL, "plan");
    unsigned int cpu, kind, count;
    while (fscanf(input, "%u %u %u", &cpu, &kind, &count) == 3) {
        require(cpu < FC_CPUS && kind < FC_KINDS && fc_size(kind) && count <= 4096, "plan_range");
        plan[cpu][kind] = count;
    }
    fclose(input);
    control = mmap(NULL, sizeof(*control), PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    require(control != MAP_FAILED, "control_memory");
    int channel[2]; require(pipe(channel) == 0, "barrier_pipe");
    pid_t child = fork(); require(child >= 0, "driver_fork");
    if (!child) { close(channel[1]); driver(channel[0], plan); }
    close(channel[0]);
    struct bpf_object *object = bpf_object__open_file(argv[1], NULL);
    require(!libbpf_get_error(object), "object_open");
    require(bpf_object__load(object) == 0, "object_load");
    int config_fd = bpf_object__find_map_fd_by_name(object, "config");
    int counter_fd = bpf_object__find_map_fd_by_name(object, "counters");
    int ring_fd = bpf_object__find_map_fd_by_name(object, "events");
    unsigned int zero = 0;
    struct fc_config settings = { .target = child, .enabled = 1 };
    require(bpf_map_update_elem(config_fd, &zero, &settings, BPF_ANY) == 0, "config_update");
    struct bpf_link *link = bpf_program__attach(bpf_object__find_program_by_name(object, "transport"));
    require(!libbpf_get_error(link), "attach");
    struct ring_buffer *ring = ring_buffer__new(ring_fd, consume, NULL, NULL);
    require(ring != NULL, "ring_consumer");
    require(write(channel[1], "1", 1) == 1, "attached_release"); close(channel[1]);
    guard(setup_cpu, setup_wall);
    unsigned long long begin = clock_ns(CLOCK_MONOTONIC), consume_cpu = 0;
    while (!atomic_load(&control->done)) {
        unsigned long long cpu_begin = clock_ns(CLOCK_PROCESS_CPUTIME_ID), wall_begin = clock_ns(CLOCK_MONOTONIC);
        require(wall_begin - begin < 10000000000ULL, "runtime");
        require(ring_buffer__consume_n(ring, 256) >= 0, "consume");
        if (starts == FC_CPUS && !atomic_load(&control->ready)) {
            if (mode == 2) {
                struct fc_stats initial[FC_CPUS] = {};
                for (unsigned int index = 0; index < FC_CPUS; index++) initial[index].sequence = 0xffffffffULL;
                require(bpf_map_update_elem(counter_fd, &zero, initial, BPF_ANY) == 0, "counter_fault_seed");
            }
            control->baseline_throttled = throttled();
            atomic_store(&control->ready, 1);
            if (mode == 1) {
                while (!atomic_load(&control->done) && clock_ns(CLOCK_MONOTONIC) - wall_begin < 2000000000ULL) {}
            }
        }
        consume_cpu += clock_ns(CLOCK_PROCESS_CPUTIME_ID) - cpu_begin;
        guard(cpu_begin, wall_begin);
        if (!atomic_load(&control->done)) usleep(100);
    }
    unsigned long long stop_begin = clock_ns(CLOCK_MONOTONIC);
    unsigned long long stop_cpu = clock_ns(CLOCK_PROCESS_CPUTIME_ID);
    int child_status; require(waitpid(child, &child_status, 0) == child, "driver_join");
    require(WIFEXITED(child_status) && WEXITSTATUS(child_status) == 0, "driver_status");
    settings.enabled = 0;
    require(bpf_map_update_elem(config_fd, &zero, &settings, BPF_ANY) == 0, "disable");
    require(bpf_link__destroy(link) == 0, "detach");
    struct fc_stats terminal[FC_KINDS][FC_CPUS], after[FC_KINDS][FC_CPUS];
    for (unsigned int index = 0; index < FC_KINDS; index++)
        require(bpf_map_lookup_elem(counter_fd, &index, terminal[index]) == 0, "terminal_read");
    int drained;
    do {
        unsigned long long cpu_begin = clock_ns(CLOCK_PROCESS_CPUTIME_ID), wall_begin = clock_ns(CLOCK_MONOTONIC);
        drained = ring_buffer__consume_n(ring, 256); require(drained >= 0, "terminal_drain");
        drain_cpu += clock_ns(CLOCK_PROCESS_CPUTIME_ID) - cpu_begin;
        guard(cpu_begin, wall_begin);
        require(clock_ns(CLOCK_MONOTONIC) - stop_begin < 8000000000ULL, "stop_deadline");
    } while (drained);
    for (unsigned int index = 0; index < FC_KINDS; index++)
        require(bpf_map_lookup_elem(counter_fd, &index, after[index]) == 0, "terminal_recheck");
    require(!memcmp(terminal, after, sizeof(terminal)), "terminal_changed");
    unsigned long long stop_ns = clock_ns(CLOCK_MONOTONIC) - stop_begin;
    guard(stop_cpu, stop_begin);
    unsigned long long save_cpu = clock_ns(CLOCK_PROCESS_CPUTIME_ID), save_wall = clock_ns(CLOCK_MONOTONIC);
    printf("{\"mode\":%d,\"header_bytes\":%zu,\"max_record_bytes\":%zu,\"alignment\":%zu,", mode, sizeof(struct fc_header), sizeof(struct fc_record), _Alignof(struct fc_record));
    printf("\"received\":%llu,\"decoded\":%llu,\"retained\":%llu,\"evicted\":%llu,\"invalid\":%llu,\"sequence_errors\":%llu,", seen, decoded, decoded - evicted, evicted, invalid, gaps);
    printf("\"boundary_errors\":%llu,\"occupied_bytes\":%llu,\"drain_cpu_ns\":%llu,", boundary_errors, occupied_bytes, drain_cpu);
    printf("\"starts\":%u,\"ends\":%u,\"detached\":true,\"terminal_stable\":true,\"drain_ns\":%llu,", starts, ends, stop_ns);
    printf("\"driver_ns\":%llu,\"max_consumer_pause_ns\":%llu,\"consumer_cpu_ns\":%llu,\"batch_cpu_max_ns\":%llu,\"batch_wall_max_ns\":%llu,\"guard_violations\":%llu,", control->end_ns-control->begin_ns, max_pause, consume_cpu, maximum_cpu, maximum_wall, violations);
    printf("\"throttled_before\":%llu,\"throttled_at_trigger\":%llu,\"terminal\":[", control->baseline_throttled, control->trigger_throttled);
    int separator = 0;
    for (unsigned int cpu_index = 0; cpu_index < FC_CPUS; cpu_index++) {
        for (unsigned int index = 0; index < FC_KINDS; index++) {
            const struct fc_stats *stats = &terminal[index][cpu_index];
            if (!stats->hits && !stats->overflow && !control->calls[cpu_index][index]) continue;
            printf("%s{\"cpu\":%u,\"kind\":%u,\"ledger\":%llu,\"hits\":%llu,\"attempted\":%llu,\"submitted\":%llu,\"failed\":%llu,\"discarded\":%llu,\"overflow\":%llu,\"received\":%llu}", separator ? "," : "", cpu_index, index, control->calls[cpu_index][index], stats->hits, stats->attempted, stats->submitted, stats->failed, stats->discarded, stats->overflow, received[cpu_index][index]);
            separator = 1;
        }
    }
    printf("]}\n"); fflush(stdout);
    fprintf(stderr, "FC_SAVE_COST {\"cpu_ns\":%llu,\"wall_ns\":%llu}\n", clock_ns(CLOCK_PROCESS_CPUTIME_ID)-save_cpu, clock_ns(CLOCK_MONOTONIC)-save_wall);
    ring_buffer__free(ring); bpf_object__close(object); munmap(control, sizeof(*control));
    return 0;
}
