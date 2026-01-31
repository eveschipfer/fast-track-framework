"""
SQL Normalizer Utility

Normalizes SQL strings for robust contract testing by removing:
- Extra whitespace
- Newlines
- Inconsistent spacing around operators
- Case differences (optional)

This allows comparing SQL query structure without being sensitive to
formatting differences.

Usage:
    from tests.utils.sql_normalizer import normalize_sql

    expected = "SELECT users.id FROM users WHERE users.age >= :age_1"
    actual = query.to_sql()

    assert normalize_sql(actual) == normalize_sql(expected)

Educational Note:
    SQL contract tests verify the STRUCTURE of generated queries, not
    their execution. This catches regressions like:
    - Changed join types (INNER vs LEFT)
    - Missing WHERE clauses
    - Wrong ORDER BY direction
    - Accidental query modifications
"""

import re


def normalize_sql(sql: str) -> str:
    """
    Normalize SQL string for robust comparison.

    Removes extra whitespace, newlines, and normalizes spacing around
    operators and keywords. This makes SQL comparison resilient to
    formatting changes while still catching semantic differences.

    Args:
        sql: Raw SQL string (from to_sql() or hand-written)

    Returns:
        str: Normalized SQL string with consistent formatting

    Example:
        >>> query = '''
        ...     SELECT
        ...         users.id,
        ...         users.name
        ...     FROM users
        ...     WHERE users.age >= :age_1
        ...     ORDER BY users.created_at DESC
        ... '''
        >>> normalize_sql(query)
        'SELECT users.id, users.name FROM users WHERE users.age >= :age_1 ORDER BY users.created_at DESC'

    Contract Testing Pattern:
        >>> expected = "SELECT id FROM users WHERE age >= :age_1"
        >>> actual = user_repo.query().where(User.age >= 18).to_sql()
        >>> assert normalize_sql(actual) == normalize_sql(expected)
        # If this fails, the query structure changed unexpectedly!
    """
    # Remove leading/trailing whitespace
    sql = sql.strip()

    # Replace multiple spaces with single space
    sql = re.sub(r"\s+", " ", sql)

    # Normalize newlines to spaces
    sql = sql.replace("\n", " ").replace("\r", "")

    # Remove spaces around parentheses for consistency
    sql = re.sub(r"\s*\(\s*", "(", sql)
    sql = re.sub(r"\s*\)\s*", ")", sql)

    # Normalize spaces around commas (no space before, one space after)
    sql = re.sub(r"\s*,\s*", ", ", sql)

    # Remove extra spaces around operators (for cleaner comparison)
    # But keep spaces around comparison operators for readability
    sql = re.sub(r"\s*(=|!=|<>|<=|>=|<|>)\s*", r" \1 ", sql)

    # Final cleanup: remove duplicate spaces
    sql = re.sub(r"\s+", " ", sql)

    return sql.strip()


def normalize_sql_case_insensitive(sql: str) -> str:
    """
    Normalize SQL string and convert to uppercase for case-insensitive comparison.

    Use this when comparing SQL from different sources that may use
    different casing conventions (SELECT vs select).

    Args:
        sql: Raw SQL string

    Returns:
        str: Normalized SQL string in uppercase

    Example:
        >>> a = "select id from users"
        >>> b = "SELECT id FROM users"
        >>> normalize_sql_case_insensitive(a) == normalize_sql_case_insensitive(b)
        True

    Note:
        Be careful with this for case-sensitive identifiers (table/column names).
        Use normalize_sql() for most cases.
    """
    return normalize_sql(sql).upper()


def extract_query_type(sql: str) -> str:
    """
    Extract the query type (SELECT, INSERT, UPDATE, DELETE) from SQL.

    Useful for categorizing queries in tests or debugging.

    Args:
        sql: SQL string

    Returns:
        str: Query type in uppercase (SELECT, INSERT, UPDATE, DELETE, etc.)

    Example:
        >>> sql = "SELECT id FROM users WHERE age > 18"
        >>> extract_query_type(sql)
        'SELECT'
    """
    normalized = normalize_sql(sql)
    match = re.match(r"^(\w+)", normalized)
    return match.group(1).upper() if match else "UNKNOWN"


def count_clauses(sql: str) -> dict[str, int]:
    """
    Count occurrences of SQL clauses in a query.

    Useful for contract tests that verify query complexity.

    Args:
        sql: SQL string

    Returns:
        dict[str, int]: Count of each clause type

    Example:
        >>> sql = "SELECT id FROM users WHERE age > 18 AND status = 'active'"
        >>> counts = count_clauses(sql)
        >>> counts["WHERE"]
        1
        >>> counts["AND"]
        1
    """
    normalized = normalize_sql(sql).upper()

    clauses = {
        "SELECT": normalized.count("SELECT"),
        "FROM": normalized.count("FROM"),
        "WHERE": normalized.count("WHERE"),
        "JOIN": normalized.count("JOIN"),
        "LEFT JOIN": normalized.count("LEFT JOIN"),
        "INNER JOIN": normalized.count("INNER JOIN"),
        "ORDER BY": normalized.count("ORDER BY"),
        "GROUP BY": normalized.count("GROUP BY"),
        "HAVING": normalized.count("HAVING"),
        "LIMIT": normalized.count("LIMIT"),
        "OFFSET": normalized.count("OFFSET"),
        "AND": normalized.count(" AND "),  # Space-bounded to avoid substring matches
        "OR": normalized.count(" OR "),
    }

    return {k: v for k, v in clauses.items() if v > 0}


def is_parameterized(sql: str) -> bool:
    """
    Check if SQL query uses parameterized queries (has placeholders).

    Parameterized queries are safer against SQL injection.

    Args:
        sql: SQL string

    Returns:
        bool: True if query has parameters, False otherwise

    Example:
        >>> is_parameterized("SELECT * FROM users WHERE id = :id_1")
        True
        >>> is_parameterized("SELECT * FROM users")
        False
    """
    # Check for common parameter patterns
    # SQLAlchemy uses :param_name
    # Other libraries use ? or $1, etc.
    return bool(
        re.search(r":\w+|\?|\$\d+|%s", sql)
    )


def remove_parameters(sql: str) -> str:
    """
    Remove parameter placeholders from SQL for structural comparison.

    Use this when you want to compare query structure without caring
    about specific parameter names.

    Args:
        sql: SQL string with parameters

    Returns:
        str: SQL with parameters replaced by '?'

    Example:
        >>> sql = "SELECT * FROM users WHERE age >= :age_1 AND status = :status_1"
        >>> remove_parameters(sql)
        'SELECT * FROM users WHERE age >= ? AND status = ?'
    """
    normalized = normalize_sql(sql)

    # Replace SQLAlchemy-style parameters (:param_name)
    normalized = re.sub(r":\w+", "?", normalized)

    # Replace numbered placeholders ($1, $2)
    normalized = re.sub(r"\$\d+", "?", normalized)

    # %s placeholders already match '?'

    return normalized
