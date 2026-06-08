# Binary Analysis Workflows

Use these workflows as starting points for Python code passed to `execute()`. Adapt paths, addresses, names, and filters to the user's task. Keep output concise.

## Load a Binary Once

```python
import binaryninja as bn
path = '/path/to/binary'
bv = bn.load(path)
bv.update_analysis_and_wait()
print('view', bv.view_type, 'arch', bv.arch, 'platform', bv.platform)
print('entry', hex(bv.entry_point), 'range', hex(bv.start), hex(bv.end))
print('counts', {
    'functions': len(list(bv.functions)),
    'strings': len(list(bv.strings)),
    'symbols': len(list(bv.symbols)),
    'data_vars': len(list(bv.data_vars)),
})
```

## Create Small Helper Functions

Helpers persist in the session and reduce repetition. When output structure matters, do not encode it with indentation alone; use braces, BEGIN/END markers, node IDs with edge lists, JSON, or S-expressions.

```python
from itertools import islice

def short_text(tokens_or_obj, limit=120):
    if isinstance(tokens_or_obj, str):
        s = tokens_or_obj
    else:
        try:
            s = ''.join(tok.text for tok in tokens_or_obj)
        except TypeError:
            s = str(tokens_or_obj)
    return s.replace('\n', ' ')[:limit]

def line_text(line):
    tokens = getattr(line, 'tokens', None)
    if tokens is None:
        return str(line)
    return ''.join(tok.text for tok in tokens)

def print_braced_lines(lines, max_lines=120):
    # For Binary Ninja text lines whose nesting may otherwise be indentation-only.
    rendered = [line_text(line).rstrip() for line in islice(lines, max_lines)]
    has_block_braces = any(
        line.strip() in {'{', '}'} or line.rstrip().endswith('{') or line.lstrip().startswith('}')
        for line in rendered
    )
    if has_block_braces:
        for line in rendered:
            print(line)
        return

    indents = [0]
    for raw in rendered:
        expanded = raw.expandtabs(4).rstrip()
        if not expanded.strip():
            print()
            continue
        indent = len(expanded) - len(expanded.lstrip(' '))
        while indent < indents[-1]:
            indents.pop()
            print(' ' * indents[-1] + '}')
        if indent > indents[-1]:
            print(' ' * indents[-1] + '{')
            indents.append(indent)
        print(' ' * indent + expanded.lstrip(' '))
    while len(indents) > 1:
        indents.pop()
        print(' ' * indents[-1] + '}')

def func_summary(f):
    return {
        'start': hex(f.start),
        'name': f.name,
        'blocks': len(list(f.basic_blocks)),
        'calls': len(list(f.call_sites)),
        'vars': len(list(f.vars)),
    }
```

## Summarize Interesting Functions

```python
funcs = sorted(bv.functions, key=lambda f: (len(list(f.basic_blocks)), f.highest_address - f.lowest_address), reverse=True)
for f in funcs[:20]:
    size = f.highest_address - f.lowest_address
    print(hex(f.start), f.name, 'size', size, 'blocks', len(list(f.basic_blocks)), 'calls', len(list(f.call_sites)))
```

## Search Strings and Find Referencing Functions

```python
keywords = ['password', 'token', 'secret', 'key', 'auth', 'error']
results = []
for s in bv.strings:
    text = str(s.value)
    if not any(k in text.lower() for k in keywords):
        continue
    refs = list(bv.get_code_refs(s.start, max_items=50))
    funcs = sorted({ref.function.name for ref in refs if ref.function})
    results.append((s.start, text, funcs))

print('matching strings', len(results))
for addr, text, funcs in results[:30]:
    print(hex(addr), repr(text[:80]), 'refs', funcs[:8])
```

## Inspect a Function by Name or Address

```python
name = 'main'
funcs = list(bv.get_functions_by_name(name))
if not funcs:
    print('not found:', name)
else:
    f = funcs[0]
    print('function', hex(f.start), f.name)
    print('blocks', len(list(f.basic_blocks)), 'vars', [v.name for v in list(f.vars)[:20]])
    print('callers', [c.name for c in list(f.callers)[:20]])
    print('callees', [c.name for c in list(f.callees)[:20]])
    if f.pseudo_c_if_available:
        print_braced_lines(f.pseudo_c_if_available.lines, max_lines=120)
    elif f.hlil_if_available:
        print_braced_lines(f.hlil_if_available.root.lines, max_lines=120)
```

For address-based lookup:

```python
addr = 0x1000
funcs = bv.get_functions_containing(addr)
for f in funcs:
    print(hex(f.start), f.name)
```

## Build an Import or Symbol Caller Map

```python
targets = []
for sym in bv.symbols:
    name = sym.full_name or sym.name
    if any(k in name.lower() for k in ['crypt', 'open', 'read', 'write', 'exec', 'socket', 'connect']):
        targets.append(sym)

for sym in targets[:50]:
    refs = list(bv.get_code_refs(sym.address, max_items=100))
    funcs = sorted({ref.function.name for ref in refs if ref.function})
    if funcs:
        print(hex(sym.address), sym.full_name, 'called_by', funcs[:20])
```

## Find Constant Uses

```python
constants = [0xdeadbeef, 0x1000]
for value in constants:
    hits = []
    for f in bv.functions:
        for ref in f.get_constants_referenced_by(value):
            hits.append((ref.address, f.name))
    print('constant', hex(value), 'hits', len(hits))
    for addr, name in hits[:30]:
        print(' ', hex(addr), name)
```

If this is too slow, narrow to selected functions or use `bv.find_all_constant(...)` if appropriate for the binary and architecture.

## Scan MLIL or HLIL for Operations

```python
import binaryninja as bn
ops = {bn.MediumLevelILOperation.MLIL_CALL, bn.MediumLevelILOperation.MLIL_CALL_UNTYPED}
for f in bv.functions:
    mlil = f.mlil_if_available
    if not mlil:
        continue
    count = 0
    for insn in mlil.instructions:
        if insn.operation in ops:
            print(hex(insn.address), f.name, short_text(insn.tokens))
            count += 1
            if count >= 5:
                break
```

## Traverse Limited Call Graph

```python
start_name = 'main'
roots = list(bv.get_functions_by_name(start_name))
if not roots:
    print('missing root', start_name)
else:
    seen = set()
    frontier = [(roots[0], 0)]
    while frontier:
        f, depth = frontier.pop(0)
        if f.start in seen or depth > 2:
            continue
        seen.add(f.start)
        print('  ' * depth + f'{hex(f.start)} {f.name}')
        for callee in sorted(f.callees, key=lambda x: x.start)[:20]:
            frontier.append((callee, depth + 1))
```

## Check Sections and Segments

```python
print('segments')
for seg in bv.segments:
    perms = ''.join([
        'r' if seg.readable else '-',
        'w' if seg.writable else '-',
        'x' if seg.executable else '-',
    ])
    print(hex(seg.start), hex(seg.end), perms, 'len', seg.length)

print('sections')
for sec in bv.sections:
    print(sec.name, hex(sec.start), hex(sec.end), sec.semantics.name)
```

## Handle Large Results Safely

When the result may be large:

1. Count first.
2. Filter by name, address range, section, operation, or keyword.
3. Sort by relevance.
4. Print top-N with enough identifiers for follow-up.

Example:

```python
candidates = []
for f in bv.functions:
    score = len(list(f.basic_blocks)) + len(list(f.call_sites)) * 2
    if score >= 20:
        candidates.append((score, f))

for score, f in sorted(candidates, reverse=True, key=lambda x: x[0])[:25]:
    print(score, hex(f.start), f.name)
```

## State-Changing Workflows

If the user asks for a change, first confirm the exact target and action. After explicit permission, use the smallest scoped mutation possible and report what changed.

Example confirmation request:

```text
This will rename function 0x401000 from sub_401000 to parse_header in the current Binary Ninja session. Do you want me to proceed?
```

After permission, perform the change and print a concise confirmation. Do not combine unrelated mutations in one script unless the user approved the full batch.
