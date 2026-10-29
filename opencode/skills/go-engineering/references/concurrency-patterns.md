# Concurrency patterns with tests (verified with go1.27.3)

Tested on 2026-10-29 with go1.27.3: `go vet` clean, `golangci-lint` `0 issues.`, `go test -race
-count=1` ok, 100.0% statement coverage, and every `synctest` test runs in 0.00s because the bubble
uses a fake clock. The two edge-case tests fail against the previous version of this code:
`FetchAll(..., 0, ...)` blocked forever ("is blocked, want an immediate error", then synctest's
"deadlock: main bubble goroutine has exited but blocked goroutines remain"), and `Debounce` with a
closed input spun until `go test -timeout 15s` killed it. Dependencies: `golang.org/x/sync v0.24.0`
and `github.com/google/go-cmp v0.7.0`.

## Bounded fan-out with fail-fast cancellation, and a debouncer

`FetchAll` is the default shape for "call a slow thing N times": `errgroup.WithContext` cancels the
rest on the first error, `SetLimit` bounds concurrency (no hand-written worker pool), and each
goroutine writes only its own slice index so results need no mutex. Since Go 1.22 the loop variables
are per-iteration, so the closure capture is safe. `limit` is validated because errgroup gives 0 and
negative values special meanings: `SetLimit(0)` admits no goroutines, so the first `g.Go` blocks
forever, and a negative limit removes the bound.

`Debounce` shows the timer-reuse rule (GO-CONC-4): one `time.Timer`, `Reset` on each event, and a
`select` that always includes `ctx.Done()`. It also handles a closed input: a receive from a closed
channel succeeds immediately forever, so `case <-in:` alone turns into a hot loop that keeps
resetting the timer and never fires. The `_, ok := <-in` form detects the close, setting `in = nil`
removes that case from the `select` (a nil channel never becomes ready), and the pending call still
fires before `Debounce` returns.

```go
// Package fanout fetches many items concurrently with a bound and fail-fast cancellation.
package fanout

import (
	"context"
	"fmt"
	"time"

	"golang.org/x/sync/errgroup"
)

// FetchFunc loads one item.
type FetchFunc func(ctx context.Context, id int) (string, error)

// FetchAll runs fetch for every id with at most limit in flight. The first error cancels the rest.
// Results keep the order of ids. limit must be at least 1.
func FetchAll(ctx context.Context, ids []int, limit int, fetch FetchFunc) ([]string, error) {
	// errgroup treats 0 as "no new goroutines" (g.Go would block forever) and a negative value
	// as "no limit", so neither is a valid bound here.
	if limit < 1 {
		return nil, fmt.Errorf("fanout: limit must be >= 1, got %d", limit)
	}
	out := make([]string, len(ids))
	g, ctx := errgroup.WithContext(ctx)
	g.SetLimit(limit)
	for i, id := range ids {
		g.Go(func() error {
			v, err := fetch(ctx, id)
			if err != nil {
				return fmt.Errorf("fetch %d: %w", id, err)
			}
			out[i] = v // each goroutine writes its own index: no data race
			return nil
		})
	}
	if err := g.Wait(); err != nil {
		return nil, err
	}
	return out, nil
}

// Debounce calls fn once after d has passed without another event on in. It returns when ctx
// ends, or when in is closed and any call still pending has fired.
func Debounce(ctx context.Context, in <-chan struct{}, d time.Duration, fn func()) {
	t := time.NewTimer(d)
	t.Stop()
	pending := false
	for {
		select {
		case <-ctx.Done():
			t.Stop()
			return
		case _, ok := <-in:
			if !ok {
				if !pending {
					return
				}
				in = nil // a closed channel is always ready; nil blocks forever, so stop selecting on it
				continue
			}
			pending = true
			t.Reset(d)
		case <-t.C:
			pending = false
			fn()
			if in == nil {
				return
			}
		}
	}
}
```

## Tests: limits, error propagation, and deterministic time

```go
package fanout

import (
	"context"
	"errors"
	"strconv"
	"sync/atomic"
	"testing"
	"testing/synctest"
	"time"

	"github.com/google/go-cmp/cmp"
)

func TestFetchAllOrderAndLimit(t *testing.T) {
	t.Parallel()
	var inFlight, peak atomic.Int32
	fetch := func(_ context.Context, id int) (string, error) {
		n := inFlight.Add(1)
		defer inFlight.Add(-1)
		for {
			p := peak.Load()
			if n <= p || peak.CompareAndSwap(p, n) {
				break
			}
		}
		return strconv.Itoa(id), nil
	}
	got, err := FetchAll(t.Context(), []int{3, 1, 2}, 2, fetch)
	if err != nil {
		t.Fatalf("FetchAll: %v", err)
	}
	if diff := cmp.Diff([]string{"3", "1", "2"}, got); diff != "" {
		t.Errorf("FetchAll mismatch (-want +got):\n%s", diff)
	}
	if p := peak.Load(); p > 2 {
		t.Errorf("peak concurrency = %d, want <= 2", p)
	}
}

var errBoom = errors.New("boom")

func TestFetchAllFirstErrorWins(t *testing.T) {
	t.Parallel()
	fetch := func(_ context.Context, id int) (string, error) {
		if id == 2 {
			return "", errBoom
		}
		return "", nil
	}
	if _, err := FetchAll(t.Context(), []int{1, 2, 3}, 1, fetch); !errors.Is(err, errBoom) {
		t.Fatalf("err = %v, want errBoom", err)
	}
}

// A limit of 0 would make errgroup block forever in g.Go; FetchAll must reject it instead.
func TestFetchAllRejectsBadLimit(t *testing.T) {
	t.Parallel()
	for _, limit := range []int{0, -1} {
		synctest.Test(t, func(t *testing.T) {
			done := make(chan error, 1)
			go func() {
				_, err := FetchAll(t.Context(), []int{1}, limit, func(context.Context, int) (string, error) { return "", nil })
				done <- err
			}()
			synctest.Wait() // returns once the goroutine has exited or is durably blocked
			select {
			case err := <-done:
				if err == nil {
					t.Fatalf("FetchAll(limit=%d) err = nil, want an error", limit)
				}
			default:
				t.Fatalf("FetchAll(limit=%d) is blocked, want an immediate error", limit)
			}
		})
	}
}

// synctest gives the bubble a fake clock: time advances only when every goroutine is blocked,
// so this test is deterministic and takes microseconds, not 300ms.
func TestDebounce(t *testing.T) {
	t.Parallel()
	synctest.Test(t, func(t *testing.T) {
		ctx, cancel := context.WithCancel(t.Context())
		in := make(chan struct{})
		var calls atomic.Int32
		done := make(chan struct{})
		go func() {
			Debounce(ctx, in, 100*time.Millisecond, func() { calls.Add(1) })
			close(done)
		}()

		in <- struct{}{}
		synctest.Sleep(50 * time.Millisecond)
		in <- struct{}{} // resets the timer
		synctest.Sleep(99 * time.Millisecond)
		if got := calls.Load(); got != 0 {
			t.Fatalf("calls before quiet period = %d, want 0", got)
		}
		synctest.Sleep(2 * time.Millisecond)
		if got := calls.Load(); got != 1 {
			t.Fatalf("calls after quiet period = %d, want 1", got)
		}
		cancel()
		<-done
	})
}

// Closing the input must neither spin nor drop a pending call: the pending call fires after the
// quiet period and Debounce returns without waiting for ctx.
func TestDebounceClosedInput(t *testing.T) {
	t.Parallel()
	for _, pending := range []bool{true, false} {
		synctest.Test(t, func(t *testing.T) {
			in := make(chan struct{})
			var calls atomic.Int32
			done := make(chan struct{})
			go func() {
				Debounce(t.Context(), in, 100*time.Millisecond, func() { calls.Add(1) })
				close(done)
			}()
			if pending {
				in <- struct{}{}
			}
			close(in)
			start := time.Now()
			<-done // with the old code this blocks until the test deadline
			want, wantWait := int32(0), time.Duration(0)
			if pending {
				want, wantWait = 1, 100*time.Millisecond
			}
			if got := calls.Load(); got != want {
				t.Errorf("pending=%v: calls = %d, want %d", pending, got, want)
			}
			if got := time.Since(start); got != wantWait {
				t.Errorf("pending=%v: returned after %v, want %v", pending, got, wantWait)
			}
		})
	}
}
```

Notes:

- Inside `synctest.Test`, time advances only when every goroutine in the bubble is durably blocked,
  so `synctest.Sleep(99 * time.Millisecond)` is exact and instant. Do not use real `time.Sleep` for
  synchronization in tests.
- A channel, `time.Timer` or `time.Ticker` created inside the bubble belongs to it; operating on it
  from outside the bubble panics (per the `testing/synctest` package docs).
- To find leaks in a whole package, add `func TestMain(m *testing.M) { goleak.VerifyTestMain(m) }`
  (`go.uber.org/goleak` v1.3.0), or read `/debug/pprof/goroutineleak` (Go 1.27) in a running service.
- Use `wg.Go(func(){ ... })` (Go 1.25) when the work cannot fail; use `errgroup` when it can.
