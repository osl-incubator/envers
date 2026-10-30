# Development guide

## Purpose

Envers manages environment configuration by release and deployment profile. Its
useful direction is checking configuration contracts and supplying them to
Containers Sugar. Sugar owns container orchestration; Envers owns configuration.
See `docs/roadmap.md` for priorities and `docs/project-assessment.md` for
context.

## Working principles

- Group related tasks into one focused PR that completes a useful workflow;
  avoid a separate PR for each small internal step.
- Prefer direct code over new frameworks, provider abstractions or speculative
  extension points. Refactor only where it helps the current change.
- Envers is pre-stable and not production-ready. Breaking changes are
  acceptable; do not add compatibility aliases, migrations or deprecated paths
  unless asked or needed by an explicitly supported workflow. Describe changed
  behavior in the PR.
- Add tests for meaningful behavior changes and regressions. Do not test every
  permutation, mirror implementation details or add tests for documentation
  edits.
- Documentation changes are not required for every code change. Leave guides
  alone for routine fixes and internal changes; use CLI help and the PR
  description. Change documentation only when users need new instructions or
  existing instructions become materially wrong. Keep one concise explanation,
  and remove redundant documentation instead of repeatedly maintaining copies.
- Treat the roadmap as a bounded plan. Do not add follow-up tasks, split items
  or expand scope after each change. Do not edit it routinely in every PR;
  revise it only for an agreed milestone review or explicit user request.
- Keep unrelated cleanup, dependency upgrades and generated files out of a PR.

## Code and files

- `src/envers/cli.py`: Typer command definitions and CLI presentation.
- `src/envers/core.py`: spec, release and profile operations.
- `src/envers/crypt.py`: password input and encryption through `cryptography`.
- `tests/`: pytest tests; `.makim.yaml` also defines CLI smoke tests.
- `pyproject.toml` / `poetry.lock`: dependencies and tool configuration.
- `README.md` / `docs/index.md`: user guides; routine code changes do not
  require edits to either file.
- `mkdocs.yaml`: documentation navigation and build configuration.

Preserve stored data on rejected operations. Never commit real secrets, put them
in public spec defaults, or expose them in logs or command arguments. Use
synthetic values in tests. Do not add shell evaluation to configuration values.
Treat unvalidated paths and plaintext output as explicit design concerns when
changing import/export behavior.

## Validation

Use Python 3.10+ and Poetry. Read `.makim.yaml` and the CI workflow when
changing their behavior; do not invent commands from older contributor
instructions.

```bash
poetry install
poetry run pytest
poetry run makim tests.smoke  # when changing CLI or the release workflow
poetry run pre-commit run --files <changed-files>
```

Run the relevant tests first, then the full small unit suite for runtime
changes. Do not broaden testing without a reason. Build docs when changing their
structure or configuration. Report commands actually run and any failures; do
not claim a container integration was tested without running it. Use
conventional commit/PR titles, such as `fix: preserve deployed profile values`.
