# ADR-0002: Initial Compatibility Policy

- Status: Accepted
- Date: 2026-09-11

## Context

ETLantic 0.x packages evolve as a lockstep train. The published 0.51.0 train is
available and its adapter declares Python, FastAPI, and Pydantic ranges.

## Decision

ShuETL 0.1 declares Python `>=3.11,<3.14` and proves exactly
`etlantic==0.51.0` plus `etlantic-fastapi==0.51.0`. FastAPI and Pydantic must
satisfy the adapter's declared ranges and their resolved versions are recorded
in the lock file/evidence; 0.1 does not claim support across their full ranges.

## Consequences

The 0.1 evidence is reproducible and conservative. A second ETLantic minor
train requires a new compatibility decision and contract evidence.

## Validation

The test extra, lock file, import-origin checks, and Python matrix prove this
decision. See AC-004, AC-005, and AC-019.

## Revisit trigger

Revisit before adding a second ETLantic minor train or changing the supported
Python classifier range.
