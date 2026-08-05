# Common Patterns

## Skeleton Projects

When implementing new functionality:
1. Search for battle-tested skeleton projects
2. Use parallel agents to evaluate options:
   - Security assessment
   - Extensibility analysis
   - Relevance scoring
   - Implementation planning
3. Clone best match as foundation
4. Iterate within proven structure

## Design Patterns

### Repository Pattern

Encapsulate data access behind a consistent interface:
- Define standard operations: findAll, findById, create, update, delete
- Concrete implementations handle storage details (database, API, file, etc.)
- Business logic depends on the abstract interface, not the storage mechanism
- Enables easy swapping of data sources and simplifies testing with mocks

### API Response Format

Use a consistent envelope for all API responses:
- Include a success/status indicator
- Include the data payload (nullable on error)
- Include an error message field (nullable on success)
- Include metadata for paginated responses (total, page, limit)

### Anti-Corruption Layer (Boundary Adapters)

An adapter that maps an internal type to an external one across a module boundary is **not** a redundant pass-through, even when the signatures look identical. It decouples the internal model from the external one and is what keeps the seam testable.

- A bridge that translates an internal command/marker (domain language) into an external infra command/marker (DTO) is a deliberate boundary, not an identity wrapper. Distinct internal and external marker types are the point — the domain depends only on the internal one, so a test can substitute a fake at that seam without touching the external infrastructure.
- A domain layer (entity + handler + store interface) is kept even when it carries no behavior yet — documented future use cases land there naturally. The DTO → entity → DTO "round-trip" is the deliberate price of separation.

Do not flag such layers as "thin wrapper", "identity wrapper", "valueless indirection", or "pass-through" in review and propose deleting them — that couples internal directly to external and removes the test seam. This is a recurring review misjudgment.
