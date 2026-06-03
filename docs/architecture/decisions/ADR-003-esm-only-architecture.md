# ADR-003: ESM-Only Architecture

## Status
**Accepted** - 2024-12-05

## Context

Node.js has supported ES Modules (ESM) since version 12, with stable support since version 14. We needed to choose between continuing with CommonJS (CJS), adopting a hybrid approach, or fully committing to ESM for the WAIF framework.

### Current Module System Challenges
- **Legacy CommonJS**: Using `require()` and `module.exports`
- **Mixed Module Types**: Some dependencies use ESM, others CJS
- **Import/Export Inconsistency**: Different patterns across the codebase
- **Tooling Complexity**: Build tools handling multiple module formats
- **Performance Considerations**: Module loading and tree-shaking efficiency

### Module System Options Evaluated

#### 1. **CommonJS (Legacy)**
```javascript
// CommonJS syntax
const express = require('express');
const { UserService } = require('./services/user.service');
module.exports = { UserController };
```

#### 2. **Hybrid Approach**
```javascript
// Mixed syntax - CJS in some files, ESM in others
// Requires complex tooling and configuration
```

#### 3. **ESM-Only**
```javascript
// Pure ES Modules
import express from 'express';
import { UserService } from './services/user.service.js';
export { UserController };
```

### Technology Constraints
- **Node.js Version**: 24.x (latest LTS with full ESM support)
- **Build Tools**: Native Node.js ESM, no transpilation needed
- **Testing**: Node.js built-in test runner with ESM support
- **Deployment**: Modern container environments supporting ESM

## Decision

We will adopt an **ESM-Only Architecture** throughout the entire WAIF framework, eliminating CommonJS usage and ensuring consistency across all modules.

### Implementation Rules

#### 1. **File Extensions**
```javascript
// ✅ REQUIRED: All imports must specify .js extension
import { UserService } from './services/user.service.js';
import { logger } from '../utils/logger.js';

// ❌ FORBIDDEN: Extensions omitted (works in CJS, not ESM)
import { UserService } from './services/user.service';
```

#### 2. **Package.json Configuration**
```json
{
  "type": "module",
  "exports": {
    ".": {
      "import": "./src/index.js"
    }
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
```

#### 3. **Import/Export Patterns**
```javascript
// ✅ Named exports (preferred)
export const UserService = class {};
export const validateUser = () => {};

// ✅ Default exports (when appropriate)
export default class UserController {}

// ✅ Re-exports
export { UserService } from './user.service.js';
export * from './validation.js';

// ❌ FORBIDDEN: CommonJS syntax
const express = require('express');
module.exports = UserService;
```

## Rationale

### Why ESM-Only?

#### 1. **Future-Proof Technology Stack**
- **Native Node.js Support**: No transpilation required
- **Standard Specification**: ECMAScript modules are the official standard
- **Ecosystem Direction**: npm packages increasingly adopting ESM
- **Modern Tooling**: Better support in development tools

#### 2. **Performance Benefits**
```javascript
// ESM enables better tree-shaking
import { specificFunction } from 'large-library'; // Only imports what's needed

// vs CommonJS
const entireLibrary = require('large-library'); // Imports everything
```

#### 3. **Static Analysis Advantages**
- **Compile-time Import Resolution**: Errors caught earlier
- **Better IDE Support**: Improved autocomplete and refactoring
- **Dependency Analysis**: Clear dependency graphs
- **Bundle Optimization**: More efficient bundling

#### 4. **Consistency and Maintainability**
```javascript
// Single, consistent import/export pattern throughout codebase
import express from 'express';
import { MongoDBService } from './services/mongodb.service.js';
import { logger } from '../utils/logger.js';

export class ApiController {
  // Implementation
}
```

### Why Not Other Approaches?

#### CommonJS Continuation
- **❌ Legacy Technology**: Being phased out by ecosystem
- **❌ Performance Limitations**: No tree-shaking, larger bundles
- **❌ Tooling Issues**: Decreasing support in modern tools
- **❌ Future Compatibility**: New packages dropping CJS support

#### Hybrid Approach
- **❌ Complexity**: Managing two module systems is complex
- **❌ Inconsistency**: Different patterns confuse developers
- **❌ Tooling Overhead**: Requires complex build configurations
- **❌ Maintenance Burden**: More code paths to maintain

## Implementation Details

### Project Structure
```
src/
├── api/
│   ├── v1.0/
│   │   ├── controllers/        # *.js (ESM)
│   │   ├── routes/            # *.js (ESM)  
│   │   └── services/          # *.js (ESM)
│   └── middleware/            # *.js (ESM)
├── utils/                     # *.js (ESM)
├── config/                    # *.js (ESM)
└── app.js                     # Main ESM entry point
```

### Import Path Conventions
```javascript
// ✅ Relative imports with explicit extensions
import { UserService } from './services/user.service.js';
import { validateInput } from '../utils/validation.js';

// ✅ Absolute imports from node_modules
import express from 'express';
import { MongoClient } from 'mongodb';

// ✅ Barrel exports (index.js files)
import { UserController, OrderController } from './controllers/index.js';
```

### Dynamic Imports
```javascript
// ESM supports dynamic imports for conditional loading
const loadFeature = async (featureName) => {
  const { feature } = await import(`./features/${featureName}.js`);
  return feature;
};

// Useful for optional dependencies
try {
  const { debugModule } = await import('./debug/advanced.js');
} catch (error) {
  // Graceful fallback if debug module not available
}
```

### Configuration Module
```javascript
// config/index.js - ESM configuration pattern
import { config } from 'dotenv';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

// ESM equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

config({ path: resolve(__dirname, '../.env') });

export const appConfig = {
  port: process.env.PORT || 3000,
  mongodb: {
    uri: process.env.MONGODB_URI,
    database: process.env.MONGODB_DATABASE
  }
};
```

### Error Handling with ESM
```javascript
// Error classes using ESM exports
export class AppError extends Error {
  constructor(message, code = 'GENERIC_ERROR', statusCode = 500) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.statusCode = statusCode;
    this.isOperational = true;
  }
}

export class ValidationError extends AppError {
  constructor(message, field = null) {
    super(message, 'VALIDATION_ERROR', 400);
    this.field = field;
  }
}
```

## Migration Strategy

### Phase 1: Package Configuration
```json
// package.json changes
{
  "type": "module",
  "main": "src/app.js",
  "scripts": {
    "start": "node src/app.js",
    "test": "node --test tests/**/*.test.js"
  }
}
```

### Phase 2: File-by-File Conversion
```bash
# Convert CommonJS to ESM systematically
# 1. Update imports/exports
# 2. Add .js extensions
# 3. Update package.json type
# 4. Test thoroughly
```

### Phase 3: Dependency Updates
```javascript
// Update all dependencies to ESM-compatible versions
// Check npm packages for ESM support
// Replace CJS-only packages where necessary
```

## Consequences

### Positive

#### 1. **Modern Development Experience**
- **Better IDE Support**: Improved IntelliSense and refactoring
- **Static Analysis**: Earlier error detection
- **Standard Compliance**: Following ECMAScript specifications

#### 2. **Performance Improvements**
- **Tree Shaking**: Better dead code elimination
- **Smaller Bundles**: More efficient bundling
- **Faster Loading**: Native browser/Node.js support

#### 3. **Future Compatibility**
- **Ecosystem Alignment**: Better compatibility with modern packages
- **Tool Support**: Better integration with modern tooling
- **Standard Adoption**: Following industry direction

#### 4. **Development Efficiency**
```javascript
// Consistent patterns across entire codebase
import { service } from './service.js';  // Always this pattern
export { controller } from './controller.js';  // Always this pattern
```

### Negative

#### 1. **Learning Curve**
- **Developer Training**: Team needs to understand ESM patterns
- **Different Syntax**: Change from familiar CommonJS patterns
- **Import Path Requirements**: Must remember .js extensions

#### 2. **Ecosystem Compatibility**
- **Some Legacy Packages**: May not support ESM yet
- **Tooling Updates**: Some tools may need updates
- **Third-party Integration**: May require workarounds

#### 3. **Migration Effort**
- **Codebase Conversion**: Existing code needs updating
- **Testing Requirements**: Extensive testing during migration
- **Documentation Updates**: All examples need updating

### Mitigation Strategies

#### 1. **Developer Training**
```javascript
// Create comprehensive migration guide
// Provide code examples and patterns  
// Set up linting rules to enforce ESM patterns
```

#### 2. **Gradual Migration**
```javascript
// Migrate module by module
// Extensive testing at each step
// Maintain backward compatibility during transition
```

#### 3. **Tooling Support**
```json
// ESLint configuration for ESM
{
  "parserOptions": {
    "ecmaVersion": 2022,
    "sourceType": "module"
  },
  "rules": {
    "prefer-const": "error",
    "no-var": "error"
  }
}
```

## Development Guidelines

### 1. **Import Organization**
```javascript
// Group imports logically
// 1. Node.js built-in modules
import { resolve } from 'path';
import { readFile } from 'fs/promises';

// 2. Third-party packages
import express from 'express';
import { MongoClient } from 'mongodb';

// 3. Internal modules (absolute paths first, then relative)
import { logger } from '../utils/logger.js';
import { UserService } from './user.service.js';
```

### 2. **Export Patterns**
```javascript
// Prefer named exports for better tree-shaking
export const userController = new UserController();
export const userService = new UserService();

// Use default exports sparingly, for main module exports
export default class Application {
  // Main application class
}
```

### 3. **File Naming**
```javascript
// All JavaScript files use .js extension
// Service files: user.service.js
// Controller files: user.controller.js
// Utility files: validation.js
// Test files: user.service.test.js
```

## Testing with ESM

### Node.js Test Runner
```javascript
// tests/user.service.test.js
import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert';
import { UserService } from '../src/services/user.service.js';

describe('UserService', () => {
  let userService;

  beforeEach(() => {
    userService = new UserService();
  });

  it('should create user', async () => {
    const user = await userService.create({ name: 'Test' });
    assert.ok(user.id);
  });
});
```

### Mocking in ESM
```javascript
// Use dynamic imports for mocking
const mockUserService = {
  create: () => Promise.resolve({ id: '123' })
};

// Mock using import.meta.resolve or dynamic imports
const originalImport = await import('../src/services/user.service.js');
// Apply mocks as needed
```

## Monitoring and Debugging

### ESM-Specific Debugging
```javascript
// Use import.meta for module information
console.log('Current module:', import.meta.url);
console.log('Module resolved:', import.meta.resolve('./other.js'));

// Dynamic imports for conditional debugging
if (process.env.NODE_ENV === 'development') {
  const { debugUtility } = await import('./debug-utils.js');
  debugUtility.enableVerboseLogging();
}
```

### Performance Monitoring
```javascript
// Monitor import performance
const startTime = performance.now();
const { heavyModule } = await import('./heavy-computation.js');
const loadTime = performance.now() - startTime;
logger.debug('Module load time', { module: 'heavy-computation', loadTime });
```

## Future Considerations

### 1. **Import Maps** (Future Node.js feature)
```json
{
  "imports": {
    "@utils/": "./src/utils/",
    "@services/": "./src/services/"
  }
}
```

### 2. **Top-Level Await**
```javascript
// Already supported in Node.js 14.8+
const config = await import('./config.js');
const db = await connectToDatabase();
```

### 3. **Module Federation**
```javascript
// Potential future feature for microservices
const remoteModule = await import('https://remote-service/module.js');
```

## References

- [Node.js ES Modules Documentation](https://nodejs.org/api/esm.html)
- [ECMAScript Modules Specification](https://tc39.es/ecma262/#sec-modules)
- [ES Modules: A Cartoon Deep-Dive](https://hacks.mozilla.org/2018/03/es-modules-a-cartoon-deep-dive/)

## Review and Updates

- **Decision Date**: 2024-12-05
- **Last Reviewed**: 2024-12-05
- **Next Review**: 2025-06-01 (6 months)
- **Status**: Active implementation

---

*This ADR establishes ESM as the exclusive module system for the WAIF framework, ensuring modern, performant, and maintainable code that aligns with ECMAScript standards and Node.js best practices.*