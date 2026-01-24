# Contributing to Fast Track Framework

First off, thanks for taking the time to contribute! 🎉

This is an educational project, and contributions help make it a better learning resource for everyone.

## 🎯 Types of Contributions

### 1. **Bug Reports**
- Use GitHub Issues with the `bug` label
- Include Python version, OS, and steps to reproduce
- Provide minimal code example if possible

### 2. **Feature Requests**
- Use GitHub Issues with the `enhancement` label
- Explain the use case and expected behavior
- Bonus: Include a design proposal or code sketch

### 3. **Code Contributions**
- Bug fixes
- New features (discuss in issue first)
- Performance improvements
- Documentation improvements

### 4. **Educational Content**
- Tutorial blog posts
- Video walkthroughs
- Example projects
- Architecture decision records (ADRs)

## 🚀 Getting Started

### Development Setup

```bash
# Fork the repo on GitHub, then clone your fork
git clone https://github.com/eveschipfer/fast-track-framework.git
cd fast-track-framework

# Add upstream remote
git remote add upstream https://github.com/eveschipfer/fast-track-framework.git

# Install dependencies
poetry install

# Install pre-commit hooks
pre-commit install

# Create a branch
git checkout -b feature/your-feature-name
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov --cov-report=html

# Run specific test file
pytest tests/unit/test_container.py -v

# Run only fast tests (skip slow integration tests)
pytest -m "not slow" -v
```

### Code Quality Checks

```bash
# Type checking
mypy src/ --strict

# Formatting
black src/ tests/

# Linting
ruff check src/ tests/ --fix

# Run all pre-commit hooks
pre-commit run --all-files
```

## 📝 Code Standards

### Type Hints

**Required** on all functions, methods, and class attributes:

```python
# ✅ Good
async def get_user(user_id: int, db: AsyncSession) -> User:
    return await db.get(User, user_id)

# ❌ Bad
async def get_user(user_id, db):
    return await db.get(User, user_id)
```

### Docstrings

Use Google-style docstrings for public APIs:

```python
async def create_user(name: str, email: str, db: AsyncSession) -> User:
    """
    Create a new user in the database.
    
    Args:
        name: The user's full name
        email: The user's email address
        db: Async database session
        
    Returns:
        The created User instance
        
    Raises:
        ValueError: If email is invalid
        IntegrityError: If email already exists
        
    Example:
        >>> user = await create_user("John Doe", "john@example.com", db)
        >>> print(user.name)
        'John Doe'
    """
    # Implementation
```

### Testing

- **Coverage**: Maintain >80% coverage
- **Naming**: `test_<function>_<scenario>_<expected_result>`
- **Structure**: Follow AAA pattern (Arrange, Act, Assert)

```python
async def test_container_resolve_singleton_returns_same_instance():
    """Test that singleton scope returns same instance across resolves"""
    # Arrange
    container = Container()
    container.register(Database, singleton=True)
    
    # Act
    db1 = container.resolve(Database)
    db2 = container.resolve(Database)
    
    # Assert
    assert db1 is db2
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding tests
- `refactor`: Code change that neither fixes bug nor adds feature
- `perf`: Performance improvement
- `chore`: Changes to build process or tools

**Examples:**
```
feat(orm): add support for eager loading relationships

Implements .with_() method on query builder to allow
eager loading of related models, reducing N+1 queries.

Closes #42
```

```
fix(container): prevent circular dependency infinite loop

Added resolution stack tracking to detect and raise
CircularDependencyError before stack overflow.

Fixes #38
```

## 🔄 Pull Request Process

### 1. Before Opening PR

- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] Type checking passes (`mypy src/ --strict`)
- [ ] Code is formatted (`black src/ tests/`)
- [ ] Linter passes (`ruff check src/ tests/`)
- [ ] Pre-commit hooks pass
- [ ] Branch is up to date with `develop`

### 2. PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran to verify your changes.

## Checklist
- [ ] My code follows the code style of this project
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing unit tests pass locally
- [ ] I have added necessary documentation
- [ ] My changes generate no new warnings
```

### 3. Review Process

- At least 1 approval required
- All CI checks must pass
- No unresolved conversations
- Branch must be up to date

### 4. After Merge

- Delete your branch
- Pull latest `develop` locally
- Update any related issues

## 🎓 Learning-Focused Guidelines

Since this is an educational project:

### Documentation Philosophy

1. **Explain WHY, not just WHAT**
   ```python
   # ❌ Bad comment
   # Set singleton to True
   container.register(Database, singleton=True)
   
   # ✅ Good comment
   # Database must be singleton to prevent connection pool exhaustion.
   # Multiple instances would create separate pools, breaking connection limits.
   container.register(Database, singleton=True)
   ```

2. **Link to learning resources**
   ```python
   # Uses Python's descriptor protocol for lazy loading
   # Learn more: https://docs.python.org/3/howto/descriptor.html
   def __get__(self, obj, objtype=None):
       # Implementation
   ```

3. **Document design decisions**
   - Create ADRs (Architecture Decision Records) for major choices
   - Explain trade-offs between alternatives
   - Link to relevant GitHub discussions

### Code Review Focus

Reviewers should focus on:

1. **Correctness** - Does it work?
2. **Learning Value** - Could someone learn from this code?
3. **Type Safety** - Are types properly annotated?
4. **Testing** - Are edge cases covered?
5. **Documentation** - Would a beginner understand this?

## 🐛 Bug Reports

### Good Bug Report Template

```markdown
**Describe the bug**
A clear and concise description.

**To Reproduce**
Steps to reproduce the behavior:
1. Install version X.Y.Z
2. Run command '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Environment**
- OS: [e.g. Ubuntu 22.04]
- Python version: [e.g. 3.11.5]
- Package version: [e.g. 0.2.1]

**Additional context**
- Stack trace (if applicable)
- Minimal code example
- Related issues
```

## 💡 Feature Requests

### Good Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
Clear and concise description of what you want to happen.

**Describe alternatives you've considered**
Other solutions you've thought about.

**Additional context**
- Use cases
- Code examples
- Similar features in other frameworks
```

## 📚 Documentation Contributions

We especially welcome:

- Tutorial articles
- Video walkthroughs
- Real-world example projects
- Translations (future)

## ❓ Questions?

- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bugs and feature requests
- **Discord** (coming soon): For real-time chat

## 🙏 Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in relevant documentation

---

Thank you for contributing to making Python web development more accessible! 🚀
