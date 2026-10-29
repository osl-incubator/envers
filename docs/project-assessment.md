# Project assessment

Reviewed on 2026-10-29 against Envers upstream
[`a00b535`](https://github.com/osl-incubator/envers/commit/a00b535d38d62f4d3cf43441e887780adda8c39e)
and Sugar
[`736c43f`](https://github.com/sugar-org/sugar/commit/736c43f47d93e1a7b09d0f1492f3768f64bec73d).
Findings describe that baseline; the initial fixes are listed in the roadmap.

## Recommendation

Continue as a focused experiment in **release-specific configuration contracts
for Sugar projects**: check that each deployment profile supplies the variables
an application release requires, explain changes between releases, and provide
validated configuration before containers start.

Encrypted `.env` storage and basic validation already have capable alternatives.
The potential value is combining release requirements, profile checks and
Sugar's workflow. This is not yet implemented fully or demonstrated with real
users. Pilot it in two projects; if a small adapter around existing tools serves
them equally well, reduce Envers to that adapter or stop development.

## Goals and code

Envers addresses configuration drift between development, staging, production
and application releases. `cli.py` defines Typer commands; `core.py` combines
YAML specs, persistence, prompts and rendering; `crypt.py` handles password
input and Fernet encryption. The public contract lives in `.envers/specs.yaml`;
profile values and schema snapshots live in `.envers/data/<profile>.lock`.

`deploy` initializes a configuration release, rather than deploying an app.
`profile-set` edits values; `profile-load` writes plaintext files. Git retains
historical ciphertext, but `profile-versions` is currently a print-only stub.

Strengths are the small codebase, separate schema/profile concepts, multiple
output files, local operation, authenticated encryption through `cryptography`,
and existing Linux/macOS CI with unit, smoke and lint checks. These fit Sugar's
multi-profile workflow and make incremental improvement practical.

## Findings

| Priority                  | Evidence at upstream baseline                                                                                            | Consequence / action                                                 |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| First fix                 | Redeploy replaces saved values with defaults; draft can edit deployed schemas; recursive merges discard nested overrides | Preserve releases and reject accidental resets; addressed in this PR |
| Before production secrets | `draft --from-env` copies values into plaintext spec defaults and interpolates imported values                           | Separate schema discovery from encrypted value import                |
| Before production secrets | Profile prompts expose current values; empty passwords/EOF are accepted; export permissions depend on umask              | Hide secret input, validate credentials and control plaintext output |
| Before production secrets | Lock writes truncate before encryption completes; no atomic writes or concurrency control                                | Preserve the last good store on failures                             |
| Before integration        | Variable types are metadata only; malformed specs, paths and output types lack complete validation                       | Define a small enforced contract and constrain filesystem writes     |
| Before integration        | Export concatenates `name=value` without quoting                                                                         | Implement literal dotenv rendering and test supported consumers      |
| Usability                 | README commands/paths differ from CLI; installation is a placeholder; contributor instructions reference obsolete tools  | Replace with one tested walkthrough                                  |
| Packaging                 | No explicit build backend; mypy still targets Python 3.8 while runtime requires 3.10+                                    | Declare the backend and align tooling when addressing packaging      |

Synthetic experiments confirmed plaintext value import, changed values after a
quoted/multiline dotenv roundtrip, and a generated file mode of `0644` under the
review environment's umask. The seven original unit tests pass but mainly cover
happy paths. The new regression tests target release preservation.

Upstream main has 23 commits; the latest is from 2025-10-31. The latest
retrieved GitHub release is 0.4.1 from 2024-09-28. Recent commits are
maintenance/docs; most runtime behavior dates from 2023. This shows limited
momentum, not proof of absent users. Confirm user need and maintenance capacity
before expanding scope.

Evidence:
[runtime code](https://github.com/osl-incubator/envers/tree/a00b535d38d62f4d3cf43441e887780adda8c39e/src/envers),
[tests](https://github.com/osl-incubator/envers/tree/a00b535d38d62f4d3cf43441e887780adda8c39e/tests),
[history](https://github.com/osl-incubator/envers/commits/main/),
[releases](https://github.com/osl-incubator/envers/releases).

## Alternatives

These primary sources were checked during the review; this is a scope
comparison, not a benchmark or proof that Envers's proposed workflow is unique.

| Project                                                         | Overlap                                                           | Implication                                                                                          |
| --------------------------------------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| [SOPS](https://getsops.io/)                                     | Encrypted dotenv/YAML/JSON with age, PGP and cloud KMS identities | Evaluate as storage before expanding native key management                                           |
| [dotenvx](https://github.com/dotenvx/dotenvx)                   | Encrypted `.env`, per-environment keys, runtime injection         | Direct alternative for encrypted environment files                                                   |
| [git-crypt](https://github.com/AGWA/git-crypt)                  | Transparent encryption of selected Git files                      | Useful when repository-file protection is the actual need                                            |
| [dotenv-linter](https://github.com/dotenv-linter/dotenv-linter) | Checks, comparisons and schema validation                         | Basic validation alone does not distinguish Envers                                                   |
| [CUE](https://cuelang.org/docs/)                                | Configuration constraints, validation and generation              | Avoid inventing a general configuration language                                                     |
| [direnv](https://github.com/direnv/direnv)                      | Per-directory environment loading                                 | Adjacent developer workflow, rather than release management                                          |
| [Infisical](https://github.com/Infisical/infisical)             | Centralized secrets, versioning, rotation and access control      | Prefer a service-backed solution when governance is required; enterprise code has separate licensing |

[BlackBox](https://github.com/StackExchange/blackbox) is a historical
alternative, but its current README says it is abandoned and should not be used.

## Sugar integration

Sugar already owns profiles, services, backends and Compose arguments. Keep
Envers responsible for resolving and validating configuration. Explicitly map a
Sugar profile to an Envers profile and pinned release; do not select "latest"
implicitly or assume profile names match.

Sugar's inspected
[base extension](https://github.com/sugar-org/sugar/blob/736c43f47d93e1a7b09d0f1492f3768f64bec73d/src/sugar/extensions/base.py)
loads root environment files before defaults/profile selection. Current pre-run
hooks execute later and even precede its dry-run check; post-run hooks are not
guaranteed cleanup after failure. A hook-only integration therefore cannot
reliably supply early values or manage temporary secret files.

The
[Compose extension](https://github.com/sugar-org/sugar/blob/736c43f47d93e1a7b09d0f1492f3768f64bec73d/src/sugar/extensions/compose.py)
already accepts multiple `env-file` paths. Use a managed resolve/execute/cleanup
lifecycle, define environment precedence and keep dry-run free of secret output.
Test Compose interpolation separately from service environment injection;
[Docker's documentation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/)
also notes that `.env` substitution does not automatically apply to Swarm.
Validate Docker Compose first and Podman Compose separately.

See the [roadmap](roadmap.md). This review used code inspection and synthetic
experiments; it is not a security audit or an end-to-end container test.
