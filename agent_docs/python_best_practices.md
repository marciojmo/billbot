# Google Best Practices for Python Development

This document summarizes Google's official Python style guide and best practices for writing clean, maintainable, and efficient Python code.

---

## Table of Contents

1. [Language Rules](#language-rules)
2. [Style Rules](#style-rules)
3. [Naming Conventions](#naming-conventions)
4. [Type Annotations](#type-annotations)
5. [Documentation](#documentation)
6. [Imports](#imports)
7. [Exceptions](#exceptions)
8. [Best Practices Summary](#best-practices-summary)

---

## Language Rules

### Lint Your Code

- Run `pylint` over your code using the Google pylint configuration
- Pylint catches common errors and enforces style consistency
- Suppress warnings only when necessary and document why

### Imports

- Use `import x` for importing packages and modules
- Use `from x import y` where `x` is the package prefix and `y` is the module name
- Use `from x import y as z` if two modules named `y` are being imported or if `y` is too long
- Use `import y as z` only when `z` is a standard abbreviation (e.g., `import numpy as np`)

**Do:**
```python
import os
import sys
from collections.abc import Mapping, Sequence
from typing import Any, NewType
```

**Don't:**
```python
from os import *  # Never use wildcard imports
```

### Packages

- Import each module using the full pathname location of the module
- Helps prevent module name conflicts

### Exceptions

- Exceptions are allowed but must be used carefully
- Raise exceptions like this: `raise MyError('Error message')` or `raise MyError()`
- Never use catch-all `except:` statements or catch `Exception` or `StandardError`
- Minimize the amount of code in a `try/except` block
- Use the `finally` clause to execute code whether or not an exception is raised

**Do:**
```python
try:
    value = collection[key]
except KeyError:
    return key_not_found(key)
else:
    return handle_value(value)
finally:
    cleanup()
```

### Global Variables

- Avoid global variables
- If needed, declare them at the module level by prepending an `_` to the name
- Constants should be named with `ALL_CAPS_WITH_UNDERSCORES`

### Nested/Local/Inner Classes and Functions

- Nested local functions or classes are fine when used to close over a local variable
- Inner classes and functions have benefits for encapsulation

### Comprehensions & Generator Expressions

- Okay to use for simple cases
- Each portion must fit on one line: mapping expression, `for` clause, filter expression
- Multiple `for` clauses or filter expressions are not permitted
- Use loops instead when things get more complicated

**Do:**
```python
result = [x**2 for x in range(10)]
result = {x: x**2 for x in range(10)}
```

**Don't:**
```python
result = [(x, y) for x in range(10) for y in range(5) if x * y > 10]  # Too complex
```

### Default Iterators and Operators

- Use default iterators and operators for types that support them (lists, dictionaries, files)
- They are simple and efficient

**Do:**
```python
for key in dictionary:
    ...
if key in dictionary:
    ...
for line in file:
    ...
```

### Generators

- Use generators as needed
- A function that returns an iterator is fine
- Use "Yields:" in the docstring instead of "Returns:"

### Lambda Functions

- Okay to use for one-liners
- If the code inside the lambda is longer than 60-80 chars, define it as a regular function

### Conditional Expressions

- Okay to use for simple cases
- Each portion must fit on one line: true-expression, if-expression, else-expression

**Do:**
```python
x = 1 if cond else 2
```

**Don't:**
```python
x = (really_long_true_expression
     if condition
     else really_long_false_expression)  # Use if/else instead
```

### Default Argument Values

- Okay to use with care
- **Never use mutable objects as default values**

**Do:**
```python
def foo(a, b=None):
    if b is None:
        b = []
```

**Don't:**
```python
def foo(a, b=[]):  # BAD - mutable default argument
    ...
```

### Properties

- Use properties for simple attribute access
- Properties should be used when simple accessors/mutators would be expected

### True/False Evaluations

- Use the implicit false if possible
- Python evaluates certain values as `False`: `0, None, [], {}, ''`

**Do:**
```python
if not users:
    print('No users')

if foo:
    process(foo)
```

**Don't:**
```python
if len(users) == 0:
    print('No users')

if foo is not None and foo != []:
    process(foo)
```

---

## Style Rules

### Line Length

- Maximum line length is **80 characters**
- Exceptions:
  - Long import statements
  - URLs, pathnames, or long flags in comments
  - Long string module level constants not containing whitespace

### Indentation

- Indent code blocks with **4 spaces**
- Never use tabs
- Implied line continuation should align wrapped elements vertically

```python
# Aligned with opening delimiter
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

# More indentation to distinguish this from the rest
def long_function_name(
        var_one, var_two, var_three,
        var_four):
    print(var_one)
```

### Blank Lines

- Two blank lines between top-level definitions (functions or class definitions)
- One blank line between method definitions inside a class
- Use single blank lines as you judge appropriate within functions or methods

### Whitespace

- Follow standard typographic rules for spaces around punctuation
- No whitespace inside parentheses, brackets, or braces
- No whitespace before a comma, semicolon, or colon
- Whitespace around binary operators (assignment, comparisons, Booleans)

**Do:**
```python
spam(ham[1], {'eggs': 2}, [])
x = 1
y = 2
long_variable = 3
```

**Don't:**
```python
spam( ham[ 1 ], { 'eggs': 2 }, [ ] )
x             = 1
y             = 2
long_variable = 3
```

### Shebang Line

- Most `.py` files do not need a shebang line
- Start the main file of a program with `#!/usr/bin/env python3`

### Comments

- Use the right style for the type of comment (module, function, inline)
- Be sure to use proper punctuation and complete sentences

### Strings

- Use `f-strings`, `%` operator, or `format` method for formatting strings
- Avoid using `+` for string concatenation in loops

**Do:**
```python
x = f'name: {name}; score: {score}'
```

### Files and Sockets

- Explicitly close files and sockets when done with them
- Use the `with` statement to manage files

**Do:**
```python
with open('file.txt', 'r') as f:
    content = f.read()
```

### TODO Comments

- Use `TODO` comments for code that is temporary, short-term, or good-enough but not perfect
- Format: `# TODO(username): description of what to do`

```python
# TODO(marcio): Use a more efficient data structure here
```

---

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Modules | `lower_with_underscores` | `my_module.py` |
| Packages | `lowercase` | `mypackage` |
| Classes | `CapWords` | `MyClass` |
| Exceptions | `CapWords` | `MyError` |
| Functions | `lower_with_underscores` | `my_function()` |
| Global/Class Constants | `CAPS_WITH_UNDERSCORES` | `MAX_SIZE` |
| Global/Class Variables | `lower_with_underscores` | `my_variable` |
| Instance Variables | `lower_with_underscores` | `self.my_var` |
| Method Names | `lower_with_underscores` | `my_method()` |
| Function/Method Parameters | `lower_with_underscores` | `my_param` |
| Local Variables | `lower_with_underscores` | `local_var` |

### Naming Guidelines

- **Single leading underscore (`_`)**: Internal use indicator (weak convention)
- **Single trailing underscore (`_`)**: Used to avoid conflicts with Python keywords
- **Double leading underscore (`__`)**: Triggers name mangling in class attributes
- **Double leading and trailing underscores (`__name__`)**: Reserved for Python special methods

**Do:**
```python
class MyClass:
    MAX_ITEMS = 100  # Class constant
    
    def __init__(self):
        self._internal_value = 0  # Internal use
        self.public_value = 1     # Public attribute
    
    def calculate_total(self, items_list):
        return sum(items_list)
```

---

## Type Annotations

### General Rules

- Use type annotations for function signatures
- Use the `typing` module for complex types
- Annotate all public APIs

```python
from typing import Optional, Sequence

def greeting(name: str) -> str:
    return f'Hello, {name}'

def process_items(items: Sequence[int]) -> Optional[int]:
    if items:
        return sum(items)
    return None
```

### Modern Type Annotations (Python 3.10+)

```python
def process(items: list[int]) -> int | None:
    if items:
        return sum(items)
    return None
```

### Type Annotation Best Practices

- Use `Any` sparingly and only when absolutely necessary
- Prefer `Sequence` over `list` for input parameters (more flexible)
- Use `Mapping` over `dict` for read-only dictionary parameters
- Use `Optional[X]` for values that could be `None`

---

## Documentation

### Docstrings

- All public modules, functions, classes, and methods should have docstrings
- Use Google-style docstrings

#### Module Docstring

```python
"""A one-line summary of the module or program, terminated by a period.

Leave one blank line. The rest of this docstring should contain an
overall description of the module or program. Optionally, it may also
contain a brief description of exported classes and functions and/or
usage examples.

Typical usage example:

    foo = ClassFoo()
    bar = foo.FunctionBar()
"""
```

#### Function Docstring

```python
def fetch_data(url: str, timeout: int = 30) -> dict:
    """Fetches data from the given URL.

    Retrieves JSON data from a remote API endpoint and returns it
    as a dictionary.

    Args:
        url: The URL to fetch data from.
        timeout: Optional timeout in seconds. Defaults to 30.

    Returns:
        A dict mapping keys to the corresponding data fetched.
        For example:

        {'name': 'John', 'age': 30}

    Raises:
        ConnectionError: If the connection to the server fails.
        TimeoutError: If the request times out.
    """
    ...
```

#### Class Docstring

```python
class SampleClass:
    """Summary of class here.

    Longer class information...

    Attributes:
        likes_spam: A boolean indicating if we like SPAM or not.
        eggs: An integer count of the eggs we have laid.
    """

    def __init__(self, likes_spam: bool = False):
        """Initializes the instance based on spam preference.

        Args:
            likes_spam: Defines if instance exhibits SPAM preference.
        """
        self.likes_spam = likes_spam
        self.eggs = 0
```

---

## Imports

### Import Order

Imports should be grouped in the following order with a blank line between each group:

1. **Future imports** (if any)
2. **Standard library imports**
3. **Related third-party imports**
4. **Local application/library specific imports**

Within each grouping, imports should be sorted lexicographically.

```python
from __future__ import annotations

import os
import sys
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from mypackage import mymodule
from mypackage.subpackage import another_module
```

### Import Best Practices

- Import only modules, not classes or functions directly (with some exceptions)
- Avoid circular imports by restructuring code or using local imports
- Never use relative imports; always use the full package path

---

## Exceptions

### Defining Exceptions

```python
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression: Input expression in which the error occurred.
        message: Explanation of the error.
    """

    def __init__(self, expression: str, message: str):
        self.expression = expression
        self.message = message
```

### Using Exceptions

```python
def divide(a: float, b: float) -> float:
    """Divides a by b.

    Args:
        a: The dividend.
        b: The divisor.

    Returns:
        The quotient of a divided by b.

    Raises:
        ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError('Cannot divide by zero')
    return a / b
```

---

## Best Practices Summary

### Do

✅ Use 4 spaces for indentation  
✅ Limit lines to 80 characters  
✅ Use descriptive variable and function names  
✅ Write docstrings for all public modules, functions, classes, and methods  
✅ Use type annotations  
✅ Use `with` statements for file operations  
✅ Use comprehensions for simple transformations  
✅ Use f-strings for string formatting  
✅ Run `pylint` on your code  
✅ Use `None` as the default for mutable arguments  
✅ Use meaningful exception types  
✅ Use implicit boolean evaluation  

### Don't

❌ Use tabs for indentation  
❌ Use wildcard imports (`from module import *`)  
❌ Use mutable objects as default argument values  
❌ Use bare `except:` clauses  
❌ Use single-letter variable names (except for counters)  
❌ Have too much code in a `try` block  
❌ Use global variables unnecessarily  
❌ Use complex comprehensions  
❌ Catch `Exception` without re-raising  
❌ Leave files/sockets open  

---

## References

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 – Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)

---

*Last updated: January 2026*

