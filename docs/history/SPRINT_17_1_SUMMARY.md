# Sprint 17.1 Summary: Fix CLI Make Commands

**Dates:** February 6, 2026
**Status:** ✅ Complete
**Tests:** 451 passing (100%), 7 skipped
**Coverage:** 48.68%

---

## 🎯 Sprint Goal

Fix failing CLI make commands (`workbench/tests/cli/test_make_commands.py`) that were broken during Sprint 17 global rebranding from `ftf` to `jtc`.

---

## 📋 Issues Fixed

### 1. **Controller Template Signature Error**

**Error:**
```
TypeError: get_controller_template() takes 1 positional argument but 2 were given
```

**Root Cause:**
The `make_controller` command in `framework/jtc/cli/commands/make.py` was calling the template function with two arguments:
```python
content = get_controller_template(name, resource_name)  # ❌ Wrong
```

But the template function `get_controller_template()` only accepts one parameter (`name`) and computes `resource_name` internally.

**Fix:**
```python
# framework/jtc/cli/commands/make.py:445
content = get_controller_template(name)  # ✅ Correct
```

**Impact:** Controller scaffolding now works correctly.

---

### 2. **Provider Template Undefined Variables**

**Error:**
```
NameError: name 'model_name' is not defined
```

**Root Cause:**
The `get_provider_template()` function in `framework/jtc/cli/templates.py` had copy-pasted comments from the resource template that referenced variables (`model_name`, `class_name`) that don't exist in the provider template's scope.

**Fix:**
Removed the invalid usage examples and replaced with generic, safe comments:
```python
# Before (lines 1876-1895):
# Usage Examples:
# ---------------
# @app.get("/api/{model_name.lower()}s/{{id}}")
# async def get_{model_name.lower()}(...)
#     return {class_name}.make({model_name.lower()}).resolve()

# After:
# Usage Examples:
# ---------------
# @app.get("/api/endpoint/{{id}}")
# async def get_endpoint(id: int, repo: MyRepository = Inject(MyRepository))
#     item = await repo.find_or_fail(id)
#     return item
```

**Impact:** Provider scaffolding now generates valid Python code without NameErrors.

---

### 3. **File Path Issues (Models & Repositories)**

**Error:**
```
AssertionError: assert False  (File not found)
```

**Root Cause:**
The `make:model` and `make:repository` commands were generating files in the wrong directories:
- Models: `src/jtc/models/` instead of `workbench/app/models/`
- Repositories: `src/jtc/repositories/` instead of `workbench/app/repositories/`

Tests expected files in the correct `workbench/` locations.

**Fix:**
```python
# framework/jtc/cli/commands/make.py

# make:model (line 174):
# Before: Path("src/jtc/models") / f"{filename}.py"
# After:  Path("workbench/app/models") / f"{filename}.py"

# make:repository (line 218):
# Before: Path("src/jtc/repositories") / f"{filename}.py"
# After:  Path("workbench/app/repositories") / f"{filename}.py"
```

**Impact:** Models and repositories now generate to the correct `workbench/` directories, matching test expectations.

---

### 4. **Remaining `ftf` References in Help Text**

**Root Cause:**
During Sprint 17 rebranding, some help text examples in `make.py` still referenced `ftf` instead of `jtc`.

**Fix:**
Updated all help messages to use the new brand:
```python
# framework/jtc/cli/commands/make.py

# Line 310 (resource help):
"Use --model to specify: jtc make:resource MyResource --model MyModel"

# Lines 866-867 (auth scaffolding):
"1. Create migration: [dim]jtc make migration create_users_table[/dim]"
"2. Run migration: [dim]jtc db migrate[/dim]"

# Line 881 (command help):
"This allows users to extend the jtc CLI with custom commands."

# Line 925 (command registration):
"Then run: [dim] jtc {name.lower()} --help"

# Line 1034 (rule help):
"jtc make:rule CpfIsValid"
```

**Impact:** All CLI help text now reflects the correct `jtc` branding.

---

## 📊 Test Results

### Before Sprint 17.1
```
FAILED  workbench/tests/cli/test_make_commands.py::test_make_model
FAILED  workbench/tests/cli/test_make_commands.py::test_make_repository
FAILED  workbench/tests/cli/test_make_commands.py::test_make_controller
FAILED  workbench/tests/cli/test_make_commands.py::test_make_provider
FAILED  workbench/tests/cli/test_make_commands.py::test_make_existing_file_fails_without_force
FAILED  workbench/tests/cli/test_make_commands.py::test_make_force_overwrites

6 failed, 445 passed, 7 skipped
```

### After Sprint 17.1
```
PASSED  workbench/tests/cli/test_make_commands.py::test_make_model
PASSED  workbench/tests/cli/test_make_commands.py::test_make_repository
PASSED  workbench/tests/cli/test_make_commands.py::test_make_controller
PASSED  workbench/tests/cli/test_make_commands.py::test_make_provider
PASSED  workbench/tests/cli/test_make_commands.py::test_make_existing_file_fails_without_force
PASSED  workbench/tests/cli/test_make_commands.py::test_make_force_overwrites

451 passed, 7 skipped, 7966 warnings in 75.84s
```

**Result:** ✅ **All CLI make commands working perfectly!**

---

## 📝 Files Modified

| File | Lines Changed | Description |
|-------|--------------|-------------|
| `framework/jtc/cli/commands/make.py` | 5 edits | Fixed file paths, template call signature, help text |
| `framework/jtc/cli/templates.py` | 1 edit | Fixed provider template comments |

---

## 🎓 Educational Notes

### Why Did These Bugs Occur?

These issues emerged during the **Sprint 17 global rebranding** (`ftf` → `jtc`) because:

1. **Template Signature Mismatch:** The controller template was refactored to compute `resource_name` internally, but the calling code wasn't updated to match.

2. **Copy-Paste Errors:** The provider template had copy-pasted usage examples from the resource template that referenced variables not available in the provider context.

3. **Path Inconsistency:** During early development, framework code was in `src/jtc/` (as suggested by the scaffolded paths), but the actual project structure uses `workbench/app/` for application code. The make commands needed to match the project structure.

### Key Learnings

1. **Template Function Design:** Template functions should be self-contained and compute any derived values internally rather than requiring callers to pass them.

2. **Code Review Matters:** Copy-pasting code between templates without verifying variable scope leads to runtime errors.

3. **Project Structure Awareness:** Scaffold generators must generate files in the correct project structure locations, not idealized locations.

4. **Comprehensive Brand Updates:** When renaming a framework, help text and examples must be updated everywhere, not just code.

---

## 🚀 Usage Examples

All make commands now work correctly:

```bash
# Generate a model
jtc make model User
# Creates: workbench/app/models/user.py

# Generate a repository
jtc make repository UserRepository
# Creates: workbench/app/repositories/user_repository.py

# Generate a controller
jtc make controller UserController
# Creates: workbench/http/controllers/user_controller.py

# Generate a service provider
jtc make provider PaymentServiceProvider
# Creates: workbench/app/providers/payment_service_provider.py

# Force overwrite
jtc make model User --force
# Overwrites existing: workbench/app/models/user.py
```

---

## ✅ Sprint 17.1 Checklist

- [x] Fix controller template signature error
- [x] Fix provider template undefined variables
- [x] Fix model file path
- [x] Fix repository file path
- [x] Update remaining ftf references in help text
- [x] All 6 CLI make command tests passing
- [x] Full test suite passing (451 tests)
- [x] Create sprint summary

---

## 📈 Impact

**Framework Stability:** High
All core scaffolding commands now work correctly, allowing developers to generate boilerplate code reliably.

**Developer Experience:** Improved
Developers can confidently use `jtc make:*` commands without encountering errors or generating files in wrong locations.

**Code Quality:** Maintained
All changes preserve type safety and follow existing code conventions.

---

## 🔮 Next Steps

No immediate follow-up work required. The CLI make commands are fully functional.

**Potential Future Enhancements:**
1. Add `jtc make:middleware` test coverage
2. Add `jtc make:job` test coverage
3. Add `jtc make:listener` test coverage
4. Auto-detect and use project root from current working directory

---

**Last Updated:** February 6, 2026
