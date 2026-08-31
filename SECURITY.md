# Security Policy

## Reporting a Vulnerability

Please do not open a public GitHub issue for a security report.

Use GitHub's private advisory form:

https://github.com/jwilson411/pcos-litwatch/security/advisories/new

Include the version or commit, steps to reproduce, and what an attacker gains.

## Scope

pcos-litwatch is a local stdlib collector. Live runs open HTTPS to PubMed E-utilities (`eutils.ncbi.nlm.nih.gov`), ClinicalTrials.gov v2, and arXiv export. They do not download PDFs or model weights. CI uses fixtures and does not hit the network.

The optional Postgres sink reads `HERMES_DATABASE_URL` or `DATABASE_URL` from the environment. This repository does not store secrets. The collector is not medical advice and does not diagnose, treat, or claim a cure.

An attacker who already controls the process, the DSN, or the destination database is out of scope.

## Supported versions

Only the latest release receives security fixes.
