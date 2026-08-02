# Evidence records

This directory preserves inert evidence and decision history. Every record has `authority: none`; nothing here establishes canon, story lifecycle, naming reservations, publication eligibility, or reader-site inclusion.

`MANIFEST.json` v3 contains:

- local records with repository path, controlled version label, verification status, and verification time;
- external records with a controlled locator, declared version when known, access date, access requirements, and verification status.

A `verified` record may support a reproducible decision when its declared version can be retrieved from its controlled path or locator. A `descriptive-only` record is provenance or a request for missing input and cannot support a factual claim. Locators are not runtime dependencies or grants of authority.

If a referenced input cannot be verified at the declared location and version, treat claims drawn from it as unsupported. Preserve the uncertainty instead of promoting it into universe notes.
