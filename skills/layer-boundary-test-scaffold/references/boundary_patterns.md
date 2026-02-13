# Boundary Patterns

## Import Ban (module prefix)

```python
def has_prefix(module_name: str, prefixes: tuple[str, ...]) -> bool:
    return any(module_name == p or module_name.startswith(f"{p}.") for p in prefixes)
```

Use with `ast.Import` + `ast.ImportFrom` to detect direct and nested module imports.

## TYPE_CHECKING Exception Gate

```python
def is_type_checking_guard(expr: ast.AST) -> bool:
    if isinstance(expr, ast.Name):
        return expr.id == "TYPE_CHECKING"
    if isinstance(expr, ast.Attribute):
        return isinstance(expr.value, ast.Name) and expr.value.id == "typing" and expr.attr == "TYPE_CHECKING"
    return False
```

Use when runtime imports are forbidden but typing-only imports are allowed.

## Violation Format

```python
violations.append(f"{rel_path}:{node.lineno} imports forbidden dependency")
```

Keep violation strings stable so CI logs remain grep-friendly.

## Test Granularity

- one rule family = one test function
- one assertion per test function
- include rule text in assertion message
