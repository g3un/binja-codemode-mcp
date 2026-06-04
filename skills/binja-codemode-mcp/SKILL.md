---
name: binja-codemode-mcp
description: Analyze binaries through Binary Ninja. Use this skill for reverse engineering tasks, static binary analysis, or when the user asks to use Binary Ninja/binja; useful for inspecting functions, strings, xrefs, symbols, types, and IL.
---

# Binja Codemode MCP

Use `binja-codemode-mcp` as a code-mode interface to the Binary Ninja Python API. Prefer writing Python that performs the Binary Ninja analysis inside one `execute()` call, filters intermediate data in Python, and prints only the concise results needed by the user.

## Session Choice

- Use `stdio` by default for headless analysis. It launches a dedicated Binary Ninja worker process for the session and does not require a separate HTTP server.
- Use `http` when attaching to an already-running Binary Ninja MCP HTTP server, including the GUI plugin server or a headless server started with `serve`.
- Treat each session as stateful: globals persist between `execute()` calls. Load the binary once into `bv`, define helper functions as needed, and reuse them in later calls.
- Close sessions when finished.

## Standard Workflow

1. Create a session with `create_session(transport="stdio")` unless the user specifically needs `http`.
2. Load the binary and wait for analysis:
   ```python
   import binaryninja as bn
   bv = bn.load(path)
   bv.update_analysis_and_wait()
   print(bv.view_type, bv.arch, bv.platform, hex(bv.entry_point))
   ```
3. Perform analysis in Python using loops, filters, joins, sorting, and aggregation.
4. Print short summaries, addresses, names, counts, and top-N results. Do not dump full Binary Ninja objects or large collections.
5. Reuse `bv` and helper functions in later `execute()` calls.
6. Close the session when the task is complete.

## Code Mode Rules

- Favor one meaningful Python script over many small MCP calls.
- Keep intermediate results inside Python. Return only final summaries or selected evidence.
- Use `dir()`, `inspect.signature()`, and `inspect.getdoc()` for focused API discovery instead of printing entire modules or object graphs.
- Limit result size explicitly, for example with `[:20]`, `max_items`, thresholds, or top-N sorting.
- Convert Binary Ninja objects to stable identifiers before printing: addresses, names, operation names, variable names, short token text, and counts.
- If an operation may be slow, first count or sample results, then narrow the query.

## Permission Policy for Changes

Reading, searching, summarizing, and inspecting Binary Ninja state is allowed.

Before performing any operation that writes, mutates, annotates, patches, saves, renames, edits types, creates databases, changes comments, changes symbols, or modifies GUI/shared state, ask the user for explicit permission.

This applies to both `stdio` and `http`. It is especially important for `http` sessions because they may be attached to the user's running Binary Ninja GUI process or another shared Binary Ninja process.

Examples of operations that require explicit permission include:

- `bv.write`, `bv.insert`, `bv.remove`, `bv.convert_to_nop`
- `bv.define_user_symbol`, `bv.define_user_type`, `bv.define_user_data_var`
- `bv.create_user_function`, `bv.remove_user_function`
- `bv.set_comment_at`, `f.set_comment_at`
- `f.set_user_type`, variable rename/type changes
- `bv.create_database` or saving analysis databases
- GUI navigation, opening/closing tabs, or other UI actions

## Reference Files

Read these files only when needed:

- `references/api-reference.md`: Binary Ninja API areas, common methods, and mutation-sensitive methods.
- `references/analysis-workflows.md`: Concrete Python workflows for common binary analysis tasks.
- `references/advanced-analysis.md`: Advanced workflows for SSA/dataflow, branch-condition provenance, and call argument/return tracking.
