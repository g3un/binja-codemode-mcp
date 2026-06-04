# Advanced Binary Analysis

Use this reference only for advanced analysis tasks such as dataflow, SSA def-use tracking, branch-condition provenance, phi-node inspection, or call argument/return tracking. For ordinary function, string, xref, symbol, and section inspection, prefer `analysis-workflows.md`.

## SSA Dataflow APIs

Prefer MLIL SSA for most value-flow questions because it is lower-level than HLIL but easier to inspect than LLIL.

Common APIs:

- `f.mlil_if_available.ssa_form`, `f.hlil_if_available.ssa_form`, `f.llil_if_available.ssa_form`
- `ssa.instructions`, `ssa.basic_blocks`, `ssa.ssa_vars`
- `ssa.get_ssa_var_definition(ssa_var)`
- `ssa.get_ssa_var_uses(ssa_var)`
- `ssa.get_ssa_var_value(ssa_var)`
- `ssa.get_var_definitions(var)`, `ssa.get_var_uses(var)`
- `ssa.is_ssa_var_live(ssa_var)`, `ssa.is_ssa_var_live_at(ssa_var, instr)`
- `insn.vars_read`, `insn.vars_written`
- SSA operations such as `MLIL_SET_VAR_SSA`, `MLIL_VAR_PHI`, `MLIL_MEM_PHI`, `MLIL_CALL_SSA`

Output guidelines:

- Print SSA variable names, definition addresses, use addresses, operation names, and short token text.
- Do not print complete IL objects.
- Keep recursion depth small when doing backward or forward slices.
- Stop at user inputs, function parameters, calls, memory loads, or ambiguous phi nodes unless the user asks for deeper analysis.

## Follow SSA Definitions and Uses

Use this when tracking where a value came from or where it flows.

```python
f = bv.get_function_at(addr) or bv.get_functions_containing(addr)[0]
mlil = f.mlil_if_available
if not mlil:
    print('MLIL not available')
else:
    ssa = mlil.ssa_form
    print('function', hex(f.start), f.name, 'ssa vars', len(list(ssa.ssa_vars)))

    rows = []
    for v in ssa.ssa_vars:
        definition = ssa.get_ssa_var_definition(v)
        uses = ssa.get_ssa_var_uses(v)
        if definition and len(uses) >= 2:
            value = ssa.get_ssa_var_value(v)
            rows.append((len(uses), v, definition, uses, value))

    for use_count, v, definition, uses, value in sorted(rows, reverse=True, key=lambda x: x[0])[:15]:
        print('VAR', v, 'uses', use_count, 'value', value)
        print('  def', hex(definition.address), definition.operation.name, short_text(definition.tokens))
        for use in uses[:5]:
            print('  use', hex(use.address), use.operation.name, short_text(use.tokens))
```

## Backward Slice from a Branch Condition

Use this when the user asks why a branch is taken, how a condition is computed, or where a checked value comes from.

```python
f = bv.get_functions_containing(branch_addr)[0]
ssa = f.mlil_if_available.ssa_form

branch = None
for insn in ssa.instructions:
    if insn.address == branch_addr and 'IF' in insn.operation.name:
        branch = insn
        break

if branch is None:
    print('no SSA branch at', hex(branch_addr))
else:
    print('branch', hex(branch.address), short_text(branch.tokens))
    seen = set()

    def show_var(v, depth=0):
        if str(v) in seen or depth > 3:
            return
        seen.add(str(v))
        definition = ssa.get_ssa_var_definition(v)
        value = ssa.get_ssa_var_value(v)
        indent = '  ' * depth
        if definition is None:
            print(indent, 'input', v, 'value', value)
            return
        print(indent, 'def', v, 'value', value, '@', hex(definition.address), definition.operation.name, short_text(definition.tokens))
        for source in getattr(definition, 'vars_read', [])[:8]:
            show_var(source, depth + 1)

    for v in branch.vars_read:
        show_var(v)
```

## Inspect Calls in MLIL SSA

Use call SSA form to identify return values, memory versions, and arguments without printing full IL objects.

```python
import binaryninja as bn
call_ops = {
    bn.MediumLevelILOperation.MLIL_CALL_SSA,
    bn.MediumLevelILOperation.MLIL_CALL_UNTYPED_SSA,
    bn.MediumLevelILOperation.MLIL_TAILCALL_SSA,
}

for f in bv.functions:
    mlil = f.mlil_if_available
    if not mlil:
        continue
    for insn in mlil.ssa_form.instructions:
        if insn.operation in call_ops:
            reads = ', '.join(str(v) for v in getattr(insn, 'vars_read', [])[:8])
            writes = ', '.join(str(v) for v in getattr(insn, 'vars_written', [])[:8])
            print(hex(insn.address), f.name, insn.operation.name)
            print('  text  ', short_text(insn.tokens))
            print('  reads ', reads)
            print('  writes', writes)
```

## When Not to Use SSA

Avoid SSA-first analysis for broad triage or simple lookup tasks. For these, use the simpler workflows instead:

- Listing functions, imports, strings, sections, or symbols
- Finding xrefs to a known address or string
- Summarizing call graph neighborhoods
- Showing pseudocode or HLIL for a function
- Checking segment permissions or binary metadata
