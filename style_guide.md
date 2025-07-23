# GTK Signage Style Guide

This document outlines the coding style conventions for the GTK Signage project. Following these guidelines ensures consistent, readable, and maintainable code across the project.

## General Principles

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines for Python code
- Favor readability and clarity over terseness
- Be consistent with the existing codebase
- Use descriptive names for variables, functions, and classes

## Specific Guidelines

### Imports

Organize imports into three groups, separated by a blank line:
1. Standard library imports
2. Third-party library imports
3. Local application imports

Within each group, imports should be sorted alphabetically.

```python
# Good
import os
import sys
from datetime import datetime

import gi
from dotenv import load_dotenv
from flask import Flask, render_template

from signage.models import Slide
from signage.slidestore import SlideStore
```

### Naming Conventions

- Use `snake_case` for variables, functions, and methods
- Use `PascalCase` for class names
- Use `UPPER_CASE` for constants

```python
# Good
slide_index = 0
DEFAULT_PORT = 5000

def calculate_duration():
    pass

class SlideStore:
    pass
```

### Docstrings

Use triple-quoted docstrings for all modules, classes, and functions. Follow this format:

```python
"""
Brief one-line description.

More detailed description if needed.
"""

def function(arg1, arg2):
    """
    Brief description of function.
    
    Longer description if needed.
    
    Args:
        arg1 (type): Description of arg1.
        arg2 (type): Description of arg2.
        
    Returns:
        type: Description of return value.
        
    Raises:
        ExceptionType: When and why this exception is raised.
    """
```

### Indentation and Line Length

- Use 4 spaces for indentation (no tabs)
- Limit lines to 79-99 characters
- For long lines, break before operators and indent the continuation line

```python
# Good
long_variable = (value1 
                 + value2 
                 + value3)
```

### Comments

- Use comments sparingly and only when necessary to explain complex logic
- Keep comments up-to-date with code changes
- Use complete sentences with proper capitalization and punctuation

### Logging

Use the `logging` module instead of `print` statements for all output:

```python
# Bad
print(f"Showing slide: {current_slide.source}")

# Good
import logging
logging.info(f"Showing slide: {current_slide.source}")
```

### Exception Handling

- Be specific about which exceptions you catch
- Avoid bare `except:` clauses
- Include meaningful error messages

```python
# Bad
try:
    do_something()
except Exception:
    pass

# Good
try:
    do_something()
except ValueError as e:
    logging.error(f"Invalid value: {e}")
except IOError as e:
    logging.error(f"I/O error: {e}")
```

### Whitespace

- Surround operators with a single space
- No trailing whitespace at the end of lines
- Two blank lines before top-level class and function definitions
- One blank line before method definitions inside a class

### String Formatting

Prefer f-strings for string formatting:

```python
# Good
name = "World"
greeting = f"Hello, {name}!"
```

## Tools

Use these tools to help maintain code style:
- `flake8` for style checking
- `black` for automatic formatting
- `isort` for organizing imports

## Example

```python
"""
Module docstring with brief description.

More detailed description if needed.
"""
import os
from datetime import datetime

from third_party_lib import SomeClass

from local_module import local_function


def example_function(param1, param2=None):
    """
    Brief description of function.
    
    Args:
        param1 (str): Description of param1.
        param2 (int, optional): Description of param2. Defaults to None.
        
    Returns:
        bool: Description of return value.
    """
    if param2 is None:
        param2 = 0
        
    result = param1 + str(param2)
    return len(result) > 10
```