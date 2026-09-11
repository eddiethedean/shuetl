# Phase 0.2 ownership evidence

| Area | ShuETL | ETLantic / adapter | Host application |
|---|---|---|---|
| Deployment profile | local/test composition only | provider contracts | production deployment profile |
| HTTP routes and schemas | mounts complete router | authoritative owner | chooses host integration |
| Providers and persistence | never constructs or closes | provider protocols | constructs and owns providers |
| Authentication and authorization | preserves dependencies | semantic contracts | supplies principal/context policy |
| Lifespan | tracks mount activity and composes order | no guessed lifecycle | starts and stops providers |
| Execution | no execution code | upstream semantics | external worker or runtime |
| Migrations | none | provider-owned | deployment-owned |

The facade is limited to local/test composition. It makes no production
durability or in-process execution claim.
