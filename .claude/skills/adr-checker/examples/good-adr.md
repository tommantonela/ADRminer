# Use Redis for Session Caching

Date: 2024-03-10

## Status

Accepted

## Context

Our web application currently stores user sessions in the primary PostgreSQL database.
As traffic has grown, session lookups are adding measurable latency to every request
(average 45ms per query). The database is also handling session expiry cleanup, which
competes with business-critical queries for connection pool resources.

We need a dedicated session store that can handle high read/write throughput with
sub-millisecond latency, while surviving application restarts (unlike in-memory stores).

## Decision Drivers

- **Low latency**: Session lookups must complete in under 5ms at the 99th percentile.
- **High availability**: The session store must survive application restarts and ideally support failover.
- **Operational simplicity**: The team is small and cannot manage complex infrastructure.
- **Automatic expiry**: TTL-based key expiration is required to avoid manual cleanup.
- **Cost**: We prefer open-source, self-hostable solutions.

## Considered Options

### Option 1: Redis

**Pros:**

- Sub-millisecond read/write latency for in-memory key-value operations.
- Built-in key expiration (TTL) ideal for session management.
- Supports persistence (RDB snapshots and AOF) so sessions survive restarts.
- Supports replication and sentinel-based failover.
- Extremely mature ecosystem with client libraries for every language.

**Cons:**

- Adds a new infrastructure component to monitor and maintain.
- Data is primarily in-memory, so memory cost is higher per session than disk-based storage.
- Requires careful configuration of eviction policies under memory pressure.

### Option 2: Memcached

**Pros:**

- Very fast, simple in-memory key-value store.
- Well understood, minimal operational overhead.
- Distributed by nature (client-side consistent hashing).

**Cons:**

- No persistence — all sessions lost on restart.
- No built-in replication or high-availability mechanism.
- No rich data types (only raw strings).

### Option 3: JWT (stateless sessions)

**Pros:**

- No server-side session store needed at all.
- Scales trivially with no shared state.

**Cons:**

- Cannot revoke sessions before token expiry without a server-side blocklist.
- Token size grows with claims, increasing per-request overhead.
- Security concerns around token theft and replay.

## Decision

We will use **Redis** as our dedicated session store.

Redis provides the best combination of low latency, persistence, automatic key expiry, and
operational maturity. The built-in TTL feature directly solves our session cleanup problem,
and sentinel-based replication gives us the high availability we need. The team's prior
exposure to Redis in other projects reduces the learning curve.

## Consequences

**Positive:**

- Session lookup latency drops from ~45ms to under 2ms (99th percentile).
- Database connection pool is freed for business-critical queries.
- Automatic key expiration eliminates the need for cron-based cleanup jobs.

**Negative:**

- We introduce a new point of failure — if Redis goes down, users lose sessions.
- Requires monitoring and alerting for Redis health (memory usage, replication lag).
- Team must learn Redis cluster management for production-grade deployment.

**Neutral:**

- We will run Redis in a replicated setup with at least one replica per region.