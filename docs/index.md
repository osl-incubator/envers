# Envers

`Envers` is a command-line tool (CLI) designed to manage and version environment
variables for different deployment stages such as staging, development, and
production. It provides a secure and organized way to handle
environment-specific configurations.

## Features

- Encrypt environment variables: Creates encrypted files that store environment
  variables that can be safely stored in a git repository
- Group-Based Configurations: Allows defining variables for different
  groups/profiles like prod, dev, etc.
- File-Based Variable Definitions: Supports multiple environment files (.env)
  with specific variables for each file.
- CLI-Driven: Provide CLI commands that helps to create drafts for environment
  variables and deploy it to encrypted files
- Spec Management: Each release has a defined spec that applies to all
  groups/profiles within that release.
- Environment File Generation: Enables generating .env files for specific
  versions and groups/profiles using commands.

## Installation

TBD

## Usage

Start with an existing `.env` file and keep it out of Git:

```bash
envers init
envers draft 1.0 --from-env .env
envers deploy --profile base --spec 1.0
envers profile-import --profile base --spec 1.0 --from-env .env
envers profile-load --profile base --spec 1.0
```

`draft --from-env` discovers variable names without copying values into
`.envers/specs.yaml`. Edit types, documentation and non-secret defaults there
before deploying. The spec is public metadata; values belong in the encrypted
`.envers/data/<profile>.lock` file. Review defaults imported by older versions
and rotate credentials that were committed or otherwise exposed.

`profile-import` updates values in an already-deployed profile/release. It never
changes the public spec or expands `${VARIABLE}` references. Omitted variables
keep their saved values; `NAME=` sets an empty string. Bare names without `=`,
undeclared variables and malformed syntax reject the entire import. Diagnostics
do not print values.

The source defaults to the same file path declared in the release. To import
from another location, select the declared file explicitly:

```bash
envers profile-import --profile base --spec 1.0 --from-env input.env --file .env
```

For interactive changes, use `envers profile-set --profile base --spec 1.0`.
Saved and entered values stay hidden. Enter keeps a value; Ctrl+C discards the
edit. Use `profile-import` to set an empty value.

`profile-load` writes plaintext files using dotenv quoting and atomic
replacement, with owner-only permissions on POSIX. When reading them with
python-dotenv, use `dotenv_values(path, interpolate=False)` to preserve dollar
references literally. These files are not shell scripts. Compatibility with
Compose's interpolation rules still needs verification before Sugar integration.

Release schemas become read-only to draft commands after deployment. Repeating
`deploy` for the same profile/release fails without resetting values. Use
`envers draft 2.0 --from-spec 1.0` for a new schema version; another declared
profile can use the same release.

### Password input

Interactive password prompts are hidden. The first deployment of a profile asks
for a password and confirmation; later commands ask once. Empty passwords and
EOF are rejected. Spaces and tabs are significant and are preserved.

For unattended runs, supply a newline-terminated password on stdin from your
credential source. A new profile needs two identical lines for confirmation;
existing profiles need one. Passwords are not accepted as command-line options.
The Python API also rejects empty password strings.

## Roadmap

See the [project assessment](project-assessment.md) and
[development roadmap](roadmap.md) for priorities and Containers Sugar
integration. Envers is pre-stable; path validation, concurrency control and
recovery across lock/spec updates remain open before production-secret use.

## Contributing

https://osl-incubator.github.io/envers

## License

BSD-Clause 3
