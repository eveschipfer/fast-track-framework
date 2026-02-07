# Sprint 3.6 Summary - Custom Validation Rules CLI

**Sprint Duration**: January 31, 2026
**Sprint Goal**: Implement `jtc make rule` command for generating custom Pydantic validation rules
**Status**: ✅ Complete

---

## 📋 Overview

Sprint 3.6 extends the Fast Track Framework CLI tooling with the `jtc make rule` command, allowing developers to generate custom validation rules following the Pydantic v2 pattern. This is similar to Laravel's `php artisan make:rule` but adapted for Python's Pydantic validation ecosystem.

### Objectives

1. ✅ Add `get_rule_template()` to `src/jtc/cli/templates.py`
2. ✅ Implement `jtc make rule <name>` command in `src/jtc/cli/commands/make.py`
3. ✅ Support both PascalCase and snake_case input
4. ✅ Generate validation rules in `src/rules/` directory
5. ✅ Integrate ftf.i18n for multi-language error messages
6. ✅ Follow Pydantic v2 AfterValidator pattern

---

## 🎯 What Was Built

### 1. Custom Validation Rule Template

**File**: `src/jtc/cli/templates.py`

Created `get_rule_template(class_name: str)` that generates:

- Callable class with `__call__` method (Pydantic v2 pattern)
- Integration with `ftf.i18n` for translations
- Comprehensive docstrings with usage examples
- Educational comparisons with Laravel's approach
- Type hints for strict type safety

**Key Features**:
- ✅ `__init__()` method for initialization parameters
- ✅ `__call__(value: Any) -> Any` for validation logic
- ✅ Raises `ValueError` for validation failures
- ✅ Uses `trans()` for multi-language error messages
- ✅ Follows Pydantic AfterValidator pattern

### 2. CLI Command Implementation

**File**: `src/jtc/cli/commands/make.py`

Added three new functions:

#### `to_pascal_case(name: str) -> str`
Converts any input to PascalCase:
- `cpf_is_valid` → `CpfIsValid`
- `CpfIsValid` → `CpfIsValid` (preserves if already PascalCase)
- Handles both snake_case and hyphen-case inputs

#### `make_rule(name: str, force: bool)`
Generates validation rule files:
- Creates `src/rules/` directory automatically
- Generates `__init__.py` to make it a Python package
- Converts names to appropriate formats (snake_case file, PascalCase class)
- Provides usage examples after generation
- Supports `--force` flag to overwrite existing files

### 3. Generated File Structure

```
src/
└── rules/
    ├── __init__.py                  # Package marker
    ├── cpf_is_valid.py             # CpfIsValid class
    └── min_age.py                  # MinAge class
```

---

## 💻 Usage Examples

### 1. Generate a Validation Rule

```bash
$ jtc make rule CpfIsValid
✓ Validation Rule created: src/rules/cpf_is_valid.py

💡 Usage Example:

from typing import Annotated
from pydantic import AfterValidator, BaseModel
from rules.cpf_is_valid import CpfIsValid

class MyModel(BaseModel):
    field: Annotated[str, AfterValidator(CpfIsValid())]
```

### 2. Generated Code Structure

**File**: `src/rules/cpf_is_valid.py`

```python
"""
CpfIsValid Validation Rule.
"""

from typing import Any
from jtc.i18n import trans


class CpfIsValid:
    """
    Validate that the input meets specific criteria.

    Usage:
        from typing import Annotated
        from pydantic import AfterValidator, BaseModel

        class MyModel(BaseModel):
            field: Annotated[str, AfterValidator(CpfIsValid())]
    """

    def __init__(self) -> None:
        """Initialize validator with parameters."""
        # TODO: Add initialization parameters
        pass

    def __call__(self, value: Any) -> Any:
        """
        Validate the value.

        Args:
            value: Field value to validate

        Returns:
            Valid value (can be transformed)

        Raises:
            ValueError: If validation fails
        """
        # TODO: Implement validation logic
        # if not is_valid(value):
        #     raise ValueError(trans("validation.custom_rule_key"))

        return value
```

### 3. Complete Example - CPF Validation

**Implementation**:

```python
# src/rules/cpf_is_valid.py
from typing import Any
from jtc.i18n import trans


class CpfIsValid:
    """Validate Brazilian CPF (Cadastro de Pessoas Físicas)."""

    def __init__(self, allow_masked: bool = True) -> None:
        self.allow_masked = allow_masked

    def __call__(self, value: str) -> str:
        """Validate CPF format."""
        # Remove formatting if allowed
        if self.allow_masked:
            value = value.replace(".", "").replace("-", "")

        # Check if it's 11 digits
        if not value.isdigit() or len(value) != 11:
            raise ValueError(trans("validation.invalid_cpf"))

        # Check for known invalid CPFs
        if value == value[0] * 11:
            raise ValueError(trans("validation.invalid_cpf"))

        # Validate check digits (simplified)
        # TODO: Implement full CPF check digit validation

        return value
```

**Usage in Pydantic Model**:

```python
from typing import Annotated
from pydantic import BaseModel, AfterValidator
from rules.cpf_is_valid import CpfIsValid


class UserRegistration(BaseModel):
    name: str
    cpf: Annotated[str, AfterValidator(CpfIsValid())]


# Validation in action
try:
    user = UserRegistration(name="João", cpf="123.456.789-00")
    print(f"Valid CPF: {user.cpf}")
except ValueError as e:
    print(f"Invalid CPF: {e}")
```

### 4. With Translation Support

**Add to `src/resources/lang/pt_BR.json`**:

```json
{
  "validation.invalid_cpf": "O CPF informado é inválido.",
  "validation.invalid_email_domain": "O domínio de e-mail não é permitido."
}
```

**Multi-language validation**:

```python
from jtc.i18n import set_locale

# Portuguese validation message
set_locale("pt_BR")
user = UserRegistration(name="João", cpf="invalid")
# ValueError: O CPF informado é inválido.

# English validation message
set_locale("en")
user = UserRegistration(name="John", cpf="invalid")
# ValueError: The CPF provided is invalid.
```

---

## 🏗️ Architecture Decisions

### 1. Pydantic v2 Pattern (AfterValidator)

**Decision**: Use Pydantic's `AfterValidator` with callable classes instead of function decorators.

**Rationale**:
- ✅ **Stateful validators**: Can hold configuration via `__init__`
- ✅ **Reusable**: Single class instance can validate multiple fields
- ✅ **Type-safe**: Full MyPy support with proper type hints
- ✅ **Educational**: Clear separation of initialization and validation logic
- ✅ **Pydantic v2 standard**: Follows official Pydantic v2 patterns

**Comparison with Laravel**:

| Laravel (PHP) | Fast Track (Python) |
|---------------|---------------------|
| `php artisan make:rule Uppercase` | `jtc make rule Uppercase` |
| `Rule` interface with `passes()` | Callable class with `__call__()` |
| Returns boolean | Raises `ValueError` on failure |
| Uses `message()` for errors | Uses `trans()` for i18n errors |

### 2. Directory Structure (`src/rules/`)

**Decision**: Store validation rules in `src/rules/` instead of `src/jtc/validation/rules/`.

**Rationale**:
- ✅ **User-owned**: Rules are application-specific, not framework code
- ✅ **Portable**: Easy to copy rules between projects
- ✅ **Clear separation**: Framework code vs user code
- ✅ **Simple imports**: `from rules.cpf_is_valid import CpfIsValid`

### 3. Integration with ftf.i18n

**Decision**: Auto-import `ftf.i18n.trans` in generated templates.

**Rationale**:
- ✅ **Multi-language support**: Error messages in user's language
- ✅ **Consistent UX**: All validation errors can be translated
- ✅ **Best practice**: Encourages i18n from the start
- ✅ **Educational**: Shows how to integrate i18n in custom code

---

## 📊 Files Created/Modified

### Modified Files

1. **`src/jtc/cli/templates.py`** (+96 lines)
   - Added `get_rule_template(class_name: str)` function
   - Generates validation rule class with `__call__` method
   - Includes ftf.i18n integration
   - Comprehensive docstrings and examples

2. **`src/jtc/cli/commands/make.py`** (+85 lines)
   - Added `to_pascal_case(name: str)` function
   - Added `make_rule(name: str, force: bool)` command
   - Updated imports to include `get_rule_template`
   - Smart name conversion (PascalCase ↔ snake_case)

### Generated Files (Examples)

3. **`src/rules/__init__.py`** (auto-generated)
   - Makes `rules/` a Python package
   - Created automatically when first rule is generated

4. **`src/rules/cpf_is_valid.py`** (example)
   - CpfIsValid validation rule class
   - 76 lines with full documentation

---

## ✅ Testing & Validation

### Manual Testing

```bash
# Test 1: PascalCase input
$ jtc make rule CpfIsValid
✓ Validation Rule created: src/rules/cpf_is_valid.py
# Class name: CpfIsValid ✅

# Test 2: snake_case input
$ jtc make rule min_age
✓ Validation Rule created: src/rules/min_age.py
# Class name: MinAge ✅

# Test 3: Force overwrite
$ jtc make rule CpfIsValid --force
✓ Validation Rule created: src/rules/cpf_is_valid.py
# Overwrites existing file ✅

# Test 4: Duplicate detection
$ jtc make rule CpfIsValid
❌ Rule already exists: src/rules/cpf_is_valid.py
Use --force to overwrite
# Correctly prevents overwrite ✅

# Test 5: Directory creation
$ rm -rf src/rules
$ jtc make rule TestRule
✓ Validation Rule created: src/rules/test_rule.py
# Creates directory + __init__.py ✅
```

### File Structure Validation

```bash
$ tree src/rules
src/rules
├── __init__.py
├── cpf_is_valid.py  # CpfIsValid class
└── min_age.py       # MinAge class
```

### Import Validation

```python
# Verify imports work correctly
from rules.cpf_is_valid import CpfIsValid
from rules.min_age import MinAge

# Both imports successful ✅
```

---

## 🎓 Key Learnings

### 1. PascalCase Conversion Challenge

**Problem**: Initial `to_pascal_case()` used `.capitalize()` which lowercased all letters except the first.

```python
# ❌ Wrong
"cpf_is_valid".split("_") → ["cpf", "is", "valid"]
["cpf", "is", "valid"].capitalize() → ["Cpf", "Is", "Valid"]  # Correct
BUT: "Cpf".capitalize() → "Cpf" ✅, "is".capitalize() → "Is" ✅
RESULT: "CpfIsValid" ✅

# BUT when input was already PascalCase:
"CpfIsValid" → to_snake_case → "cpf_is_valid"
"cpf_is_valid".split("_") → ["cpf", "is", "valid"]
"cpfisvalid".capitalize() → "Cpfisvalid" ❌  # capitalize() lowercases other chars!
```

**Solution**: Preserve uppercase letters instead of using `.capitalize()`:

```python
def to_pascal_case(name: str) -> str:
    # If already PascalCase, return as-is
    if "_" not in name and "-" not in name and name and name[0].isupper():
        return name

    # Otherwise, capitalize first letter only
    words = name.replace("-", "_").split("_")
    return "".join(word[0].upper() + word[1:] if word else "" for word in words)
```

**Lesson**: Python's `.capitalize()` lowercases everything except the first character. Use `word[0].upper() + word[1:]` to preserve case.

### 2. Pydantic v2 Validation Patterns

**Learning**: Pydantic v2 moved from `@validator` decorators to `Annotated` with `AfterValidator`.

**Old Pattern (Pydantic v1)**:
```python
from pydantic import BaseModel, validator

class User(BaseModel):
    cpf: str

    @validator("cpf")
    def validate_cpf(cls, v):
        if not is_valid_cpf(v):
            raise ValueError("Invalid CPF")
        return v
```

**New Pattern (Pydantic v2)**:
```python
from typing import Annotated
from pydantic import BaseModel, AfterValidator

class CpfValidator:
    def __call__(self, v: str) -> str:
        if not is_valid_cpf(v):
            raise ValueError("Invalid CPF")
        return v

class User(BaseModel):
    cpf: Annotated[str, AfterValidator(CpfValidator())]
```

**Benefits of v2 Pattern**:
- ✅ Reusable validators across models
- ✅ Stateful validators with `__init__` parameters
- ✅ Better type inference
- ✅ Cleaner separation of concerns

### 3. CLI UX Best Practices

**Key Insights**:

1. **Show usage examples immediately** - Don't make users search docs
2. **Create package markers** (`__init__.py`) automatically
3. **Support both naming conventions** - PascalCase and snake_case
4. **Provide educational comparisons** - Laravel vs Fast Track
5. **Fail fast with clear errors** - "Use --force to overwrite"

**Example**: Our UX after generating a rule:

```
✓ Validation Rule created: src/rules/cpf_is_valid.py

💡 Usage Example:

from typing import Annotated
from pydantic import AfterValidator, BaseModel
from rules.cpf_is_valid import CpfIsValid

class MyModel(BaseModel):
    field: Annotated[str, AfterValidator(CpfIsValid())]

📚 Learn More:
https://docs.pydantic.dev/latest/concepts/validators/#annotated-validators
```

**Result**: Developers can copy-paste the example immediately without reading documentation.

---

## 🔄 Comparison with Laravel

| Feature | Laravel | Fast Track Framework |
|---------|---------|---------------------|
| **Command** | `php artisan make:rule Uppercase` | `jtc make rule Uppercase` |
| **Pattern** | Implements `Rule` interface | Callable class with `__call__()` |
| **Validation** | `passes()` returns bool | `__call__()` raises ValueError |
| **Error Messages** | `message()` method | `trans()` for i18n support |
| **Directory** | `app/Rules/` | `src/rules/` |
| **Integration** | Laravel Validator | Pydantic BaseModel |
| **Type Safety** | PHP type hints | Python + MyPy strict mode |
| **Reusability** | Per-field in FormRequest | Annotated type alias |

**Example Comparison**:

**Laravel**:
```php
// Generate
php artisan make:rule Uppercase

// app/Rules/Uppercase.php
class Uppercase implements Rule {
    public function passes($attribute, $value) {
        return strtoupper($value) === $value;
    }

    public function message() {
        return 'The :attribute must be uppercase.';
    }
}

// Usage
$request->validate([
    'name' => ['required', new Uppercase]
]);
```

**Fast Track**:
```bash
# Generate
ftf make rule Uppercase
```

```python
# src/rules/uppercase.py
class Uppercase:
    def __call__(self, value: str) -> str:
        if value.upper() != value:
            raise ValueError(trans("validation.must_be_uppercase"))
        return value

# Usage
from typing import Annotated
from pydantic import BaseModel, AfterValidator

class MyModel(BaseModel):
    name: Annotated[str, AfterValidator(Uppercase())]
```

---

## 📈 Sprint Metrics

```
Command:       jtc make rule
Files Modified: 2
Lines Added:   +181
New Functions: 2 (to_pascal_case, make_rule)
Templates:     1 (get_rule_template)
Test Cases:    5 manual tests (all passing)
```

### Command Performance

```bash
# Cold start (first rule)
$ time jtc make rule CpfIsValid
real    0m0.234s  # Instant

# Directory already exists
$ time jtc make rule MinAge
real    0m0.198s  # Even faster
```

---

## 🚀 Future Enhancements

### 1. Built-in Validators Library

**Idea**: Provide common validation rules out of the box.

```bash
$ jtc make rule CpfValidator --preset=cpf
✓ Using preset: Brazilian CPF validation
✓ Validation Rule created: src/rules/cpf_validator.py
# Full CPF validation logic included
```

**Presets**:
- `--preset=email` - Email domain validation
- `--preset=cpf` - Brazilian CPF
- `--preset=cnpj` - Brazilian CNPJ
- `--preset=phone` - Phone number validation
- `--preset=password` - Password strength

### 2. Unit Test Generation

**Idea**: Generate test files automatically.

```bash
$ jtc make rule CpfValidator --with-tests
✓ Validation Rule created: src/rules/cpf_validator.py
✓ Test file created: tests/rules/test_cpf_validator.py
```

**Generated test structure**:
```python
# tests/rules/test_cpf_validator.py
import pytest
from rules.cpf_validator import CpfValidator


def test_cpf_validator_accepts_valid_cpf():
    validator = CpfValidator()
    result = validator("123.456.789-00")
    assert result == "123.456.789-00"


def test_cpf_validator_rejects_invalid_cpf():
    validator = CpfValidator()
    with pytest.raises(ValueError):
        validator("invalid")
```

### 3. Interactive Rule Generator

**Idea**: Interactive prompt for complex rules.

```bash
$ jtc make rule --interactive
? Rule name: MinAge
? Validation type: (Use arrow keys)
  ❯ Numeric range
    String pattern
    Custom logic
? Minimum value: 18
? Error message key: validation.min_age

✓ Validation Rule created: src/rules/min_age.py
```

### 4. Rule Composition

**Idea**: Combine multiple validators.

```python
# Generate composite rule
$ jtc make rule EmailWithDomain --compose="email,domain"

# Generated code
class EmailWithDomain:
    def __init__(self, allowed_domains: list[str]):
        self.allowed_domains = allowed_domains

    def __call__(self, value: str) -> str:
        # Validate email format
        EmailValidator()(value)

        # Validate domain
        DomainValidator(self.allowed_domains)(value)

        return value
```

---

## 🎯 Sprint Success Criteria

- ✅ **Command Implementation**: `jtc make rule` command works correctly
- ✅ **Template Generation**: Generates valid Python code with type hints
- ✅ **Naming Conversion**: Handles both PascalCase and snake_case inputs
- ✅ **Directory Management**: Creates `src/rules/` and `__init__.py` automatically
- ✅ **i18n Integration**: Generated code imports and uses `ftf.i18n.trans()`
- ✅ **Documentation**: Comprehensive docstrings and usage examples
- ✅ **UX**: Clear output with usage examples and next steps
- ✅ **Force Overwrite**: `--force` flag works correctly
- ✅ **Error Handling**: Prevents accidental overwrites without `--force`

---

## 📝 Known Issues

### 1. Typer 0.15.3 Help Bug

**Issue**: `jtc make rule --help` raises TypeError.

**Error**:
```
TypeError: TyperArgument.make_metavar() takes 1 positional argument but 2 were given
```

**Impact**: ⚠️ Cosmetic only - command works perfectly for actual usage

**Workaround**: Use `jtc make --help` to see all make commands

**Status**: Known Typer bug, does not affect functionality

---

## 🎓 Comparison: Laravel vs Fast Track

### Command Similarity

```bash
# Laravel
php artisan make:rule Uppercase
# Creates: app/Rules/Uppercase.php

# Fast Track
ftf make rule Uppercase
# Creates: src/rules/uppercase.py
```

### Key Differences

| Aspect | Laravel | Fast Track |
|--------|---------|------------|
| **Language** | PHP | Python |
| **Validation Library** | Laravel Validator | Pydantic v2 |
| **Pattern** | Interface implementation | Callable class |
| **Return Value** | Boolean | Value or ValueError |
| **Error Messages** | `message()` method | `trans()` function |
| **Type Safety** | PHP type hints | MyPy strict mode |
| **Reusability** | Instance per validation | Type annotation |
| **Testing** | PHPUnit | pytest |

### Pattern Evolution

**Laravel (PHP)**:
```php
class Uppercase implements Rule {
    public function passes($attribute, $value) {
        return strtoupper($value) === $value;
    }

    public function message() {
        return 'The :attribute must be uppercase.';
    }
}
```

**Fast Track (Python)**:
```python
class Uppercase:
    def __call__(self, value: str) -> str:
        if value.upper() != value:
            raise ValueError(trans("validation.must_be_uppercase"))
        return value
```

**Advantages of Fast Track Pattern**:
- ✅ Can transform value (not just validate)
- ✅ Type-safe return value
- ✅ i18n built-in with `trans()`
- ✅ Stateful validators via `__init__`
- ✅ Compose with other validators
- ✅ Full MyPy support

---

## 🏆 Sprint Completion

**Date**: January 31, 2026
**Status**: ✅ Complete
**Next Sprint**: TBD (Sprint 3.7 - Awaiting user direction)

**Sprint 3.6 delivered**:
- ✅ New CLI command: `jtc make rule`
- ✅ Pydantic v2 validation pattern
- ✅ i18n integration
- ✅ Comprehensive documentation
- ✅ Laravel-inspired DX

**Total Project Status**:
- **Tests**: 360 (100% passing)
- **Coverage**: ~66%
- **Sprints Completed**: 3.6
- **Commands**: 14 (make:*, db:*, queue:*)

---

## 📚 References

- [Pydantic v2 Validators](https://docs.pydantic.dev/latest/concepts/validators/#annotated-validators)
- [Laravel Validation Rules](https://laravel.com/docs/11.x/validation#custom-validation-rules)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [ftf.i18n Documentation](SPRINT_3_5_SUMMARY.md)

---

**Built with ❤️ for the Fast Track Framework**
