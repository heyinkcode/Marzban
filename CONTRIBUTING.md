# Contributing to the heyinkcode Marzban fork

This fork is based on [Gozargah/Marzban](https://github.com/Gozargah/Marzban). Preserve upstream attribution and the [license](LICENSE). The [previous contribution guide](https://github.com/heyinkcode/Marzban/blob/23a977829603de3695b468e733499da9c7210e29/CONTRIBUTING.md) is preserved in the repository history as of 2026-11-27.

## Propose a change

1. Fork or clone this repository and create a topic branch from the current `master`.
2. Keep the change focused. Update the relevant [documentation](docs/README.md) and tests. Use the [release workflow](docs/REPOSITORY_UPDATE_FLOW.md) for changes that affect Node, deployment scripts, configuration, APIs, or database migrations.
3. Open a [pull request](https://github.com/heyinkcode/Marzban/pulls) targeting this fork's `master`. In the description, state the expected and actual behavior, how to reproduce the issue, affected versions, and what you tested. Name any checks you skipped and why.

If you include logs or configuration examples, remove passwords, tokens, subscription URLs, private keys, personal data, and production database contents. Use a test account and database for reproduction. For configuration changes, keep [`.env.example`](.env.example) and the [configuration guide](docs/CONFIGURATION.md) in sync; never commit a real `.env`.

## Project layout

| Path | Contains |
| --- | --- |
| `app/` | FastAPI backend, including models, endpoints, jobs, and Alembic migrations |
| `app/dashboard/` | React/TypeScript dashboard using Chakra UI |
| `cli/` | Built-in management CLI. See the [CLI command reference](cli/README.md); deployment and updates use the [separate scripts repository](https://github.com/heyinkcode/Marzban-scripts). |
| `xray_api/` | Internal Xray gRPC client, not the public Marzban HTTP API |
| `tests/` and `docs/` | Regression tests and project documentation |

## Verify before opening a PR

In an isolated Python 3.12 environment, run the backend suite from the repository root:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p 'test_*.py' -v
```

Some Xray integration tests require the pinned test binary. See the [Linux CI workflow](.github/workflows/build.yml) for those commands and the container-based migration check. With Node.js/npm available, run the dashboard checks from the repository root:

```bash
cd app/dashboard
npm ci --ignore-scripts
npm run test:locales
npm exec tsc -- --noEmit
VITE_BASE_API=/api/ npm exec vite -- build --outDir build --assetsDir statics
cp build/index.html build/404.html
```

The dashboard commands above use a POSIX shell, as in CI. For UI changes, keep the existing Chakra components and verify the actual interface. Check [the release checklist](RELEASE_CHECKLIST.md) for changes that affect deployment; testing does not require updating a live server.

