# Testing code whose framework is not installed

When code imports a framework that is missing from the test environment (for example Home Assistant or Django), stub the modules so the code imports, then test only the code's own logic.

1. Enumerate every import of the framework across all files in the package, including transitive ones. One missed name fails collection with `ImportError`.
2. Register stub modules for each before importing the code under test. In Python, insert `types.ModuleType` objects into `sys.modules`.
3. Give each stub every attribute the code imports: classes, constants, exceptions, and functions.
4. Keep all stub setup in one place, such as `conftest.py` or the top of the test file.
5. Test the code's logic, not the stubbed framework. Verify framework interaction in integration tests with the real framework installed.

```python
import sys, types

for name in ("framework", "framework.core", "framework.helpers"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["framework.core"].BaseEntity = type("BaseEntity", (), {})
sys.modules["framework.helpers"].get_session = lambda *a, **k: None

from mypackage.integration import MyClient  # noqa: E402  (import after stubs)
```
