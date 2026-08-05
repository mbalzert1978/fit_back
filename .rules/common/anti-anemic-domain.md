# Anti-Anemic Domain Model

## Core Principle (CRITICAL)

Objects do their own work. Handlers orchestrate, not execute.

An **anemic domain** treats objects as passive data bags — the handler queries ports, inspects raw fields, and performs the domain logic itself.
A **rich domain** puts logic where the data lives — the object calls the port and returns a meaningful result.

```
// Pseudocode
WRONG:  if !port.IsReady(object) → return; if !port.IsReady(object.Sibling) → return; result = Type.Form(object.a, object.b)
CORRECT: result = object.ResolveAsync(port)   // object decides what "ready" means and how to form itself
```

## Handler Responsibility Contract

A handler must only:
- Accept a request
- Pass dependencies (ports) to domain objects
- Commit the result (write to store, publish event, return to caller)

A handler must never:
- Call ports repeatedly to reconstruct conditions the domain already knows
- Extract raw fields to feed into static factory calls
- Encode "is this object ready?" logic in `if`-chains
- Repeat port calls that duplicate domain invariants

## Object-Calls-Port Pattern

Prefer `object.OperationAsync(port, cancellationToken)` over `port.OperationAsync(object, cancellationToken)`.

The object owns the invariant. It knows which port calls it needs and what the results mean.
The port is an injectable dependency — a seam, not a decision-maker.

```
// CORRECT — object drives, port is the seam
if (await request.Path.FormGroupAsync(grouping, ct) is not { } group)
    return new GroupingResult.Pending();

await group.MarkMembersGroupedAsync(grouping, ct);

// WRONG — handler drives, object is passive data
if (!await grouping.IsDownloadedAsync(request.Path, ct)) return Pending();
if (!await grouping.IsDownloadedAsync(candidate.Sibling.Value, ct)) return Pending();
FileGroup group = FileGroup.Form(candidate.Stem, candidate.Jpl, candidate.Pdf);
await grouping.MarkGroupedAsync(candidate.Jpl.Value, candidate.Stem.Value, ct);
await grouping.MarkGroupedAsync(candidate.Pdf.Value, candidate.Stem.Value, ct);
```

## Domain Responsibilities

Domain objects own:
- The decision of whether an operation is possible
- How to form or transition themselves
- Naming of their own value concepts (stem, sibling, key)
- Iteration over their own members

Domain objects do not own:
- I/O (pass the port in, do not construct it)
- Publishing events (handler publishes what the domain produced)
- Error formatting or logging

## Checklist

Before marking a handler complete:
- [ ] Handler has no multi-step port queries that reconstruct domain state
- [ ] Static factory calls (`Type.Form(a, b, c)`) are inside the domain object, not the handler
- [ ] Member-level operations (`MarkMembersGroupedAsync`) are one call on the aggregate, not N calls in the handler
- [ ] Handler body fits in ~10 lines (orchestration only)
- [ ] All branching on domain state is inside domain methods, not `if`-chains in the handler
