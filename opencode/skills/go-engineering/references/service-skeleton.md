# Production HTTP service skeleton (Go 1.26+, verified with go1.27.3)

Tested on 2026-10-29 with go1.27.3: `go vet` clean, `golangci-lint run` with the vetted config printed
`0 issues.`, `staticcheck` silent, `go fix -diff` empty, `go test -race -count=1` ok five runs in a
row, and `cmd/api` statement coverage 87.3% (`run` 88.9%, `serve` 89.5%; only `main` itself is
untested). The shutdown test fails against the previous version of this file, whose `BaseContext`
returned the signal context: the in-flight request got `503 request ctx canceled` instead of
`completed`. It needs Go 1.26+ because it uses `errors.AsType`; replace that with `errors.As` for a
Go 1.25 module.

What it demonstrates, with the rule it implements:

- `main` only maps `run`'s error to an exit code; `run(ctx, getenv, stdout io.Writer)` takes its
  dependencies as parameters, so the test drives the real `run` on port 0 (GO-ERR-8).
- `signal.NotifyContext` turns SIGINT/SIGTERM into cancellation of `ctx`, which only starts the
  shutdown. Request contexts come from a separate `ongoingCtx` (`BaseContext`), canceled only after
  `Shutdown` has drained or timed out, so a SIGTERM does not abort requests already running
  (GO-CTX-1, GO-CTX-3).
- Method-and-path `ServeMux` patterns (`"POST /v1/items"`), no router dependency.
- All four server timeouts (GO-SEC-1), `http.MaxBytesReader` with a typed check for the limit error
  (GO-SEC-2), `DisallowUnknownFields`, and `CrossOriginProtection` (GO-SEC-3).
- A bounded drain (`context.WithTimeout` over `context.WithoutCancel`); after it expires the
  remaining requests are canceled and the server is closed, and `serve` reports
  `context.DeadlineExceeded`. The `Serve` goroutine's error is always collected (GO-CONC-1).
- A `version` variable stamped by the release build (GO-MOD-5) and logged at startup.
- `slog` JSON logging with the server's own `ErrorLog` routed through slog.

## cmd/api/main.go

```go
// Command api is a minimal production-shaped HTTP service.
package main

import (
	"cmp"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

// version is stamped at release time with -ldflags="-X main.version=...".
var version = "dev"

func main() {
	if err := run(context.Background(), os.Getenv, os.Stdout); err != nil {
		fmt.Fprintln(os.Stderr, "api:", err)
		os.Exit(1)
	}
}

// run owns the whole lifecycle so tests can call it; main only maps the error to an exit code.
func run(ctx context.Context, getenv func(string) string, stdout io.Writer) error {
	ctx, stop := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)
	defer stop()

	log := slog.New(slog.NewJSONHandler(stdout, nil))
	addr := cmp.Or(getenv("ADDR"), ":8080")

	ln, err := new(net.ListenConfig).Listen(ctx, "tcp", addr)
	if err != nil {
		return fmt.Errorf("listen: %w", err)
	}
	log.Info("listening", "addr", ln.Addr().String(), "version", version)
	return serve(ctx, ln, newHandler(log), log, 10*time.Second)
}

func newHandler(log *slog.Logger) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusNoContent)
	})
	mux.HandleFunc("POST /v1/items", createItem(log))
	return http.NewCrossOriginProtection().Handler(mux)
}

// serve runs h on ln until ctx is done. It then stops accepting connections and gives in-flight
// requests up to drain to finish; only after that are their contexts canceled.
func serve(ctx context.Context, ln net.Listener, h http.Handler, log *slog.Logger, drain time.Duration) error {
	// Request contexts derive from ongoingCtx, not ctx. If they derived from ctx, SIGTERM would
	// cancel every in-flight request at once and the Shutdown drain below would protect nothing.
	ongoingCtx, cancelOngoing := context.WithCancel(context.WithoutCancel(ctx))
	defer cancelOngoing()

	srv := &http.Server{
		Handler:           h,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       15 * time.Second,
		WriteTimeout:      15 * time.Second,
		IdleTimeout:       60 * time.Second,
		BaseContext:       func(net.Listener) context.Context { return ongoingCtx },
		ErrorLog:          slog.NewLogLogger(log.Handler(), slog.LevelWarn),
	}

	errCh := make(chan error, 1)
	go func() { errCh <- srv.Serve(ln) }() // Serve always returns a non-nil error

	select {
	case err := <-errCh:
		return fmt.Errorf("serve: %w", err)
	case <-ctx.Done():
	}

	log.Info("shutting down", "drain", drain.String())
	shutdownCtx, cancel := context.WithTimeout(context.WithoutCancel(ctx), drain)
	defer cancel()
	err := srv.Shutdown(shutdownCtx) // stops accepting, waits for in-flight requests
	cancelOngoing()                  // drain finished or timed out: cancel whatever is still running
	if err != nil {
		err = errors.Join(fmt.Errorf("shutdown: %w", err), srv.Close())
	}
	if serveErr := <-errCh; !errors.Is(serveErr, http.ErrServerClosed) {
		err = errors.Join(err, fmt.Errorf("serve: %w", serveErr))
	}
	return err
}

type item struct {
	Name string `json:"name"`
}

func createItem(log *slog.Logger) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
		dec := json.NewDecoder(r.Body)
		dec.DisallowUnknownFields()
		var in item
		if err := dec.Decode(&in); err != nil {
			if maxErr, ok := errors.AsType[*http.MaxBytesError](err); ok {
				http.Error(w, fmt.Sprintf("body exceeds %d bytes", maxErr.Limit), http.StatusRequestEntityTooLarge)
				return
			}
			http.Error(w, "invalid JSON body", http.StatusBadRequest)
			return
		}
		if in.Name == "" {
			http.Error(w, "name is required", http.StatusUnprocessableEntity)
			return
		}
		log.InfoContext(r.Context(), "item created", "name", in.Name)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		if err := json.NewEncoder(w).Encode(in); err != nil {
			log.WarnContext(r.Context(), "encode response", "err", err)
		}
	}
}
```

## cmd/api/main_test.go

```go
package main

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"log/slog"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestCreateItem(t *testing.T) {
	t.Parallel()
	log := slog.New(slog.DiscardHandler)
	h := createItem(log)

	tests := []struct {
		name, body string
		want       int
	}{
		{name: "ok", body: `{"name":"a"}`, want: http.StatusCreated},
		{name: "unknown field", body: `{"name":"a","x":1}`, want: http.StatusBadRequest},
		{name: "missing name", body: `{}`, want: http.StatusUnprocessableEntity},
		{name: "too large", body: `{"name":"` + strings.Repeat("a", 2<<20) + `"}`, want: http.StatusRequestEntityTooLarge},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			req := httptest.NewRequestWithContext(t.Context(), http.MethodPost, "/v1/items", strings.NewReader(tt.body))
			rec := httptest.NewRecorder()
			h(rec, req)
			if rec.Code != tt.want {
				t.Fatalf("status = %d, want %d (body %q)", rec.Code, tt.want, rec.Body.String())
			}
		})
	}
}

// lineSink hands each slog record (one Write per record) to the test without blocking run.
type lineSink chan string

func (s lineSink) Write(p []byte) (int, error) {
	select {
	case s <- string(p):
	default:
	}
	return len(p), nil
}

var client = &http.Client{Timeout: 5 * time.Second}

func TestRunServesHealthzAndStopsOnCancel(t *testing.T) {
	t.Parallel()
	ctx, cancel := context.WithCancel(t.Context())
	defer cancel()
	logs := make(lineSink, 16)
	getenv := func(k string) string {
		if k == "ADDR" {
			return "127.0.0.1:0" // port 0: the kernel picks a free port, read back from the log
		}
		return ""
	}
	done := make(chan error, 1)
	go func() { done <- run(ctx, getenv, logs) }()

	var rec struct{ Msg, Addr, Version string }
	select {
	case line := <-logs:
		if err := json.Unmarshal([]byte(line), &rec); err != nil || rec.Msg != "listening" {
			t.Fatalf("first log line = %q (err %v), want a listening record", line, err)
		}
	case err := <-done:
		t.Fatalf("run returned before listening: %v", err)
	case <-time.After(5 * time.Second):
		t.Fatal("no listening log within 5s")
	}
	if rec.Version != "dev" {
		t.Errorf("version = %q, want dev", rec.Version)
	}

	req, err := http.NewRequestWithContext(t.Context(), http.MethodGet, "http://"+rec.Addr+"/healthz", nil)
	if err != nil {
		t.Fatal(err)
	}
	resp, err := client.Do(req)
	if err != nil {
		t.Fatalf("GET /healthz: %v", err)
	}
	_ = resp.Body.Close()
	if resp.StatusCode != http.StatusNoContent {
		t.Fatalf("GET /healthz = %d, want 204", resp.StatusCode)
	}

	cancel() // what SIGTERM does via signal.NotifyContext
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("run() = %v, want nil after cancel", err)
		}
	case <-time.After(5 * time.Second):
		t.Fatal("run did not return within 5s of cancel")
	}
}

type result struct {
	code int
	body string
	err  error
}

func get(ctx context.Context, url string) result {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return result{err: err}
	}
	resp, err := client.Do(req)
	if err != nil {
		return result{err: err}
	}
	defer resp.Body.Close()
	b, err := io.ReadAll(resp.Body)
	return result{code: resp.StatusCode, body: string(b), err: err}
}

func listen(t *testing.T) net.Listener {
	t.Helper()
	ln, err := new(net.ListenConfig).Listen(t.Context(), "tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	return ln
}

// slowHandler takes work to finish unless its request context is canceled first.
func slowHandler(started chan<- struct{}, work time.Duration, sawCancel chan<- struct{}) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		close(started)
		select {
		case <-time.After(work):
			_, _ = io.WriteString(w, "completed")
		case <-r.Context().Done():
			close(sawCancel)
			http.Error(w, "request ctx canceled", http.StatusServiceUnavailable)
		}
	})
}

func TestServeDrainsInFlightRequestOnShutdown(t *testing.T) {
	t.Parallel()
	started, sawCancel := make(chan struct{}), make(chan struct{})
	ln := listen(t)
	ctx, cancel := context.WithCancel(t.Context())
	defer cancel()
	done := make(chan error, 1)
	go func() {
		done <- serve(ctx, ln, slowHandler(started, 200*time.Millisecond, sawCancel), slog.New(slog.DiscardHandler), 5*time.Second)
	}()
	res := make(chan result, 1)
	go func() { res <- get(t.Context(), "http://"+ln.Addr().String()+"/") }()

	<-started
	cancel() // shutdown begins while the request is in flight

	r := <-res
	if r.err != nil || r.code != http.StatusOK || r.body != "completed" {
		t.Fatalf("in-flight request = (%d, %q, %v), want (200, \"completed\", nil)", r.code, r.body, r.err)
	}
	if err := <-done; err != nil {
		t.Fatalf("serve() = %v, want nil", err)
	}
}

func TestServeCancelsRequestsAfterDrainTimeout(t *testing.T) {
	t.Parallel()
	started, sawCancel := make(chan struct{}), make(chan struct{})
	ln := listen(t)
	ctx, cancel := context.WithCancel(t.Context())
	defer cancel()
	done := make(chan error, 1)
	go func() {
		done <- serve(ctx, ln, slowHandler(started, time.Minute, sawCancel), slog.New(slog.DiscardHandler), 50*time.Millisecond)
	}()
	go func() { _ = get(t.Context(), "http://"+ln.Addr().String()+"/") }()

	<-started
	cancel()
	select {
	case <-sawCancel:
	case <-time.After(5 * time.Second):
		t.Fatal("request context not canceled after the drain deadline")
	}
	if err := <-done; !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("serve() = %v, want context.DeadlineExceeded", err)
	}
}
```

## Dockerfile (GO-MOD-7)

```dockerfile
# syntax=docker/dockerfile:1
# Pin both base images by digest in real repos and let Renovate/Dependabot move them.
FROM golang:1.27.3-trixie AS build
WORKDIR /src
# local: use the image's Go and fail on a newer go.mod requirement instead of downloading one.
ENV CGO_ENABLED=0 GOTOOLCHAIN=local GOFLAGS=-mod=readonly
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download && go mod verify
COPY . .
ARG VERSION=dev
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go build -trimpath -ldflags="-s -w -X main.version=${VERSION}" -o /out/api ./cmd/api

# static:nonroot holds CA certs, tzdata and /tmp; no shell or package manager; runs as UID 65532.
FROM gcr.io/distroless/static-debian13:nonroot
COPY --from=build /out/api /api
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/api"]
```

Build with `docker build --build-arg VERSION=$(git describe --tags --always) -t api .`. Verified on
2026-10-29: `hadolint` v2.15.1 reports nothing; both base tags exist (Docker Hub
`golang:1.27.3-trixie`, and `gcr.io/distroless/static-debian13:nonroot`, whose image config sets
`User: 65532`); the build stage's commands (`go mod download && go mod verify`, then the `go build`
line with the same environment) succeed outside Docker and produce a statically linked binary.
The image build itself was not run (no Docker daemon access on the verification box): `[UNVERIFIED]`.
Add a `.dockerignore` that excludes `.git`, `bin/` and local env files.

Extending it:

- Add dependencies (DB pool, clients) inside `run`, close them with `defer`, and pass them to handler
  constructors (`createItem(log, store)`), never via globals.
- For a readiness probe that checks the database, use a separate `GET /readyz` with a short
  `context.WithTimeout`. Behind a load balancer, fail `/readyz` once shutdown starts and keep serving
  for a few seconds before calling `Shutdown`, so no new traffic is routed to a stopping pod.
- Add OpenTelemetry (`go.opentelemetry.io/otel` v1.47.0) by wrapping the handler with the otelhttp
  handler from opentelemetry-go-contrib; check the current API through Context7 first.
- Expose pprof on a separate, non-public listener (`net/http/pprof` registered on its own mux bound to
  localhost), never on the public mux.
