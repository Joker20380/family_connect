package main

import (
	"context"
	"os"
	"runtime"
	"strconv"
	"strings"
	"syscall"
	"time"
)

func startMetrics(ctx context.Context, interval time.Duration, emit func(map[string]any) error) func() {
	if interval == 0 {
		return func() {}
	}
	ctx, cancel := context.WithCancel(ctx)
	done := make(chan struct{})
	go func() {
		defer close(done)
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				var usage syscall.Rusage
				_ = syscall.Getrusage(syscall.RUSAGE_SELF, &usage)
				var memory runtime.MemStats
				runtime.ReadMemStats(&memory)
				fields := map[string]any{"event": "resources", "heap_bytes": memory.HeapAlloc, "heap_sys_bytes": memory.HeapSys, "max_rss_kib": usage.Maxrss, "goroutines": runtime.NumGoroutine(), "cpu_user_s": float64(usage.Utime.Sec) + float64(usage.Utime.Usec)/1e6, "cpu_system_s": float64(usage.Stime.Sec) + float64(usage.Stime.Usec)/1e6}
				fields["gc_cycles"] = memory.NumGC
				fields["pid"] = os.Getpid()
				fields["logical_cpus"] = runtime.NumCPU()
				fields["cpu_source"] = "getrusage(RUSAGE_SELF), all process threads"
				if tasks, err := os.ReadDir("/proc/self/task"); err == nil {
					fields["os_threads"] = len(tasks)
				}
				if entries, err := os.ReadDir("/proc/self/fd"); err == nil {
					sockets := 0
					for _, entry := range entries {
						if target, err := os.Readlink("/proc/self/fd/" + entry.Name()); err == nil && strings.HasPrefix(target, "socket:[") {
							sockets++
						}
					}
					fields["socket_fds"] = sockets
				}
				fields["gc_pause_total_ns"] = memory.PauseTotalNs
				if statm, err := os.ReadFile("/proc/self/statm"); err == nil {
					values := strings.Fields(string(statm))
					if len(values) > 1 {
						if pages, err := strconv.ParseUint(values[1], 10, 64); err == nil {
							fields["rss_bytes"] = pages * uint64(os.Getpagesize())
						}
					}
				}
				if emit(fields) != nil {
					return
				}
			}
		}
	}()
	return func() { cancel(); <-done }
}
