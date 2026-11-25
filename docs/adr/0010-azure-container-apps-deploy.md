# ADR-0010: API on Azure Container Apps, UI on Vercel; deploys only via GitHub Actions

- Status: accepted
- Date: 2026-11-25
- Details: docs/ARCHITECTURE.md

## Context

The project targets Azure. The Students subscription's policy only allows `uaenorth`, `polandcentral`, `spaincentral`, `germanywestcentral` and `austriaeast`, and Postgres Flexible Server additionally refuses Germany West Central at create time (dry-run validation passes, so only a real create reveals it).

## Decision

Container Apps (consumption, min 0, max 2 replicas) in Spain Central (verified by creating the `cae-docqa` environment on 2026-11-25), with the image on GHCR, deployed by GitHub Actions on merge to `main`. Deploy identity, in order: an OIDC federated credential on the Students subscription (app registrations are allowed in the tenant, checked 2026-11-25); else the paid subscription only if it costs about nothing; else a service principal with a 90-day secret in GitHub secrets.

## Consequences

Cold starts after idle; the UI shows a wake-up message. The API runs in Spain while the model APIs are in the US, so evals measure the latency. Rollback is one `az containerapp update` to the previous SHA tag.
