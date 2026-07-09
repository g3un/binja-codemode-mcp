# Binary Ninja API Reference

Use this when you need to pick the right Binary Ninja Python API for an analysis script.

## Session and Environment

`stdio` sessions usually run in a private headless Binary Ninja worker. Use this for normal analysis automation.

`http` sessions attach to a Binary Ninja MCP HTTP server that is already running. That may be the GUI plugin server, or a headless process started with `serve`. The process may be shared with the user, so ask before changing any state.

Both session types keep state across `execute()` calls. Globals such as `bv`, helper functions, cached addresses, and selected functions stay around until the session closes.

## Loading and Analysis

Common APIs:

- `bn.load(path)` opens a `BinaryView`.
- `bv.update_analysis_and_wait()` waits for analysis completion.
- `bv.view_type`, `bv.arch`, `bv.platform`, `bv.endianness`
- `bv.start`, `bv.end`, `bv.entry_point`, `bv.entry_function`
- `bv.analysis_info`, `bv.analysis_state`, `bv.analysis_progress`

Typical setup:

```python
import binaryninja as bn
bv = bn.load(path)
bv.update_analysis_and_wait()
print('loaded', bv.view_type, bv.arch, bv.platform, hex(bv.entry_point))
```

## BinaryView Data

Common properties:

- `bv.functions`
- `bv.strings`
- `bv.symbols`
- `bv.data_vars`
- `bv.segments`
- `bv.sections`
- `bv.libraries`
- `bv.metadata`

Common methods:

- `bv.read(addr, length)`
- `bv.read_int(addr, size)`
- `bv.read_pointer(addr)`
- `bv.get_ascii_string_at(addr)`
- `bv.get_entropy(addr, length)`
- `bv.search(start, end, data)`
- `bv.find_all_data(...)`, `bv.find_next_data(...)`
- `bv.find_all_text(...)`, `bv.find_next_text(...)`
- `bv.find_all_constant(...)`, `bv.find_next_constant(...)`

## Functions

Common function lookup:

- `bv.get_function_at(addr)`
- `bv.get_functions_at(addr)`
- `bv.get_functions_containing(addr)`
- `bv.get_functions_by_name(name)`
- `bv.get_next_function_start_after(addr)`
- `bv.get_previous_function_start_before(addr)`

Common function properties:

- `f.name`, `f.start`, `f.symbol`
- `f.address_ranges`, `f.lowest_address`, `f.highest_address`
- `f.basic_blocks`, `f.instructions`
- `f.callers`, `f.callees`, `f.call_sites`, `f.callee_addresses`
- `f.vars`, `f.parameter_vars`, `f.stack_layout`
- `f.type`, `f.return_type`, `f.calling_convention`
- `f.llil_if_available`, `f.mlil_if_available`, `f.hlil_if_available`, `f.pseudo_c_if_available`

Useful methods:

- `f.get_instruction_containing_address(addr)`
- `f.get_llil_at(addr)`, `f.get_mlil_var_refs(var)`, `f.get_hlil_var_refs(var)`
- `f.get_constants_referenced_by(addr)`
- `f.get_regs_read_by(addr)`, `f.get_regs_written_by(addr)`
- `f.get_stack_contents_at(addr, offset, size)`
- `f.get_reg_value_at(addr, reg)`

## Basic Blocks and Control Flow

Common properties:

- `bb.start`, `bb.end`, `bb.length`
- `bb.incoming_edges`, `bb.outgoing_edges`
- `bb.dominators`, `bb.immediate_dominator`
- `bb.disassembly_text`

These are handy for control-flow summaries, graph traversal, and rough function-complexity checks.

## Cross References

Common APIs:

- `bv.get_code_refs(addr, max_items=None)`
- `bv.get_code_refs_from(addr)`
- `bv.get_data_refs(addr, max_items=None)`
- `bv.get_data_refs_from(addr)`
- `bv.get_callers(callee)`
- `bv.get_callees(caller)`

`get_code_refs()` returns reference source objects. Print `ref.address` and `ref.function.name` instead of the whole object.

## Symbols, Types, and Data Variables

Symbols:

- `bv.get_symbol_at(addr)`
- `bv.get_symbols_by_name(name)`
- `bv.get_symbols_by_raw_name(name)`
- `bv.get_symbols_of_type(symbol_type)`
- `bn.SymbolType.FunctionSymbol`, `DataSymbol`, `ImportedFunctionSymbol`, `ImportAddressSymbol`

Types:

- `bv.get_type_by_name(name)`
- `bv.get_types_referenced(addr)`
- `bv.get_type_refs_for_type(name)`
- `bn.Type.int(width)`, `bn.Type.pointer(arch, type)`, `bn.Type.array(type, count)`, `bn.Type.structure(...)`, `bn.Type.function(...)`

Data variables:

- `bv.data_vars`
- `bv.get_data_var_at(addr)`
- `dv.address`, `dv.name`, `dv.type`, `dv.value`, `dv.code_refs`, `dv.data_refs`

## IL APIs

Common properties:

- `f.llil`, `f.mlil`, `f.hlil`
- `f.llil_if_available`, `f.mlil_if_available`, `f.hlil_if_available`
- `f.pseudo_c_if_available`

Instruction properties:

- `insn.address`
- `insn.operation`
- `insn.operands`
- `insn.tokens`
- `insn.vars_read`, `insn.vars_written`
- `insn.possible_values`
- `insn.llil`, `insn.mlil`, `insn.hlil`

Operation enums:

- `bn.LowLevelILOperation`
- `bn.MediumLevelILOperation`
- `bn.HighLevelILOperation`

For advanced SSA/dataflow APIs, open `advanced-analysis.md`.

When listing IL facts, print operation names and short token strings:

```python
text = ''.join(tok.text for tok in insn.tokens)
print(hex(insn.address), insn.operation.name, text[:120])
```

When structure matters, do not rely on indentation or whitespace alone.
Decompiled code and `f.hlil_if_available.root.lines` may be indentation-based,
instruction `tokens` skip indentation/newlines, and custom tree/dataflow dumps
often use indentation for depth. Add explicit `{}` braces, `BEGIN`/`END`
markers, node IDs with edge lists, JSON, or S-expressions. For indented text
lines, use `print_braced_lines()` from `analysis-workflows.md`.

## API Discovery

Use focused introspection:

```python
import inspect
for name in dir(bv):
    if 'ref' in name.lower():
        print(name)

print(inspect.signature(bv.get_code_refs))
print('\n'.join((inspect.getdoc(bv.get_code_refs) or '').splitlines()[:5]))
```

Avoid dumping all of `dir(binaryninja)` or whole object representations unless the user asks for that.

## Operations Requiring Permission

Ask the user before using APIs that mutate state or the binary, including:

- Patching and bytes: `bv.write`, `bv.insert`, `bv.remove`, `bv.convert_to_nop`
- Symbols/types/data: `define_user_symbol`, `define_user_type`, `define_user_data_var`, `undefine_user_data_var`
- Functions: `create_user_function`, `remove_user_function`, `f.set_user_type`
- Comments/tags/metadata: `set_comment_at`, `add_tag`, `store_metadata`, `remove_metadata`
- Database and project state: `create_database`, project file changes, saving databases
- GUI or shared process actions: navigation, opening/closing files, UI dialogs, report windows unless requested
