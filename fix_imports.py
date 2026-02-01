"""
Sprint 5.0 - Import Fixer

This script fixes import statements after the monorepo refactor.
It walks through workbench/ and updates imports from the old structure
to the new structure.

Changes:
- from ftf.models.* → from app.models.*
- from ftf.resources.user_resource → from app.resources.user_resource
- Framework imports (from ftf.core, ftf.http, etc.) stay the same

Usage:
    python fix_imports.py
"""

import re
from pathlib import Path
from typing import List, Tuple


# Import mapping rules
IMPORT_MAPPINGS = [
    # App-specific imports (models)
    (r"from ftf\.models\.(\w+)", r"from app.models.\1"),
    (r"from ftf\.models import", r"from app.models import"),

    # App-specific imports (resources - only specific resource files)
    (r"from ftf\.resources\.(\w+_resource)", r"from app.resources.\1"),

    # Note: Generic resource imports (JsonResource, ResourceCollection)
    # should stay as "from ftf.resources import"
]


def fix_imports_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """
    Fix imports in a single file.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple of (changes_count, changed_lines)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, []

    original_content = content
    changes = []

    # Apply each import mapping
    for old_pattern, new_pattern in IMPORT_MAPPINGS:
        matches = re.finditer(old_pattern, content)
        for match in matches:
            old_import = match.group(0)
            new_import = re.sub(old_pattern, new_pattern, old_import)
            changes.append(f"  {old_import} → {new_import}")

        content = re.sub(old_pattern, new_pattern, content)

    # Write back if changed
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return len(changes), changes
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return 0, []

    return 0, []


def fix_imports_in_directory(directory: Path) -> dict:
    """
    Fix imports in all Python files in a directory.

    Args:
        directory: Path to the directory

    Returns:
        Dict with statistics
    """
    stats = {
        "files_scanned": 0,
        "files_changed": 0,
        "total_changes": 0,
    }

    # Find all Python files
    python_files = list(directory.rglob("*.py"))

    print(f"\nScanning {len(python_files)} Python files in {directory}...")
    print("-" * 70)

    for file_path in python_files:
        stats["files_scanned"] += 1

        changes_count, changes = fix_imports_in_file(file_path)

        if changes_count > 0:
            stats["files_changed"] += 1
            stats["total_changes"] += changes_count

            # Print relative path
            rel_path = file_path.relative_to(directory.parent)
            print(f"\n✓ {rel_path}")
            for change in changes:
                print(change)

    return stats


def main():
    """Main entry point."""
    print("=" * 70)
    print("Sprint 5.0 - Import Fixer")
    print("Fixing import statements after monorepo refactor")
    print("=" * 70)

    # Check if workbench directory exists
    workbench_path = Path("workbench")
    if not workbench_path.exists():
        print("\n✗ Error: workbench/ directory not found")
        print("Run migrate.sh first!")
        return

    # Fix imports in workbench/app
    print("\n" + "=" * 70)
    print("Fixing imports in workbench/app/")
    print("=" * 70)

    app_path = workbench_path / "app"
    if app_path.exists():
        app_stats = fix_imports_in_directory(app_path)
    else:
        print("✗ workbench/app/ not found")
        app_stats = {"files_scanned": 0, "files_changed": 0, "total_changes": 0}

    # Fix imports in workbench/tests
    print("\n" + "=" * 70)
    print("Fixing imports in workbench/tests/")
    print("=" * 70)

    tests_path = workbench_path / "tests"
    if tests_path.exists():
        tests_stats = fix_imports_in_directory(tests_path)
    else:
        print("✗ workbench/tests/ not found")
        tests_stats = {"files_scanned": 0, "files_changed": 0, "total_changes": 0}

    # Fix imports in workbench/examples
    print("\n" + "=" * 70)
    print("Fixing imports in workbench/examples/")
    print("=" * 70)

    examples_path = workbench_path / "examples"
    if examples_path.exists():
        examples_stats = fix_imports_in_directory(examples_path)
    else:
        print("✗ workbench/examples/ not found")
        examples_stats = {"files_scanned": 0, "files_changed": 0, "total_changes": 0}

    # Print summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    total_scanned = (
        app_stats["files_scanned"] +
        tests_stats["files_scanned"] +
        examples_stats["files_scanned"]
    )
    total_changed = (
        app_stats["files_changed"] +
        tests_stats["files_changed"] +
        examples_stats["files_changed"]
    )
    total_changes = (
        app_stats["total_changes"] +
        tests_stats["total_changes"] +
        examples_stats["total_changes"]
    )

    print(f"\nworkbench/app/:")
    print(f"  Files scanned: {app_stats['files_scanned']}")
    print(f"  Files changed: {app_stats['files_changed']}")
    print(f"  Total changes: {app_stats['total_changes']}")

    print(f"\nworkbench/tests/:")
    print(f"  Files scanned: {tests_stats['files_scanned']}")
    print(f"  Files changed: {tests_stats['files_changed']}")
    print(f"  Total changes: {tests_stats['total_changes']}")

    print(f"\nworkbench/examples/:")
    print(f"  Files scanned: {examples_stats['files_scanned']}")
    print(f"  Files changed: {examples_stats['files_changed']}")
    print(f"  Total changes: {examples_stats['total_changes']}")

    print(f"\nTotal:")
    print(f"  Files scanned: {total_scanned}")
    print(f"  Files changed: {total_changed}")
    print(f"  Total changes: {total_changes}")

    print("\n" + "=" * 70)
    print("✓ Import fixing complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the changes above")
    print("2. Update pyproject.toml (see instructions)")
    print("3. Run: poetry install")
    print("4. Run: poetry run pytest workbench/tests/ -v")
    print("")


if __name__ == "__main__":
    main()
