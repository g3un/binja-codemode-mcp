---
name: binja-codemode-mcp
description: Analyze binaries with Binary Ninja. Use this for reverse engineering, static analysis, or any request that mentions Binary Ninja/binja; good for functions, strings, xrefs, symbols, types, and IL.
---

# Binja Codemode MCP

Use `binja-codemode-mcp` as a code-mode path into the Binary Ninja Python API.
Do the real work inside one `execute()` call when you can: load data, filter it
in Python, then print the small result the user needs.

## Session Choice

- Use `stdio` by default for headless analysis. It starts a private Binary Ninja
  worker for the session and does not need a separate HTTP server.
- Use `http` only when you need an already-running Binary Ninja MCP HTTP server,
  such as the GUI plugin server or a headless server started with `serve`.
- Sessions are stateful. Globals persist between `execute()` calls, so load the
  binary once into `bv`, define helpers if useful, and reuse them.
- Close sessions when finished.

## Standard Workflow

1. Create a session with `create_session(transport="stdio")` unless the user
   specifically needs `http`.
2. Load the binary and wait for analysis:
   ```python
   import binaryninja as bn
   bv = bn.load(path)
   bv.update_analysis_and_wait()
   print(bv.view_type, bv.arch, bv.platform, hex(bv.entry_point))
   ```
3. Analyze in Python with loops, filters, joins, sorting, and aggregation.
4. Print short summaries: addresses, names, counts, and top-N results. Do not
   dump whole Binary Ninja objects or huge collections.
5. Reuse `bv` and helper functions in later `execute()` calls.
6. Close the session when the task is done.

## Code Mode Rules

- Prefer one useful Python script over a chain of tiny MCP calls.
- Keep intermediate results in Python. Return final summaries or selected
  evidence only.
- Use `dir()`, `inspect.signature()`, and `inspect.getdoc()` for focused API
  discovery. Do not print entire modules or object graphs.
- Put a hard cap on result size: `[:20]`, `max_items`, thresholds, or top-N
  sorting.
- Print stable identifiers for Binary Ninja objects: addresses, names, operation
  names, variable names, short token text, and counts.
- Do not use indentation alone to show structure in output meant for an LLM. For
  decompiled code, IL, trees, CFGs, and dataflow traces, print explicit
  structure: `{}`, `BEGIN`/`END`, node IDs with edge lists, JSON, or
  S-expressions.
- If something may be slow, count or sample first, then narrow the query.

## Permission Policy for Changes

Reading, searching, summarizing, and inspecting Binary Ninja state is fine.

Ask the user before anything that writes, mutates, annotates, patches, saves,
renames, edits types, creates databases, changes comments, changes symbols, or
touches GUI/shared state.

This rule applies to both `stdio` and `http`. Be extra careful with `http`: it
may be attached to the user's live Binary Ninja GUI process or another shared
process.

Examples that need explicit permission:

- `bv.write`, `bv.insert`, `bv.remove`, `bv.convert_to_nop`
- `bv.define_user_symbol`, `bv.define_user_type`, `bv.define_user_data_var`
- `bv.create_user_function`, `bv.remove_user_function`
- `bv.set_comment_at`, `f.set_comment_at`
- `f.set_user_type`, variable rename/type changes
- `bv.create_database` or saving analysis databases
- GUI navigation, opening/closing tabs, or other UI actions

## Reference Files

Open these only when they help:

- `references/api-reference.md`: Binary Ninja API areas, common methods, and
  mutation-sensitive methods.
- `references/analysis-workflows.md`: Python snippets for common binary analysis
  tasks.
- `references/advanced-analysis.md`: SSA/dataflow, branch-condition provenance,
  and call argument/return tracking.
