# Contributing to CodeAtlas

## Branching Strategy

- `main`: Stable and verified releases.
- `develop`: Integration branch for ongoing development.
- `feature/*`: New functionality.
- `fix/*`: Bug fixes.
- `hotfix/*`: Urgent production fixes.
- `release/*`: Release preparation.
- `docs/*`: Documentation improvements.

## Development Workflow

1. Create or select a GitHub issue.
2. Synchronize the develop branch.
3. Create a dedicated feature branch.
4. Implement changes incrementally.
5. Add or update automated tests.
6. Run local quality checks.
7. Create meaningful commits.
8. Push the branch to GitHub.
9. Open a pull request targeting develop.
10. Review changes and CI results.
11. Merge after successful verification.

## Commit Conventions

- `feat:` New functionality
- `fix:` Bug fixes
- `docs:` Documentation
- `test:` Automated tests
- `refactor:` Code restructuring
- `chore:` Maintenance
- `ci:` Continuous integration
- `build:` Build and packaging changes
- `perf:` Performance improvements

## Local Quality Checks

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest -v
```

## Security Guidelines

Never commit API keys, credentials, local environment files, cloned repositories, vector indexes, or sensitive runtime data.

Repository analysis must remain read-only. Untrusted repository code must not be executed.

## Definition of Done

A change is complete when its acceptance criteria are satisfied, relevant tests pass, documentation is updated, and required CI checks succeed.