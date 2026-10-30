# Roadmap

Proposed 2026-10-29. See the [assessment](project-assessment.md) for evidence.
Envers is pre-stable: prefer direct changes over compatibility layers. Phases
give priority and completion criteria, not delivery-date commitments.

## 1. Preserve configuration releases — this PR

- [x] Reject repeat deployment to the same profile/release instead of resetting
      saved values. Keep `profile-set` available for value edits.
- [x] Reject draft edits to releases that are no longer drafts.
- [x] Apply nested draft overrides correctly.
- [x] Reject undeclared deployment profiles and invalid release states.
- [x] Refuse to reinitialize an empty/invalid existing lock.
- [x] Test these regressions and retaining releases across profile deployments.

Done when relevant regressions and the existing tests pass. These are CLI
guards; manual schema edits, concurrent writers and interrupted writes remain
open work.

## 2. Fix secret handling and persistence

- [x] Import schema names without copying secret values into public defaults;
      import declared values explicitly into encrypted profile releases.
- [x] Preserve literal imported values, hide secret prompts, reject empty
      credentials/EOF, and document unattended credential input.
- [x] Serialize/encrypt profiles before writes; replace profile locks atomically
      using private temporary files (owner-only permissions on POSIX).
- [x] Write specs atomically during initialization, drafting and deployment,
      using private temporary files (owner-only permissions on POSIX).
- [ ] Add concurrency control and recovery across lock/spec updates. Atomic
      replacement of each file does not make deployment a transaction or
      guarantee power-loss durability.
- [ ] Validate profile/output paths against an explicit root, including symlinks
      and collisions with project metadata.
- [ ] Specify native Fernet envelope/KDF settings, password rotation and
      recovery. SOPS and additional storage backends are optional integrations
      driven by user demand; defer a provider framework.
- [ ] Declare the build backend and verify a clean wheel installation, declared
      dependencies and version reporting; align Python tooling.

Done when synthetic secrets stay out of public specs/logs and failed operations
preserve readable data. Document handling of already-committed values, including
credential rotation. Complete this phase before recommending production secrets.

## 3. Enforce the release contract

- [ ] Validate document structure, types, required values, allowed values,
      supported files and unset versus empty values.
- [ ] Add non-interactive validation with useful exit codes and diagnostics that
      omit values; expose the same behavior through a small Python API.
- [ ] Bind profiles to one schema identity per release; detect manual drift.
      Define schema releases versus value revisions before adding
      history/rollback.
- [ ] Compare releases and report variables that need operator input or
      migration.
- [x] Quote literal dotenv output and test hashes, quotes, newlines, backslashes
      and dollar signs with python-dotenv interpolation disabled.
- [ ] Verify dotenv output with Compose, including its interpolation rules,
      before Sugar integration.
- [ ] Add selective file export and explicit output placement; replace the
      `profile-versions` stub with useful behavior or remove it.
- [x] Replace outdated usage instructions with one tested import/export
      walkthrough. Clean package installation remains part of phase 2.

Done when CI can validate several profiles against a pinned release without
prompts or writes, and supported values survive rendering into their consumers.

## 4. Integrate with Containers Sugar

Coordinate corresponding changes in `sugar-org/sugar`.

- [ ] Map Sugar profiles explicitly to Envers profiles/releases and credential
      sources. Store only non-secret identifiers in Sugar configuration.
- [ ] Resolve values before Sugar defaults when needed; otherwise scope them to
      backend execution. Define caller/file/profile precedence.
- [ ] Manage validate/materialize/execute/cleanup through an explicit lifecycle;
      do not rely on existing pre/post hooks for early loading or reliable
      cleanup.
- [ ] Keep dry-run free of decryption/materialization, and redact command/log
      output that could expose resolved values.
- [ ] Ship one synthetic example and container tests for Docker Compose, then
      Podman Compose. Treat Swarm as separate work.

Done when invalid configuration stops execution before containers start and
tests cover profile selection, precedence, dry-run and cleanup after failure.

## 5. Decide whether to expand

Pilot two real Sugar projects across two application releases each. Compare the
same tasks with SOPS/dotenvx, schema checks and a small Sugar adapter. Record
configuration mistakes caught, setup/maintenance effort and migration friction.
Continue only if Envers's release/profile model adds useful value and has a
maintainer; otherwise simplify it to an adapter or deprecate it.

Existing issues:
[#12 password changes](https://github.com/osl-incubator/envers/issues/12)
belongs to phase 2;
[#13 selective export](https://github.com/osl-incubator/envers/issues/13) and
[#19 profile subcommands](https://github.com/osl-incubator/envers/issues/19)
belong to phase 3. Tests/docs (#16, #17) accompany relevant changes. Defer
[#14 dynamic xonsh values](https://github.com/osl-incubator/envers/issues/14),
additional formats, a web UI and orchestration features until the core workflow
has demonstrated value.
