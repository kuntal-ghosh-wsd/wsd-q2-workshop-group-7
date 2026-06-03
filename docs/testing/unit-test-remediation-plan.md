# Unit Test Suite Remediation Plan

## Current State Analysis

### 1. Mocking Approaches (Mixed & Inconsistent)
- **Node's built-in mock.fn()**: Used in some tests (test.controller.test.js, apm.test.js)
- **Sinon**: Used in most tests (mongodb.service.test.js, redis.service.test.js, context.middleware.test.js)
- **Inconsistent**: Two different mocking libraries in the same codebase

### 2. Test Target Issues
✅ **Good**: Test targets are properly tested, not mocked
- Controllers test actual controller methods
- Services test actual service implementations
- Middleware tests actual middleware functions

### 3. Dependency Mocking Issues
❌ **Problem**: Inconsistent mocking patterns
- Some tests use `sinon.createSandbox()` with manual cleanup
- Others use Node's `mock.reset()`
- Global mocks (logger) are manually created in each test file
- No centralized mock management

### 4. ESM Compatibility Workarounds
❌ **Hacky Solution**: `createRequire` workaround
```javascript
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const packageJson = require('../../../../../package.json');
```

### 5. Other Issues Found
- **Global State Pollution**: Tests modify globals (logger, apm) without consistent cleanup
- **Manual Mock Setup**: Repetitive mock setup code across test files
- **No Test Helpers**: Missing shared test utilities

## Remediation Plan

### 1. Standardize on Node.js Built-in Test Mocks
- Replace all Sinon usage with Node's native `mock.fn()` and `mock.method()`
- Remove sinon dependency from package.json
- Benefits: Native ESM support, no external dependencies, consistent API

### 2. Create Centralized Test Utilities
Create `tests/unit/test-utils.js`:
- Mock factory functions for common dependencies (logger, MongoDB, Redis)
- Setup/teardown helpers
- Common test data builders

### 3. Fix ESM Package.json Import
Replace the hacky `createRequire` pattern with proper ESM import:
```javascript
import packageJson from '../../../../../package.json' with { type: 'json' };
```

### 4. Implement Test Context Manager
Create a test context that:
- Automatically sets up/tears down global mocks
- Provides consistent mock instances
- Ensures proper cleanup between tests

### 5. Add Mock Validation
- Ensure all external dependencies are mocked
- Add linting rules to prevent direct imports in tests
- Create mock coverage reports

### 6. Documentation
- Create testing guidelines document
- Document mock patterns and best practices
- Add examples for common test scenarios

## Implementation Priority
1. **High**: Standardize mocking library (affects all tests)
2. **High**: Fix ESM import issues (removes technical debt)
3. **Medium**: Create test utilities (improves maintainability)
4. **Medium**: Add test context manager (prevents test pollution)
5. **Low**: Documentation and guidelines

## Estimated Impact
- **Test Reliability**: Reduced flakiness from global state pollution
- **Developer Experience**: Consistent patterns, less boilerplate
- **Maintenance**: Easier to update mocks centrally
- **Performance**: Native mocks may be faster than Sinon
- **Technical Debt**: Removes workarounds and hacky solutions

## Next Steps
1. Review and approve this plan
2. Create feature branch for test refactoring
3. Implement changes incrementally, ensuring tests pass at each step
4. Update CI/CD configuration if needed
5. Train team on new patterns

## Notes for Next Session
- This plan was created after analyzing the entire unit test suite
- All test targets are properly tested (not mocked), which is good
- Main issues are inconsistent mocking approaches and technical debt
- Focus should be on standardization and removing workarounds