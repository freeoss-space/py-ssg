# Repository Guidelines

## Tooling

- Use `uv` for Python commands.
- Run tests with `uv run pytest`.
- Run lint with `uv run ruff check`.
- Run type checks with `uv run ty check`.
- Prefer targeted test runs while iterating, then finish with the full suite.

## Typing

- Type every method parameter explicitly.
- Type return values explicitly.
- Do not use `...` for typing.
- Avoid introducing implicit `Any` in production code.
- When adding helpers, keep signatures narrow and concrete.
- If a shape becomes complex, such as nested `dict`, `list`, `tuple`, or mixed container data, introduce a dedicated type instead of passing raw nested structures around.
- Prefer `dataclass`es or other named type classes for structured data that has meaning in the domain.
- Use named structured types to replace opaque container types when they improve readability, validation, reuse, or testability.

## Design

- Favor single-responsibility methods.
- If a test needs many patches, treat that as a design smell and refactor the production code.
- Prefer extracting small helpers over growing orchestration methods.
- Keep orchestration methods thin and test their collaborators separately.

## Testing

- Prefer unit tests that exercise the smallest useful unit.
- Use real temporary directories and files with `tmp_path` when practical instead of mocking filesystem behavior.
- Prefer simple fakes or `MagicMock` collaborators over patching large call graphs.
- Use decorator-level patching only.
- Do not use context-manager patching with `with patch(...)` or `with patch.object(...)`.
- Keep end-to-end orchestration tests minimal; cover detailed behavior at helper-method level.

## Editing

- Preserve existing behavior unless the task explicitly changes it.
- Keep refactors incremental and verified.
- After code changes, run:
  - `uv run pytest`
  - `uv run ruff check`
  - `uv run ty check`
