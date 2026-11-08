# OAN seed data

Demo data for the OAN Frappe services, curated from the shared development sites.
The seed images copy one service's directory and load it after `bench migrate`, on every
deployment. Loading only creates records that are missing.

| Directory | Service | Holds |
|---|---|---|
| [`a2c/`](a2c) | OAN A2C | Banks, loan products, status stages, terms, users and their bank permissions |
| [`grievance/`](grievance) | OAN Grievance Service | Administrative areas, departments, categories, types, routing, SLAs, providers, users |

Each directory has a `manifest.json` (load order and Single DocTypes), `data/<DocType>.json`
with one record per line, and, where a service has attachments, `files/{public,private}`.

Not included, on purpose: passwords, API keys and environment hostnames. The loader sets the
password of the users it creates from a Kubernetes Secret. Fill these in per environment:
`OAN IAM Service`, `A2C OpenG2P Settings` and the connection on the `A2C Banks` source.
