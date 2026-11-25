# Deployment

No deployed full-stack URL has been verified. The application works locally; external hosting and secrets must be configured before publishing an operational workspace.

## Backend: Render free demo

Connect Render to this GitHub repository and use the included `render.yaml` blueprint, targeting `develop`. It explicitly selects `plan: free`. Do not upgrade or attach a paid disk without approval.

Required environment:

- `ENVIRONMENT=production` (set by Docker).
- `LLM_PROVIDER=fastembed`, `CHAT_PROVIDER=groq` (set by Docker).
- `GROQ_API_KEY`: your existing inference credential. Never put it in Git.
- `API_TOKEN`: a private random token of at least 32 characters; missing/short tokens prevent production startup.
- `FRONTEND_URL`: exact frontend origin.

The container installs the optional `cloud` dependencies and runs as an unprivileged user. FastEmbed lazily downloads `sentence-transformers/all-MiniLM-L6-v2` ONNX weights, using two inference threads. Its model card uses Apache 2.0. Chroma collections include provider and embedding model in their identity; reimport repositories after switching models.

Keep one Uvicorn worker. Repository import is serialized with inference. Defaults cap discovered Python files at 2,000, individual source size at 500 KB, aggregate source at 10 MB, and chunks at 5,000. The free blueprint further limits catalog size and GitHub-reported repository size. Reduce these limits if the host's memory requires it.

Free-service constraints: [Render free services](https://render.com/docs/free) and [Render FAQ](https://render.com/docs/faq). Files are ephemeral, idle services spin down, and the initial embedding-model download adds startup time. Memory fit requires testing on the actual host.

## Frontend: Vercel

Import `SaiSakethN/codeatlas`, set root directory `frontend`, use Node 24 and Next.js, and deploy `develop` as a preview first. Do not merge into `main` automatically.

Set server-only environment variables:

- `CODEATLAS_API_URL=https://<backend-host>`
- `CODEATLAS_API_TOKEN=<same private backend API_TOKEN>`
- `FRONTEND_PASSWORD=<private password, at least 16 characters>`

Redeploy after changing environment values. The password creates an eight-hour signed HTTP-only, secure, SameSite-strict cookie. Production workspace access fails closed if the password is missing. The public landing page remains accessible. This is owner/demo access, not per-user accounts.

Confirm that the selected Vercel account has an appropriate free plan and no usage charges before deploying; no paid features are required by this repository.

## Deployment smoke checklist

1. `/health` returns 200; unauthenticated backend API requests return 401.
2. The frontend opens over HTTPS; unauthenticated workspace API requests fail.
3. Sign in, import a small public Python repository, and observe indexing completion.
4. Inspect a file, open architecture, and run one RAG and one agent question.
5. Open a citation and verify its file/line range; inspect the completed tool trace.
6. Check failure handling and repository removal.
7. Document cold starts and restart/reindex behavior, then add the verified URL to README.

If the backend exceeds the free host's memory, keep the working local deployment until an approved alternative is available. Do not silently enable paid resources.
