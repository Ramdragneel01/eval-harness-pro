# Changelog

All notable changes to `eval-harness-pro` are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-04-30

### Added

- Initial public release.
- Declarative YAML eval suites: targets (`mock`, `http`), datasets (JSONL), judges, guards.
- Built-in judges: `exact_match`, `contains`, `regex`, `length`, `latency`, `cost`.
- Direction-aware guards (`higher_is_better`) with absolute `max_delta` tolerance.
- Three CLI subcommands: `run`, `diff`, `comment`.
- Markdown PR-comment renderer with regression / improvement badges.
- Composite GitHub Action (`action.yml`) wrapping the CLI; uploads artifacts.
- Example suite + 5-example dataset for self-contained smoke tests.
- 23 unit and integration tests covering schema, runner, judges, diff, renderer, and CLI.
- Documentation: `README.md`, `ARCHITECTURE.md`, `SECURITY.md`, `CONTRIBUTING.md`, `CODEOWNERS`.

[Unreleased]: https://github.com/Ramdragneel01/eval-harness-pro/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Ramdragneel01/eval-harness-pro/releases/tag/v0.1.0
