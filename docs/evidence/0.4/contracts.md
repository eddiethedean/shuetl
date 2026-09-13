# Phase 0.4 contracts

The PostgreSQL pilot requires the `postgresql-pilot` profile, the PostgreSQL
provider, a `postgresql+psycopg` URL, ETLantic SQLModel migration head
`005_cp1_reference`, and PostgreSQL server 18.6. Readiness inspection is
read-only and migration is explicit through `shuetl database upgrade`.
