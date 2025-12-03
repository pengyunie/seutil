## Workflow

- One step at a time, each code diff should be small for a focused review; for large changes, break them into smaller diffs, and let me review each diff before proceeding to the next.
- Ask questions for unclear specifications.
- No need to explain your thoughts. Show me the code.
- Commit message should have a prefix, a short title, and (concise) itemized changes (e.g., `[dev] add AGENTS.md\n\n* change1\n* change2`). The prefix can be:
  - a module’s name e.g., `io`: changes specific to that module
  - `dev`: changes to the build configuration, CI, metadata, etc.
  - `doc`: changes to documentation
  - `release`: bumping up release version
  - `deprecation`: deprecating/removing an old API/module
- Branch name format: `yyyymm-keywords`

## Development Environment and Tools

- Use `uv` for build config and execution environment:
  - Run Python commands with `uv run python ...` (it can be run from anywhere, no need to go back to the project root);
  - Add/modify dependencies with the corresponding uv commands, after which run `uv sync` to synchronize the virtual environment.
- Use `ruff format` for code formatting.
- Use `ruff check` for linting.

## Coding Style

- Prefer simple and elegant solutions.
- Prefer reusing existing code.
- Never silent errors. Raise if not sure, log if can be ignored for good reasons.
- Use up-to-date language and library features.
- Write professional comments that summarize the code as a whole, do not mix our conversations into the comments.
- Do not change code that is not related to the current task for reformatting; the formatter/linter will take care of it.
