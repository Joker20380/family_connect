package localwrite

import "context"

type scopeKey struct{}

func WithCompletion(ctx context.Context) context.Context {
	return context.WithValue(ctx, scopeKey{}, true)
}
func Enabled(ctx context.Context) bool { enabled, _ := ctx.Value(scopeKey{}).(bool); return enabled }
