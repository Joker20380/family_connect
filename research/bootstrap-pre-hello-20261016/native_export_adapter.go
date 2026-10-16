package nativeexport

import "context"

func Export(ctx context.Context, attempt int64) map[string]any {
	retainStartup(ctx)
	stats := map[string]any{}
	startupStats(stats, attempt)
	return stats
}
