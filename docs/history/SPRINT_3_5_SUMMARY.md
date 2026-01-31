# Sprint 3.5: i18n System & CLI Extensibility

**Status**: ✅ Complete
**Date**: 2026-01-31
**Tests**: 26 new tests (100% passing)
**Coverage**: 96.83% (i18n/core.py), 100% (i18n/__init__.py)

## Overview

Sprint 3.5 implements a **lightweight internationalization (i18n) system** and **CLI extensibility**, enabling the framework to support multiple languages (critical for "Orça Já" Portuguese support) and allowing users to create custom CLI commands.

### Key Achievement

**Before Sprint 3.5:**
- No multi-language support
- Hardcoded English messages
- No way to customize validation messages per locale
- No user-extensible CLI

**After Sprint 3.5:**
- Full i18n support with JSON translation files
- Dot notation keys (`auth.failed`, `validation.required`)
- Placeholder replacement (`:field`, `:min`, `:max`)
- Hot-swappable locales
- User-extensible CLI (`make:command`)
- Easy translation file generation (`make:lang`)

## Motivation

The "Orça Já" application needs Portuguese feedback messages for:

1. **Validation errors** — "O campo Email é obrigatório"
2. **Auth messages** — "Essas credenciais não correspondem"
3. **HTTP errors** — "Recurso não encontrado"
4. **Success messages** — "Sucesso!"

Additionally, users need to extend the `ftf` CLI with project-specific commands like deployment scripts, database maintenance, and custom tooling.

## What We Built

### 1. Translator Engine (`src/ftf/i18n/core.py`)

**Architecture:**

```python
Translator (Singleton)
├── _load_translations()
│   ├── Framework translations (src/ftf/resources/lang/{locale}.json)
│   └── User translations (src/resources/lang/{locale}.json)
├── get(key, **kwargs) → str
├── set_locale(locale)
├── has(key) → bool
└── all() → dict
```

**Key Features:**

1. **Singleton Pattern**
   - Single global instance across application
   - Consistent state for all translations
   - Efficient memory usage (translations loaded once)

2. **Cascade Loading**
   - Framework provides defaults
   - User overrides or extends
   - Similar to Laravel's vendor/app translations

3. **Dot Notation Keys**
   - Hierarchical organization (`auth.failed`, `validation.required`)
   - Easy to maintain and understand
   - Prevents key collisions

4. **Placeholder Replacement**
   - `:field`, `:min`, `:max` syntax
   - Simple string replacement
   - Type-safe (converts numbers to strings)

5. **Locale Switching**
   - Hot-swap at runtime
   - Useful for middleware (Accept-Language header)
   - Reloads translations automatically

6. **Graceful Fallbacks**
   - Returns key if translation not found
   - Fallback to default locale
   - Never crashes on missing files

**Example Usage:**

```python
from ftf.i18n import trans, set_locale

# English (default)
message = trans('auth.failed')
# "These credentials do not match our records."

# With placeholders
message = trans('validation.required', field='Email')
# "The Email field is required."

# Switch to Portuguese
set_locale('pt_BR')
message = trans('auth.failed')
# "Essas credenciais não correspondem aos nossos registros."

# Portuguese with placeholders
message = trans('validation.required', field='Email')
# "O campo Email é obrigatório."
```

### 2. Helper Functions (`src/ftf/i18n/__init__.py`)

**Public API:**

```python
trans(key, **kwargs)  # Main translation function
t(key, **kwargs)      # Alias for trans() (shorter)
set_locale(locale)    # Change language
has(key)              # Check if key exists
all_translations()    # Get all loaded translations
```

**Why Helper Functions?**

- Clean, Pythonic syntax
- No need to import Translator class
- Global state management
- Laravel-inspired API

**Comparison:**

| Framework | Translation Function |
|-----------|---------------------|
| Laravel | `__('auth.failed')` |
| Rails | `t('auth.failed')` |
| Django | `_('auth.failed')` (gettext) |
| **Fast Track** | `trans('auth.failed')` or `t('auth.failed')` |

### 3. Default Translation Files

**Framework Translations:**

```
src/ftf/resources/lang/
├── en.json      # English (55 keys)
└── pt_BR.json   # Portuguese Brazil (55 keys)
```

**Translation Categories:**

1. **Authentication** — `auth.*`
   - Failed login
   - Password reset
   - Token errors

2. **Validation** — `validation.*`
   - Required fields
   - Email format
   - Min/max lengths
   - Unique/exists checks

3. **HTTP** — `http.*`
   - 404 Not Found
   - 401 Unauthorized
   - 403 Forbidden
   - 422 Unprocessable Entity

4. **Database** — `database.*`
   - Connection errors
   - Record not found

5. **Queue** — `queue.*`
   - Job dispatched
   - Worker started/stopped

6. **CLI** — `cli.*`
   - File created
   - Command not found

7. **Common** — `common.*`
   - Success/Error
   - Save/Cancel/Delete

**Example Translation File (en.json):**

```json
{
  "auth.failed": "These credentials do not match our records.",
  "auth.throttle": "Too many login attempts. Please try again in :seconds seconds.",

  "validation.required": "The :field field is required.",
  "validation.min": "The :field must be at least :min characters.",

  "http.not_found": "Resource not found.",
  "http.unauthorized": "Unauthorized.",

  "common.success": "Success!",
  "common.error": "An error occurred."
}
```

### 4. CLI Commands

**`make:command` - Generate Custom CLI Command:**

```bash
$ ftf make:command deploy
✓ Command created: src/ftf/cli/commands/deploy.py

⚠️  Manual Registration Required:
Add this command to src/ftf/cli/main.py:

from ftf.cli.commands.deploy import app as deploy_app
app.add_typer(deploy_app, name='deploy')

Then run: ftf deploy --help
```

**Generated Template:**

```python
import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command()
def main(
    option: str = typer.Option(None, "--option", "-o"),
    flag: bool = typer.Option(False, "--flag", "-f"),
) -> None:
    """Command description."""
    console.print("[bold cyan]Running command...[/bold cyan]")

    # TODO: Implement your command logic
    console.print("[green]✓ Command completed![/green]")
```

**`make:lang` - Generate Translation File:**

```bash
$ ftf make:lang pt_BR
✓ Translation file created: src/resources/lang/pt_BR.json

💡 Next Steps:
1. Edit translation keys in the JSON file
2. Use translations in your code:

from ftf.i18n import trans, set_locale
set_locale('pt_BR')
message = trans('auth.failed')

Set default locale:
export DEFAULT_LOCALE='pt_BR'
```

**Generated Skeleton:**

```json
{
  "auth.failed": "These credentials do not match our records.",
  "validation.required": "The :field field is required.",
  "http.not_found": "Resource not found.",
  "common.success": "Success!"
}
```

## Implementation Details

### Singleton Pattern

**Why Singleton?**

1. **Single Source of Truth** — One locale across app
2. **Memory Efficient** — Translations loaded once
3. **Global Access** — No dependency injection needed
4. **Simple API** — Just call `trans()`

**Implementation:**

```python
class Translator:
    _instance = None

    @classmethod
    def get_instance(cls, locale=None):
        if cls._instance is None:
            cls._instance = cls(locale or os.getenv('DEFAULT_LOCALE', 'en'))
        elif locale and locale != cls._instance.locale:
            cls._instance.set_locale(locale)
        return cls._instance
```

**Thread Safety:**

- Python's GIL (Global Interpreter Lock) makes this thread-safe
- Each async task has its own context
- No race conditions in typical FastAPI usage

### Translation Loading Strategy

**Cascade Order:**

1. Load framework translations (defaults)
2. Load user translations (overrides)
3. Merge (user overrides framework)

**Example:**

```python
# Framework (src/ftf/resources/lang/en.json)
{"auth.failed": "Invalid credentials"}

# User (src/resources/lang/en.json)
{"auth.failed": "Wrong password!", "auth.custom": "Custom message"}

# Result:
{"auth.failed": "Wrong password!", "auth.custom": "Custom message"}
```

**Fallback Chain:**

```
1. Current locale translation
   ↓ (if not found)
2. Fallback locale (en) translation
   ↓ (if not found)
3. Return key itself
```

### Placeholder Replacement

**Simple String Replacement:**

```python
def _replace_placeholders(text, **kwargs):
    for key, value in kwargs.items():
        text = text.replace(f":{key}", str(value))
    return text
```

**Why not f-strings or .format()?**

- Translation files are JSON (static)
- Placeholders need custom syntax (`:field`)
- Simple replace is fast and predictable

**Type Conversion:**

```python
trans('auth.throttle', seconds=60)
# Converts 60 (int) to "60" (str) automatically
```

### Locale Detection (Future)

**Middleware Pattern:**

```python
from ftf.i18n import set_locale

async def locale_middleware(request, call_next):
    # Detect from Accept-Language header
    locale = request.headers.get('Accept-Language', 'en').split(',')[0]
    set_locale(locale)

    response = await call_next(request)
    return response

app.add_middleware(locale_middleware)
```

**User Preference (Future):**

```python
# Store locale in database
user = await get_current_user()
set_locale(user.locale)
```

## Test Coverage

**File**: `tests/unit/test_i18n.py`
**Total Tests**: 26 (100% passing)
**Coverage**:
- `i18n/core.py`: 96.83% (63 statements, 2 missed)
- `i18n/__init__.py`: 100% (17 statements, 0 missed)

### Test Categories

**Translator Tests (11 tests):**
- Singleton pattern verification
- Framework translations loading
- Key lookup (found and not found)
- Single and multiple placeholder replacement
- Locale switching
- `has()` method (exists and missing)
- `all()` method returns all translations
- Missing locale file handling

**Helper Function Tests (6 tests):**
- `trans()` basic usage
- `trans()` with placeholders
- `t()` alias works same as `trans()`
- `set_locale()` changes language
- `has()` checks key existence
- `all_translations()` returns dict

**User Override Tests (1 test):**
- User translations override framework defaults

**Edge Cases (4 tests):**
- Numeric placeholder values
- Missing placeholders remain in text
- Empty placeholder values
- Special characters (Portuguese ç, ã, etc.)

**Locale Tests (2 tests):**
- Portuguese translations loaded
- Fallback to English when translation missing

**Integration Tests (2 tests):**
- Complete workflow (load, switch, translate)
- Multiple locale switches

### Sample Test

```python
def test_translator_replaces_multiple_placeholders() -> None:
    """Test that multiple placeholders are replaced."""
    translator = Translator.get_instance(locale="en")

    message = translator.get("validation.min", field="Password", min=8)

    assert message == "The Password must be at least 8 characters."
```

## Comparison with Laravel

### Translation Files

**Laravel (resources/lang/en/auth.php):**

```php
<?php
return [
    'failed' => 'These credentials do not match our records.',
    'throttle' => 'Too many login attempts. Please try again in :seconds seconds.',
];
```

**Fast Track (resources/lang/en.json):**

```json
{
    "auth.failed": "These credentials do not match our records.",
    "auth.throttle": "Too many login attempts. Please try again in :seconds seconds."
}
```

**Key Differences:**

| Aspect | Laravel | Fast Track |
|--------|---------|------------|
| **Format** | PHP arrays | JSON |
| **Keys** | Nested arrays | Dot notation |
| **Loading** | Per-file (auth.php) | Single JSON file |
| **Syntax** | PHP | JSON (portable) |
| **Organization** | Multiple files | Single file per locale |

### Translation Usage

**Laravel:**

```php
// Basic
__('auth.failed')
trans('auth.failed')

// With placeholders
__('validation.min', ['field' => 'Password', 'min' => 8])

// Change locale
App::setLocale('pt_BR')

// Check existence
Lang::has('auth.failed')
```

**Fast Track:**

```python
# Basic
trans('auth.failed')
t('auth.failed')  # Alias

# With placeholders
trans('validation.min', field='Password', min=8)

# Change locale
set_locale('pt_BR')

# Check existence
has('auth.failed')
```

### CLI Commands

**Laravel (php artisan make:command):**

```bash
$ php artisan make:command DeployCommand
✓ Command created successfully.

# Auto-registered via namespace discovery
$ php artisan deploy
```

**Fast Track (ftf make:command):**

```bash
$ ftf make:command deploy
✓ Command created: src/ftf/cli/commands/deploy.py

⚠️  Manual registration required in src/ftf/cli/main.py
$ ftf deploy  # After manual registration
```

**Key Difference:**

- Laravel: Auto-discovery via namespaces
- Fast Track: Manual registration (for now)

## Educational Value

### What We Learned

1. **Singleton Pattern**
   - When to use (global state, single instance)
   - Thread safety in Python (GIL)
   - Class variables for instance storage

2. **i18n Best Practices**
   - Dot notation for hierarchical keys
   - Placeholder syntax (`:name` vs `{name}`)
   - Fallback strategies
   - Cascade loading (framework + user)

3. **JSON vs Code**
   - JSON for translations (portable, non-executable)
   - PHP arrays in Laravel (executable, more flexible)
   - Trade-offs: portability vs power

4. **CLI Extensibility**
   - Command templates
   - Auto-discovery vs manual registration
   - Trade-offs: simplicity vs convenience

5. **Graceful Degradation**
   - Return key if translation missing (better than crash)
   - Fallback to default locale
   - Handle missing files silently

### Common Patterns

**Pattern 1: Validation Messages**

```python
from ftf.i18n import trans

# In FormRequest.rules()
if not email:
    self.stop(trans('validation.required', field='Email'))

if len(password) < 8:
    self.stop(trans('validation.min', field='Password', min=8))
```

**Pattern 2: HTTP Exceptions**

```python
from ftf.http import AppException
from ftf.i18n import trans

class RecordNotFoundTranslated(AppException):
    def __init__(self, model: str, id: int):
        message = trans('database.record_not_found', model=model, identifier=id)
        super().__init__(message, status_code=404)
```

**Pattern 3: Locale Middleware**

```python
from ftf.i18n import set_locale

async def locale_middleware(request, call_next):
    # Detect from header or user preference
    locale = request.headers.get('Accept-Language', 'en').split(',')[0].split('-')[0]
    set_locale(locale if locale in ['en', 'pt', 'es'] else 'en')

    response = await call_next(request)
    return response
```

**Pattern 4: User Preference**

```python
from ftf.auth import CurrentUser
from ftf.i18n import set_locale, trans

@app.get("/profile")
async def profile(user: CurrentUser):
    # Set locale from user preference
    set_locale(user.locale or 'en')

    return {
        "message": trans('common.success'),
        "user": user
    }
```

## Files Created/Modified

### New Files

1. **`src/ftf/i18n/core.py` (459 lines)**
   - Translator class (singleton)
   - Translation loading (cascade)
   - Placeholder replacement
   - Locale switching

2. **`src/ftf/i18n/__init__.py` (202 lines)**
   - Public API: `trans()`, `t()`, `set_locale()`, `has()`, `all_translations()`
   - Helper functions wrapping Translator singleton

3. **`src/ftf/resources/lang/en.json` (55 keys)**
   - English translations (framework defaults)

4. **`src/ftf/resources/lang/pt_BR.json` (55 keys)**
   - Portuguese (Brazil) translations (for "Orça Já")

5. **`tests/unit/test_i18n.py` (377 lines)**
   - 26 comprehensive tests
   - 100% passing, 96.83% coverage

### Modified Files

1. **`src/ftf/cli/commands/make.py` (+125 lines)**
   - `make:command` — Generate custom CLI command
   - `make:lang` — Generate translation file

2. **`src/ftf/cli/templates.py` (+79 lines)**
   - `get_command_template()` — CLI command template
   - `get_lang_template()` — Translation JSON skeleton

## Architecture Decisions

### Decision 1: JSON vs PHP Arrays (Laravel)

**Why JSON?**

- ✅ Language-agnostic (portable)
- ✅ Non-executable (safer)
- ✅ Easy to edit (any text editor)
- ✅ Easy to version control (clean diffs)

**Trade-off:**
- ❌ No code in translations (Laravel allows `trans_choice()` with logic)
- ❌ No pluralization support (yet)

**Alternative:** YAML, TOML
- Rejected: JSON is simpler and more universally supported

### Decision 2: Dot Notation vs Nested Dicts

**Why Dot Notation in JSON?**

```json
// Dot notation (chosen)
{"validation.required": "Field required"}

// vs Nested (rejected)
{"validation": {"required": "Field required"}}
```

- ✅ Simpler JSON structure
- ✅ Keys are self-documenting
- ✅ No deep nesting complexity

**Trade-off:**
- ❌ Can't organize by file (all in one JSON)
- Solution: Group keys by prefix (`auth.*`, `validation.*`)

### Decision 3: Singleton vs Dependency Injection

**Why Singleton?**

- ✅ Simpler API (`trans()` vs injecting Translator)
- ✅ Global state makes sense for locale
- ✅ Laravel uses global helpers too

**Trade-off:**
- ❌ Global state (but acceptable for i18n)
- ❌ Harder to test with different locales in parallel
- Solution: Reset locale in test fixtures

### Decision 4: Manual Command Registration

**Why Manual Registration?**

- ✅ Simpler implementation (no auto-discovery)
- ✅ Explicit (clear what's registered)
- ✅ No magic

**Trade-off:**
- ❌ Extra step for users
- ❌ Easy to forget to register

**Future:** Add auto-discovery via entry points or module scanning

## Known Limitations

### 1. No Pluralization

**Issue**: Can't handle singular/plural forms automatically.

**Workaround:**

```python
# Manual pluralization
count = 5
if count == 1:
    message = trans('item.singular', count=count)
else:
    message = trans('item.plural', count=count)
```

**Future**: Add `trans_choice()` function in Sprint 4.x

### 2. No Nested Parameters

**Issue**: Can't nest placeholders or use complex logic.

**Example (not supported):**

```json
{
    "user.welcome": "Hello :user.name"  // Can't access nested properties
}
```

**Workaround:**

```python
trans('user.welcome', user_name=user.name)  // Flatten parameters
```

### 3. Manual Command Registration

**Issue**: Users must manually register commands in `main.py`.

**Future**: Implement auto-discovery via:
- Module scanning (`ftf.cli.commands.*`)
- Entry points (`setup.py`)

### 4. No Language Auto-Detection

**Issue**: Doesn't automatically detect user language from browser.

**Workaround:** Implement middleware:

```python
from ftf.i18n import set_locale

async def locale_middleware(request, call_next):
    locale = request.headers.get('Accept-Language', 'en').split(',')[0]
    set_locale(locale)
    response = await call_next(request)
    return response
```

## Production Checklist

Before deploying with i18n:

- [ ] Set `DEFAULT_LOCALE` environment variable
- [ ] Create user translations in `src/resources/lang/{locale}.json`
- [ ] Override framework translations as needed
- [ ] Test all placeholder replacements
- [ ] Verify special characters (ç, ã, ñ, etc.)
- [ ] Implement locale detection middleware (if needed)
- [ ] Document available locales for users
- [ ] Test missing translation fallback behavior

## Next Steps (Future Sprints)

1. **Pluralization Support** (Sprint 4.x)
   - `trans_choice('item.count', count)` function
   - Plural rules per locale (en: 1/other, pt: 1/other, etc.)

2. **Locale Auto-Detection** (Sprint 4.x)
   - Middleware for Accept-Language header
   - User preference from database
   - Cookie-based locale persistence

3. **Translation Management** (Sprint 4.x)
   - CLI command to extract translatable strings
   - Missing translation detection
   - Translation coverage reports

4. **Date/Number Formatting** (Sprint 4.x)
   - Locale-specific date formats
   - Number formatting (1,000 vs 1.000)
   - Currency formatting

5. **CLI Auto-Discovery** (Sprint 4.x)
   - Automatic command registration
   - Entry points support
   - No manual registration needed

## Conclusion

Sprint 3.5 successfully implemented a **lightweight yet powerful i18n system** and **CLI extensibility**, enabling:

✅ **Multi-Language Support** (JSON-based, dot notation, placeholders)
✅ **Hot-Swappable Locales** (`set_locale()` at runtime)
✅ **Framework + User Translations** (cascade loading)
✅ **Portuguese Support** (55 pre-translated keys for "Orça Já")
✅ **Custom CLI Commands** (`make:command` scaffolding)
✅ **Translation File Generation** (`make:lang` with skeleton)
✅ **26 Comprehensive Tests** (100% passing, 96.83% coverage)

**Key Achievement**: The framework now supports Portuguese (and any other language), making it suitable for international applications like "Orça Já" while maintaining a clean, Laravel-inspired API.

**Developer Experience**:
- Simple: `trans('auth.failed')` just works
- Powerful: Placeholders, fallbacks, locale switching
- Extensible: Users can override any translation
- Familiar: Laravel developers feel at home

---

**Total Test Count**: 360 tests (335 passing + 26 from Sprint 3.5, 7 bcrypt failures)
**Overall Coverage**: 63.92%
**Sprint Status**: ✅ **COMPLETE**
