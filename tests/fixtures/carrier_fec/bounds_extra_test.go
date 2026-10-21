package telemost

import (
	"context"
	"sync"
	"testing"
	"time"
)

func TestFragmentLayoutAllLengths(test *testing.T) {
	for length := 0; length <= MaxMessageSize; length++ {
		sources := max(1, (length+labSymbol-1)/labSymbol)
		groups := (sources + labSources - 1) / labSources
		covered := 0
		for group := 0; group < groups; group++ {
			count := min(labSources, sources-group*labSources)
			if count < 1 || count > 8 || group >= 8 {
				test.Fatal("group range", length)
			}
			for index := 0; index < count; index++ {
				start := (group*labSources + index) * labSymbol
				size := min(labSymbol, length-start)
				if start != covered || size < 0 || size > labSymbol {
					test.Fatal("offset/length", length)
				}
				covered += size
			}
		}
		if covered != length || sources+groups*labRepairs > 80 {
			test.Fatal("coverage", length)
		}
	}
	test.Log("all 65537 lengths: exact contiguous geometry; no payload allocation/traffic")
}

func TestFragmentHeldMemoryAndConcurrentClose(test *testing.T) {
	for _, mode := range []string{"S", "SF"} {
		left, right := labTestPair(mode)
		for message := uint32(1); message <= 17; message++ {
			parts, _ := left.encode(context.Background(), 1, message, labBody(65536))
			for _, part := range parts {
				if mode == "S" && part[40] == 0 && part[41] == 0 && part[42] == 0 {
					continue
				}
				if mode == "SF" && part[42] >= 7 {
					continue
				}
				if right.ingest(part) != nil {
					test.Fatal("incomplete delivered")
				}
			}
		}
		metrics := right.snapshot()
		if metrics.Pending != 16 || metrics.Held > labHeldLimit || metrics.Capacity == 0 || metrics.Held < 800000 {
			test.Fatal("memory bound", metrics)
		}
		test.Logf("HELD mode=%s pending=%d held=%d cap=%d", mode, metrics.Pending, metrics.Held, labHeldLimit)
		right.now = func() time.Time { return time.Now().Add(11 * time.Second) }
		right.prune()
		if right.snapshot().Held != 0 || right.snapshot().Pending != 0 {
			test.Fatal("silent lifetime")
		}
		var wait sync.WaitGroup
		for thread := 0; thread < 4; thread++ {
			wait.Add(1)
			go func() {
				defer wait.Done()
				for message := uint32(100); message < 110; message++ {
					left.encode(context.Background(), 1, message, labBody(65536))
					left.snapshot()
				}
			}()
		}
		left.close()
		wait.Wait()
		if _, err := left.encode(context.Background(), 1, 200, []byte{1}); err != ErrClosed {
			test.Fatal("encode after close", err)
		}
	}
}
