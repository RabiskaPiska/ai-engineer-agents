# Service skeleton: axum 0.8.9 + tokio 1.54.1 (verified 2026-10-29)

A minimal production-shaped HTTP service, split into a domain library (`orders`) and a thin binary
(`api`). It uses the workspace from `project-templates.md`.

**Evidence (Rust 1.99.1, this session):** clippy with `-D warnings` and `clippy::pedantic` clean;
`cargo fmt --check` clean; `cargo nextest run`: 5 passed (3 unit, 2 proptest); live run:
`GET /healthz` -> 204, `POST /orders/ABC-1 {"quantity":3}` -> 201 with JSON body,
`{"quantity":0}` -> 422 `quantity 0 is outside 1..=10000`, SKU `bad` -> 422, 70 KB body -> 413,
SIGINT and SIGTERM -> background job drained, `shutdown complete` logged, exit 0.

What it demonstrates:

- Validated newtypes (`Sku`, `Quantity`) built with `FromStr`/`TryFrom` at the boundary (R-API-1).
- A typed, `#[non_exhaustive]`, `thiserror` domain error that is `Send + Sync` (asserted at compile
  time) and mapped to HTTP only in the binary (R-ERR-1, R-ERR-4).
- Request body limit, request timeout via `TimeoutLayer::with_status_code`, panic isolation via
  `CatchPanicLayer`, request tracing (R-SEC-5, R-ASYNC-7).
- Background work owned by a `TaskTracker`, drained with a deadline on shutdown; SIGINT/SIGTERM
  handling with a `CancellationToken` (R-ASYNC-6, R-ASYNC-12).
- JSON structured logs with `EnvFilter` (R-OBS-2).

Not included (add per project): database pool (`sqlx` 0.9 with `runtime-tokio` and a `tls-rustls*`
feature; `query!` macros need `DATABASE_URL` or `.sqlx` offline data at build time), OpenTelemetry
export, configuration loading, authentication.

## `crates/orders/src/lib.rs`

```rust
//! Order domain types: validated SKUs, quantities, and order lines.

use std::fmt;
use std::str::FromStr;

/// Maximum quantity accepted for one order line; larger orders go through the bulk desk.
pub const MAX_QUANTITY: u32 = 10_000;

/// Errors produced while validating order input.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
#[non_exhaustive]
pub enum OrderError {
    /// The SKU was empty, too long, or contained characters outside `[A-Z0-9-]`.
    #[error("invalid sku {sku:?}: {reason}")]
    InvalidSku {
        /// The rejected input.
        sku: String,
        /// Why it was rejected.
        reason: &'static str,
    },
    /// The quantity was zero or above [`MAX_QUANTITY`].
    #[error("quantity {0} is outside 1..={MAX_QUANTITY}")]
    QuantityOutOfRange(u32),
}

/// A stock-keeping unit: 1 to 32 characters of `A-Z`, `0-9` or `-`.
#[derive(Debug, Clone, PartialEq, Eq, Hash, PartialOrd, Ord, serde::Serialize)]
#[serde(transparent)]
pub struct Sku(String);

impl Sku {
    /// Returns the SKU as a string slice.
    #[must_use]
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl FromStr for Sku {
    type Err = OrderError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let reject = |reason| OrderError::InvalidSku {
            sku: s.to_owned(),
            reason,
        };
        if s.is_empty() || s.len() > 32 {
            return Err(reject("length must be 1..=32"));
        }
        if !s
            .bytes()
            .all(|b| b.is_ascii_uppercase() || b.is_ascii_digit() || b == b'-')
        {
            return Err(reject("allowed characters are A-Z, 0-9 and '-'"));
        }
        Ok(Self(s.to_owned()))
    }
}

impl fmt::Display for Sku {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

/// A validated quantity in `1..=MAX_QUANTITY`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, serde::Serialize)]
#[serde(transparent)]
pub struct Quantity(u32);

impl TryFrom<u32> for Quantity {
    type Error = OrderError;

    fn try_from(n: u32) -> Result<Self, Self::Error> {
        if (1..=MAX_QUANTITY).contains(&n) {
            Ok(Self(n))
        } else {
            Err(OrderError::QuantityOutOfRange(n))
        }
    }
}

impl Quantity {
    /// Returns the raw count.
    #[must_use]
    pub fn get(self) -> u32 {
        self.0
    }
}

/// One validated line of an order.
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize)]
pub struct OrderLine {
    /// What is being ordered.
    pub sku: Sku,
    /// How many units.
    pub quantity: Quantity,
}

impl OrderLine {
    /// Validates raw input into an order line.
    ///
    /// # Errors
    ///
    /// Returns [`OrderError`] when the SKU or quantity is invalid.
    pub fn parse(sku: &str, quantity: u32) -> Result<Self, OrderError> {
        Ok(Self {
            sku: sku.parse()?,
            quantity: Quantity::try_from(quantity)?,
        })
    }
}

const _: () = {
    const fn assert_send_sync<T: Send + Sync>() {}
    assert_send_sync::<OrderLine>();
    assert_send_sync::<OrderError>();
};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_accepts_valid_line() {
        let line = OrderLine::parse("ABC-123", 3).unwrap();
        assert_eq!(line.sku.as_str(), "ABC-123");
        assert_eq!(line.quantity.get(), 3);
    }

    #[test]
    fn parse_rejects_lowercase_sku() {
        let err = OrderLine::parse("abc", 1).unwrap_err();
        assert!(matches!(err, OrderError::InvalidSku { .. }), "got {err:?}");
    }

    #[test]
    fn parse_rejects_zero_quantity() {
        assert_eq!(
            OrderLine::parse("A", 0),
            Err(OrderError::QuantityOutOfRange(0))
        );
    }
}
```

## `crates/orders/tests/properties.rs`

```rust
//! Property tests for the public order API.

use orders::{MAX_QUANTITY, OrderLine};
use proptest::prelude::*;

proptest! {
    #[test]
    fn valid_quantities_round_trip(q in 1..=MAX_QUANTITY) {
        let line = OrderLine::parse("SKU-1", q).unwrap();
        prop_assert_eq!(line.quantity.get(), q);
    }

    #[test]
    fn parse_never_panics(sku in ".{0,64}", q in any::<u32>()) {
        let _ = OrderLine::parse(&sku, q);
    }
}
```

## `crates/api/Cargo.toml`

```toml
[package]
name = "api"
version = "0.1.0"
edition.workspace = true
rust-version.workspace = true
license.workspace = true
publish.workspace = true

[dependencies]
anyhow.workspace = true
axum.workspace = true
orders.workspace = true
serde.workspace = true
serde_json.workspace = true
tokio.workspace = true
tokio-util.workspace = true
tower-http.workspace = true
tracing.workspace = true
tracing-subscriber.workspace = true

[lints]
workspace = true
```

## `crates/api/src/main.rs`

```rust
//! HTTP API for orders: thin binary that wires config, telemetry and the router.

use std::net::SocketAddr;
use std::time::Duration;

use anyhow::Context as _;
use axum::extract::{DefaultBodyLimit, Path, State};
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use orders::{OrderError, OrderLine};
use tokio_util::sync::CancellationToken;
use tokio_util::task::TaskTracker;
use tower_http::catch_panic::CatchPanicLayer;
use tower_http::timeout::TimeoutLayer;
use tower_http::trace::TraceLayer;
use tracing_subscriber::EnvFilter;

/// Largest accepted request body; order payloads are tiny.
const BODY_LIMIT_BYTES: usize = 64 * 1024;
/// Per-request deadline, including handler time.
const REQUEST_TIMEOUT: Duration = Duration::from_secs(10);
/// How long shutdown waits for background jobs before exiting anyway.
const DRAIN_DEADLINE: Duration = Duration::from_secs(20);

#[derive(Debug, Clone)]
struct AppState {
    jobs: TaskTracker,
}

#[derive(Debug, serde::Deserialize)]
struct NewOrder {
    quantity: u32,
}

/// Maps domain errors to HTTP responses at the edge, so the domain crate stays HTTP-free.
struct ApiError(OrderError);

impl From<OrderError> for ApiError {
    fn from(e: OrderError) -> Self {
        Self(e)
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let body = Json(serde_json::json!({ "error": self.0.to_string() }));
        (StatusCode::UNPROCESSABLE_ENTITY, body).into_response()
    }
}

async fn create_order(
    State(state): State<AppState>,
    Path(sku): Path<String>,
    Json(req): Json<NewOrder>,
) -> Result<(StatusCode, Json<OrderLine>), ApiError> {
    let line = OrderLine::parse(&sku, req.quantity)?;
    let audit = line.clone();
    state.jobs.spawn(async move {
        tracing::info!(sku = %audit.sku, quantity = audit.quantity.get(), "order accepted");
    });
    Ok((StatusCode::CREATED, Json(line)))
}

fn router(state: AppState) -> Router {
    Router::new()
        .route("/healthz", get(|| async { StatusCode::NO_CONTENT }))
        .route("/orders/{sku}", post(create_order))
        .layer(DefaultBodyLimit::max(BODY_LIMIT_BYTES))
        .layer(TimeoutLayer::with_status_code(
            StatusCode::REQUEST_TIMEOUT,
            REQUEST_TIMEOUT,
        ))
        .layer(TraceLayer::new_for_http())
        .layer(CatchPanicLayer::new())
        .with_state(state)
}

/// Resolves on SIGINT, SIGTERM (Unix) or an internal cancel, then cancels `token`.
async fn shutdown_signal(token: CancellationToken) {
    let ctrl_c = async {
        if let Err(e) = tokio::signal::ctrl_c().await {
            tracing::error!(error = %e, "failed to listen for ctrl-c");
        }
    };
    #[cfg(unix)]
    let terminate = async {
        match tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate()) {
            Ok(mut sig) => {
                sig.recv().await;
            }
            Err(e) => tracing::error!(error = %e, "failed to listen for SIGTERM"),
        }
    };
    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        () = ctrl_c => {},
        () = terminate => {},
        () = token.cancelled() => {},
    }
    token.cancel();
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .json()
        .init();

    let addr: SocketAddr = std::env::var("BIND_ADDR")
        .unwrap_or_else(|_| "127.0.0.1:8080".to_owned())
        .parse()
        .context("BIND_ADDR must be host:port")?;

    let token = CancellationToken::new();
    let jobs = TaskTracker::new();
    let app = router(AppState { jobs: jobs.clone() });

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .with_context(|| format!("binding {addr}"))?;
    tracing::info!(%addr, "listening");

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal(token.clone()))
        .await
        .context("server error")?;

    jobs.close();
    if tokio::time::timeout(DRAIN_DEADLINE, jobs.wait())
        .await
        .is_err()
    {
        tracing::warn!(
            pending = jobs.len(),
            "background jobs did not drain in time"
        );
    }
    tracing::info!("shutdown complete");
    Ok(())
}
```
