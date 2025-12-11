# Loader Factory Pattern Implementation

## Overview
Successfully implemented Task 3.2: Loader Factory Pattern for clean abstraction and decoupling in the RedditHarbor Pipeline V4.

## Architecture

### SOLID Principles Applied
- **S**ingle Responsibility: Each class has one responsibility
- **O**pen/Closed: Easy to extend with new loaders without modifying existing code
- **L**iskov Substitution: Both loaders can be used interchangeably via BaseLoader
- **I**nterface Segregation: BaseLoader interface is focused and minimal
- **D**ependency Inversion: Pipeline depends on abstraction, not concrete implementations

### Clean Architecture Benefits
- **Decoupling**: Pipeline no longer knows about concrete loader types
- **Centralization**: All loader creation logic in one place
- **Testability**: Easy to inject mock loaders for testing
- **Extensibility**: Simple to add new loader implementations

## Implementation Details

### 1. BaseLoader Abstract Interface (`load/loader_factory.py`)
```python
class BaseLoader(ABC):
    @abstractmethod
    def save_opportunity(self, opportunity: Opportunity) -> bool:
        pass

    @abstractmethod
    def save_analysis(self, analysis) -> bool:
        pass

    def close(self):
        pass
```

### 2. Factory Function (`load/loader_factory.py`)
```python
def get_loader(settings: Settings = None, loader_override: BaseLoader = None) -> BaseLoader:
    # Dependency injection support
    if loader_override is not None:
        return loader_override

    # Factory selection based on feature flag
    if settings.use_sqlmodel_loader:
        return SQLModelLoader(settings)
    else:
        return PostgresLoader(settings)
```

### 3. Type Safety (`load/loader_factory.py`)
```python
class LoaderType:
    POSTGRES = "postgres"
    SQLMODEL = "sqlmodel"

    @classmethod
    def is_valid(cls, loader_type: str) -> bool:
        return loader_type in cls.all_types()

def create_loader_by_type(loader_type: str, settings: Settings = None) -> BaseLoader:
    # Explicit loader creation by type string
```

### 4. Updated Loader Classes
- **PostgresLoader**: Now inherits from `BaseLoader`
- **SQLModelLoader**: Now inherits from `BaseLoader`
- Both maintain full backward compatibility

### 5. Refactored Pipeline (`core/pipeline.py`)
```python
# BEFORE: Conditional loader selection
if self.settings.use_sqlmodel_loader:
    self.loader = SQLModelLoader(self.settings)
else:
    self.loader = PostgresLoader(self.settings)

# AFTER: Clean factory usage
self.loader = get_loader(self.settings, loader)
```

## Files Created/Modified

### New Files
1. **`load/loader_factory.py`** - Factory implementation with BaseLoader abstract class
2. **`tests/test_loader_factory.py`** - Comprehensive test suite

### Modified Files
1. **`load/postgres_loader.py`** - Updated to inherit from BaseLoader
2. **`load/sqlmodel_loader.py`** - Updated to inherit from BaseLoader
3. **`core/pipeline.py`** - Refactored to use factory pattern

## Key Features

### Dependency Injection
```python
# For testing: inject mock loader
mock_loader = MockLoader()
loader = get_loader(loader_override=mock_loader)

# Pipeline automatically uses injected loader
pipeline = Pipeline(loader=mock_loader)
```

### Feature Flag Control
```python
# Settings-based loader selection
settings = Settings(use_sqlmodel_loader=True)
loader = get_loader(settings)  # Returns SQLModelLoader

settings = Settings(use_sqlmodel_loader=False)
loader = get_loader(settings)  # Returns PostgresLoader
```

### Explicit Type Selection
```python
# Create specific loader by type
loader = create_loader_by_type(LoaderType.SQLMODEL)
```

### Error Handling
- Graceful handling of import errors
- Clear error messages for invalid loader types
- Runtime error wrapping for database failures

## Testing Coverage

### Test Categories
1. **Factory Behavior Tests**
   - Correct loader selection based on settings
   - Dependency injection functionality
   - Type validation and error handling

2. **Interface Compliance Tests**
   - BaseLoader is properly abstract
   - Both loaders implement required methods
   - Type checking and inheritance verification

3. **Integration Tests**
   - Pipeline uses factory correctly
   - Loader switching works with feature flag
   - End-to-end functionality verification

### Running Tests
```bash
# Run comprehensive test suite
pytest tests/test_loader_factory.py -v

# Run manual verification
python3 -c "
from load.loader_factory import get_loader, LoaderType
print('Available types:', LoaderType.all_types())
print('Factory works:', type(get_loader()).__name__)
"
```

## Future Extensibility

### Adding a New Loader (e.g., MongoDBLoader)
1. Create implementation:
```python
class MongoDBLoader(BaseLoader):
    def save_opportunity(self, opportunity):
        # MongoDB-specific implementation
        pass
```

2. Update factory:
```python
# In get_loader()
elif settings.use_mongodb_loader:
    return MongoDBLoader(settings)

# In create_loader_by_type()
elif loader_type == LoaderType.MONGODB:
    return MongoDBLoader(settings)
```

3. Add to LoaderType:
```python
class LoaderType:
    MONGODB = "mongodb"
```

### Benefits of this Approach
- Zero impact on existing Pipeline code
- Clean separation of concerns
- Easy configuration and testing
- Type-safe loader selection
- Centralized error handling

## Conclusion

The loader factory pattern successfully achieves the architectural goals:

✅ **Decoupled**: Pipeline depends on abstraction, not concrete loaders
✅ **Centralized**: Single point of loader creation and configuration
✅ **Configurable**: External feature flag controls loader selection
✅ **Testable**: Easy dependency injection for unit testing
✅ **Extensible**: Simple to add new loader implementations
✅ **Maintainable**: Clean SOLID principles and clean architecture

The implementation maintains full backward compatibility while providing a clean, extensible foundation for future database loader implementations.
