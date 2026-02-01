"""
Fast Track Framework - API Resources

This module provides a transformation layer between database models and JSON
responses, inspired by Laravel API Resources.

Public API:
----------
- JsonResource: Base class for resource transformation
- ResourceCollection: Handle collections of resources
- MISSING: Sentinel value for conditional attributes

Usage:
------
```python
from ftf.resources import JsonResource

class UserResource(JsonResource[User]):
    def to_array(self, request: Request | None = None) -> dict[str, Any]:
        return {
            "id": self.resource.id,
            "name": self.resource.name,
            "email": self.resource.email,
        }

# Single resource
return UserResource.make(user).resolve()
# {"data": {"id": 1, "name": "John", "email": "..."}}

# Collection
return UserResource.collection(users).resolve()
# {"data": [{...}, {...}]}
```

Educational Note:
----------------
API Resources solve the problem of decoupling your database schema
from your API response format. This allows you to:

1. **Rename fields**: database_field -> apiField
2. **Format data**: datetime -> ISO 8601 string
3. **Hide sensitive data**: Don't expose passwords, tokens
4. **Add computed fields**: full_name from first_name + last_name
5. **Control relationships**: Only include when eager-loaded
6. **Conditional fields**: Based on permissions, user type, etc.

See docs/guides/resources.md for complete guide.
"""

from ftf.resources.collection import ResourceCollection
from ftf.resources.core import MISSING, JsonResource

__all__ = [
    "JsonResource",
    "ResourceCollection",
    "MISSING",
]
