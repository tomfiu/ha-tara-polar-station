# Contributing

## Local development

1. Clone this repository.
2. Install test dependencies.
3. Run `pytest`.
4. Validate integration inside a Home Assistant dev environment.

## Guidelines

- Keep changes aligned with Home Assistant architecture patterns.
- Use `DataUpdateCoordinator` for polling and shared API state.
- Add or update tests for all behavior changes.
- Document new entities, options, and events in `README.md`.

## Pull Requests

- Use clear titles and focused commits.
- Include a short testing summary in the PR description.
- Update `CHANGELOG.md` for user-facing changes.
