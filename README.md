# Envers

`Envers` is a command-line tool (CLI) designed to manage and version
environment variables for different deployment stages such as staging,
development, and production. It provides a secure and organized way to
handle environment-specific configurations.

## Features

- **Encrypted Variable Management**: Uses Ansible Vault for encrypting
  sensitive variables.
- **Versioning**: Manages environment variables by versions and groups
  within a `.envers/envers.yaml` file.
- **Group-Based Configurations**: Allows defining variables for different
  groups like `prod`, `dev`, etc.
- **File-Based Variable Definitions**: Supports multiple environment files
  (.env) with specific variables for each file.
- **CLI-Driven**: All interactions with `.envers/.envers.yaml` are done
  through the CLI, ensuring consistency and security.
- **Two-Stage Management**: Similar to git, `envers` operates in two stages -
  development (`dev`) and release.
- **Spec Management**: Each release has a defined spec that applies to all
  groups within that release.
- **Environment File Generation**: Enables generating .env files for specific
  versions and groups using commands.

## Installation

TBD

## Usage

Below are the initial subcommands for `envers`:

- `envers init`: Initialize the `envers` environment.
- `envers spec create`: Create a new spec.
- `envers spec update`: Update an existing spec.
- `envers spec remove`: Remove an existing spec.
- `envers content add`: Add new content.
- `envers content update`: Update existing content.
- `envers content remove`: Remove existing content.
- `envers generate`: Generate environment files based on specified version and group.

### Examples

Generate environment files for a specific version and group:

```
envers --version 0.1.0 --group prod
```

This command will create the environment files (.env) at the specified
paths with the variables and values for the `prod` group.

## Roadmap

- Integration with Ansible Vault for encryption.
- Detailed spec and content management functionalities.
- Enhancements in versioning and group management.

## Contributing

https://osl-incubator.github.io/envers

## License

BSD-Clause 3
