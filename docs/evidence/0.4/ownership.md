# Phase 0.4 ownership

ShuETL owns settings validation, provider composition, diagnostics, and the
explicit migration command. ETLantic SQLModel owns schema migrations and
durable store semantics. PostgreSQL owns transaction and persistence behavior.
