# ShuETL Vision

## Purpose

ShuETL gives FastAPI developers a supported, opinionated way to expose and
operate ETLantic without assembling every ETLantic control-plane provider and
deployment role themselves.

A developer should be able to provide ETLantic definitions and explicit runtime
providers, mount ShuETL into a FastAPI application, and receive a coherent HTTP
surface for validation, planning, durable submission, schedules, status,
events, reports, and artifacts to the extent those capabilities are supplied by
the selected ETLantic packages.

## Product boundary

ETLantic owns the canonical meaning and behavior of pipeline definitions,
plans, execution, scheduling, durable work, retries, cancellation, reports,
events, artifacts, secrets, and provider protocols.

`etlantic-fastapi` owns the low-level ETLantic HTTP schemas, routes, errors, and
streaming semantics.

ShuETL owns:

- an ergonomic FastAPI composition facade;
- selection and configuration of ETLantic providers;
- application lifecycle and deployment-role integration;
- safe local defaults and explicit production profiles;
- compatibility validation across the selected package set;
- optional adapters to host identity and presentation systems;
- operator-oriented documentation and integration tests.

ShuETL does not define a second pipeline representation, run state machine,
scheduler, executor protocol, artifact model, retry engine, secret resolver, or
migration system.

## Product principles

### Integration over reimplementation

Every exposed ETLantic capability retains its upstream model, identity,
versioning, validation, and failure semantics.

### One contract at every boundary

Python, HTTP, persistence, events, and tests should refer to the same ETLantic
records. ShuETL-specific models are limited to ShuETL configuration and
composition diagnostics.

### Explicit capability discovery

ShuETL reports which features are available from the configured providers. A
missing provider produces a clear unavailable/readiness result rather than a
partial ShuETL reimplementation.

### Safe deployment profiles

One-process execution is a local-development convenience. Production separates
the FastAPI gateway from scheduler/worker execution while allowing the roles to
share one installation, image, and SQL database.

### Upstream-first gaps

When ETLantic lacks a canonical semantic capability, ShuETL should contribute
the capability upstream or wait for an upstream contract. Temporary adapters
must be narrow, versioned, and explicitly non-authoritative.

### Stable host experience

ShuETL absorbs ordinary provider wiring and compatibility checks so host
applications do not need to understand every ETLantic implementation package.

## Primary users

- FastAPI developers who want to add ETLantic operations to an application;
- operators who want a documented, supported deployment topology;
- ecosystem integrators connecting identity, UI, and observability systems to
  ETLantic through FastAPI.

## Success criteria

ShuETL succeeds when it materially reduces the integration and operational work
required to deploy ETLantic while preserving exact ETLantic behavior.

Success is not measured by the number of domain abstractions implemented by
ShuETL. Prefer fewer ShuETL abstractions, smaller adapters, and more upstream
contract reuse.

## Non-goals

- implementing a general-purpose workflow orchestrator;
- redefining ETLantic pipeline, execution, scheduling, or result semantics;
- maintaining copies of ETLantic Pydantic or persistence models;
- arbitrary user-code upload or package installation through the API;
- running mutually untrusted code in the FastAPI process;
- hiding production topology or security requirements behind a development
  convenience factory;
- promising that every ETLantic feature is available when its provider has not
  been configured.
