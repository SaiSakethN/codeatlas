# Security model

- Imported source is untrusted data, never imported as Python modules or executed. Analysis uses AST parsing and tokenization. Agent tools are schema-validated read-only operations. Prompts instruct the model to treat source as data; prompt-injection resistance is not a formal guarantee.
- Only canonical public HTTPS GitHub URLs are accepted by the API. GitHub metadata is checked before cloning; reported size and catalog count are bounded. Clone timeouts, shallow history, disabled LFS smudging, and disabled hooks reduce import risk. GitHub-reported size is an admission check, not a hard disk quota.
- Public source access is restricted to discovered `.py` files inside the selected catalog repository. Symlinks and traversal paths are rejected. `.env` and arbitrary local paths are not public endpoints.
- One indexing worker and a shared expensive-operation lock bound concurrency. Source, file, chunk, request-body, history, question, tool-output, and agent-step limits bound work. Use one backend process; controls are not distributed.
- Production backend startup requires a token of at least 32 characters. The server-side frontend proxy keeps it out of the browser bundle. Owner access uses a password and signed HTTP-only cookies, same-origin mutation checks, and a local failed-login throttle.
- Frontend login limits are per instance; shared public deployment should add an edge-level throttle. Backend rate limiting is a global process-local budget. This supports a small owner-operated demo, not a high-volume multi-tenant service.
- `.env` is ignored. Example environment files contain empty credentials. Provider/Git errors returned by the API are sanitized. Never log tokens, commit credentials, or put secrets in `NEXT_PUBLIC_` variables.
- Rotation of the previously exposed provider key cannot be established from source inspection. Clean examples do not prove rotation occurred.
- Removal clears the active embedding collection and catalog entry, retaining cloned public source as a cache. Other provider/model collections can remain on disk. This is not secure erasure.
