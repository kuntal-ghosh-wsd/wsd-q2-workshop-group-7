<!-- File: /docs/patterns/STANDARDS.md -->
<!-- Last Updated: 2024-12-07 -->
<!-- Status: current -->

# WAIF Framework Coding Standards

> **TypeScript Reference**: For TypeScript-specific standards, type definitions, and configuration details, see [TypeScript Configuration Guide](./typescript.md).

## Code Style Fundamentals

### Language Support
This framework uses TypeScript as the primary language:
- **TypeScript files**: Use `.ts` extension with native TypeScript types
- **Type definitions**: Use `.d.ts` for ambient type declarations
- **ES Modules**: Must use `.js` extensions in imports (NodeNext requirement)

### ESM-First Architecture
- All files use ES modules (`.ts` extension)
- No CommonJS (`require`/`module.exports`) anywhere
- All imports must specify `.js` extension explicitly (TypeScript compiles `.ts` to `.js`)

```typescript
// ✅ Correct ES module imports
import express from 'express';
import { MongoDBService } from '../services/mongodb.service.js';
import { logger } from '../../utils/logger.js';

// ❌ Wrong - Missing .js extension
import { MongoDBService } from '../services/mongodb.service';

// ❌ Wrong - CommonJS syntax
const express = require('express');
```

### File Organization Standards

#### Directory Structure Rules
```
src/api/v{version}/          # Version-specific API code
├── controllers/             # Request handlers only
├── routes/                 # Route definitions only  
├── services/               # Business logic and data access
└── middleware/             # Custom middleware
    ├── core/               # Core processing middleware
    ├── security/           # Security-related middleware
    └── versioning/         # Version resolution middleware
```

#### File Naming Conventions
- **Controllers**: `{resource}.controller.ts` (e.g., `user.controller.ts`)
- **Services**: `{resource}.service.ts` (e.g., `mongodb.service.ts`)
- **Routes**: `{resource}.routes.ts` (e.g., `test.routes.ts`)
- **Middleware**: `{purpose}.middleware.ts` (e.g., `error.middleware.ts`)
- **Utilities**: `{purpose}.ts` (e.g., `response.handler.ts`)
- **Type Definitions**: `{purpose}.d.ts` (e.g., `express.d.ts` for augmentations)

#### File Structure Template
```typescript
/**
 * @fileoverview Brief description of file purpose
 * @author WAIF Framework
 * @since 1.0.0
 */

// External dependencies first
import express from 'express';
import type { Application } from 'express';

// Internal dependencies (services, utilities)
import { MongoDBService } from '../services/mongodb.service.js';
import { logger } from '../../utils/logger.js';
import type { Logger } from 'pino';

// Type definitions (if not in separate .d.ts file)
interface ExampleOptions {
  timeout: number;
  retries: number;
}

// Constants and configuration
const DEFAULT_OPTIONS: ExampleOptions = {
  timeout: 5000,
  retries: 3,
} as const;

// Main implementation
class ExampleService {
  private options: ExampleOptions;

  constructor(options: Partial<ExampleOptions> = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }
}

// Single default export (preferred) or named exports
export default ExampleService;
// OR
export { ExampleService, DEFAULT_OPTIONS };
export type { ExampleOptions };
```

### Naming Conventions

#### Variables and Functions
- **camelCase** for variables and functions
- **PascalCase** for classes and constructors
- **UPPER_SNAKE_CASE** for constants
- **kebab-case** for file names and directories

```typescript
// ✅ Correct naming
const userService = new UserService();
const API_VERSION = 'v1.0';
const DEFAULT_TIMEOUT = 5000;

class UserController {
  async createUser(userData: UserData): Promise<User> {
    // Implementation
  }
}

// ❌ Wrong naming
const UserService = new userService();  // Wrong case
const api_version = 'v1.0';            // Wrong case for constant
const defaulttimeout = 5000;           // Not descriptive enough
```

#### Method Naming Patterns
- **CRUD operations**: `create`, `find`, `update`, `delete` (not `get`)
- **Boolean returns**: Start with `is`, `has`, `can`, `should`
- **Async functions**: Use descriptive verbs, not `get` prefix

```javascript
// ✅ Correct method names
async findUserById(id) { }
async createNewUser(userData) { }
async updateUserProfile(id, updates) { }
async deleteUserAccount(id) { }

isHealthy() { return true; }
hasValidToken(token) { return true; }
canAccessResource(user, resource) { return true; }

// ❌ Wrong method names
async getUser(id) { }              // Use 'find' for async database operations
async getUserById(id) { }          // Redundant 'get' prefix
healthy() { }                      // Should be 'isHealthy'
validateToken(token) { }           // Should return boolean with 'is/has/can'
```

### TypeScript Documentation Standards

#### Required TSDoc for All Functions
Every function must have comprehensive TSDoc comments with proper TypeScript types:

```typescript
interface UserData {
  email: string;
  name: string;
  avatar?: string;
}

interface CreateUserOptions {
  sendWelcomeEmail?: boolean;
  timeout?: number;
}

interface CreatedUser {
  id: string;
  email: string;
  name: string;
  createdAt: Date;
}

/**
 * Creates a new user account with validation and error handling.
 *
 * @param userData - The user information
 * @param options - Additional options
 * @returns The created user object
 *
 * @throws {@link ValidationError} When required fields are missing or invalid
 * @throws {@link ConflictError} When email already exists
 * @throws {@link AppError} For general application errors
 *
 * @example
 * // Create a basic user account
 * const user = await createUser({
 *   email: 'john@example.com',
 *   name: 'John Doe'
 * });
 * console.log(user.id); // "user-123-abc"
 *
 * @example
 * // Create user without welcome email
 * const user = await createUser({
 *   email: 'jane@example.com',
 *   name: 'Jane Smith'
 * }, { sendWelcomeEmail: false });
 *
 * @since 1.0.0
 */
async createUser(
  userData: UserData,
  options: CreateUserOptions = {}
): Promise<CreatedUser> {
  // Implementation
}
```

#### Class Documentation
```javascript
/**
 * MongoDB service providing database operations with connection pooling,
 * transaction support, and health monitoring capabilities.
 * 
 * Implements singleton pattern to ensure single database connection
 * across the application lifecycle.
 * 
 * @class MongoDBService
 * @since 1.0.0
 * 
 * @example
 * // Get service instance
 * const mongodb = MongoDBService.getInstance();
 * 
 * // Perform database operations
 * const users = await mongodb.find('users', { active: true });
 */
class MongoDBService {
  /**
   * Private constructor - use getInstance() instead.
   * @private
   */
  constructor() {
    // Implementation
  }
}
```

### Error Handling Standards

#### Error Class Hierarchy
All errors must extend the base `AppError` class:

```javascript
import { AppError, ValidationError, ConflictError } from '../../utils/errors.js';

// ✅ Correct error throwing
throw new ValidationError('Email is required');
throw new ConflictError('Email already exists');
throw new AppError('Database connection failed', 'DB_CONNECTION_ERROR', 500);

// ❌ Wrong error throwing
throw new Error('Something went wrong');           // Too generic
throw 'Error message';                            // Not an Error object
return { error: 'Something failed' };             // Don't return errors
```

#### Async Error Handling Pattern
Always wrap async operations with proper error handling:

```javascript
/**
 * Standard async function error handling pattern
 */
async function performDatabaseOperation(collection, query) {
  try {
    const result = await mongodb.find(collection, query);
    logger.info('Database operation successful', { 
      collection, 
      resultCount: result.length 
    });
    return { success: true, data: result };
  } catch (error) {
    logger.error('Database operation failed', {
      error: error.message,
      stack: error.stack,
      collection,
      query
    });
    
    // Transform database errors into application errors
    if (error.code === 11000) {
      throw new ConflictError('Duplicate key violation');
    }
    
    throw new AppError(
      'Database operation failed', 
      'DB_OPERATION_ERROR',
      500,
      { originalError: error.message }
    );
  }
}
```

### Response Handler Standards

#### Controller Response Patterns
Always use response handlers from request context:

```javascript
/**
 * Standard controller method pattern
 */
class UserController {
  /**
   * Creates a new user account.
   * Standard pattern: validate → call service → return response
   */
  async createUser(request, response, next) {
    try {
      // Input validation
      const { email, name } = request.body;
      if (!email || !name) {
        return request.context.error(
          'Email and name are required',
          400,
          'VALIDATION_ERROR'
        );
      }

      // Business logic (delegate to service)
      const user = await userService.createUser({ email, name });

      // Success response
      return request.context.success(
        'User created successfully',
        user,
        201
      );
      
    } catch (error) {
      // Let error middleware handle it
      next(error);
    }
  }
}
```

#### Service Response Patterns
Services should return data or throw errors, never handle HTTP responses:

```javascript
/**
 * Service layer - pure business logic, no HTTP concerns
 */
class UserService {
  async createUser(userData) {
    // Validate business rules
    await this.validateUserData(userData);
    
    // Perform business operation
    const user = await mongodb.insertOne('users', {
      ...userData,
      createdAt: new Date(),
      id: this.generateUserId()
    });
    
    // Return business data (no HTTP status codes here)
    return user;
  }
  
  // Private validation method
  async validateUserData(userData) {
    if (await this.emailExists(userData.email)) {
      throw new ConflictError('Email already registered');
    }
  }
}
```

### Logging Standards

#### Structured Logging Pattern
Use Pino logger with structured data:

```javascript
import { logger } from '../../utils/logger.js';

// ✅ Correct structured logging
logger.info('User operation completed', {
  operation: 'createUser',
  userId: user.id,
  email: user.email,
  duration: performance.now() - startTime
});

logger.error('Database connection failed', {
  error: error.message,
  stack: error.stack,
  host: process.env.MONGODB_URI,
  retryAttempt: attempts
});

// ❌ Wrong logging patterns
logger.info('User created');                    // Not enough context
logger.info(`User ${user.email} created`);     // String interpolation instead of structured data
console.log('Debug info');                     // Don't use console.log
```

#### Context-Aware Logging
Use request context logger when available:

```javascript
// In controllers and middleware - use request context
async function handleRequest(request, response, next) {
  request.context.logger.info('Processing request', {
    method: request.method,
    path: request.path,
    userId: request.user?.id
  });
}

// In services - use global logger
class UserService {
  async createUser(userData) {
    logger.info('Creating new user', {
      email: userData.email,
      hasAvatar: !!userData.avatar
    });
  }
}
```

### Testing Standards

#### Test File Organization
```
tests/
├── unit/                    # Unit tests mirror src/ structure
│   └── api/v1.0/
│       ├── controllers/
│       ├── services/
│       └── middleware/
├── integration/             # Integration tests by feature
│   └── api/v1.0/
├── fixtures/               # Test data and mocks
└── helpers/                # Test utilities
```

#### Test Naming Conventions
```javascript
// ✅ Correct test structure
describe('UserController', () => {
  describe('createUser', () => {
    it('should create user with valid data', async () => {
      // Test implementation
    });
    
    it('should return 400 when email is missing', async () => {
      // Test implementation  
    });
    
    it('should return 409 when email already exists', async () => {
      // Test implementation
    });
  });
});

// ❌ Wrong test structure
describe('UserController Tests', () => {           // Don't add "Tests" suffix
  it('creates user', async () => {                 // Not descriptive enough
    // Test implementation
  });
});
```

#### Test Implementation Patterns
```javascript
describe('UserService', () => {
  describe('createUser', () => {
    it('should create user with valid data', async () => {
      // Arrange
      const userData = {
        email: 'test@example.com',
        name: 'Test User'
      };
      
      // Act
      const result = await userService.createUser(userData);
      
      // Assert
      assert.strictEqual(result.email, userData.email);
      assert.strictEqual(result.name, userData.name);
      assert.ok(result.id);
      assert.ok(result.createdAt instanceof Date);
    });
  });
});
```

### Express v5 Compliance Standards

#### Route Path Syntax
Express v5 has breaking changes in route syntax:

```javascript
// ✅ Express v5 compliant routes
app.get('/{*splat}', handler);           // Named wildcard
app.get('/users/:id{:format}?', handler); // Optional parameters
app.get('/files/:name.:ext', handler);    // Required parameters

// ❌ Express v4 syntax (breaks in v5)
app.get('/*', handler);                   // Unnamed wildcard
app.get('/users/:id/:format?', handler);  // Old optional syntax
```

#### Middleware Declaration
```javascript
// ✅ Correct middleware patterns for Express v5
app.use('/{*splat}', globalMiddleware);
app.use('/api/v1.0', apiMiddleware);
router.get('/ping', pingController);

// ❌ Patterns that may break
app.use('*', globalMiddleware);           // Use named wildcard
```

### Performance Standards

#### Async/Await Patterns
Always use async/await, never callbacks or raw Promises:

```javascript
// ✅ Correct async patterns
async function performOperations() {
  try {
    const user = await findUser(id);
    const profile = await updateProfile(user.id, data);
    return profile;
  } catch (error) {
    logger.error('Operation failed', { error: error.message });
    throw error;
  }
}

// ❌ Wrong patterns
function performOperations(callback) {     // Don't use callbacks
  findUser(id)
    .then(user => updateProfile(user.id, data))  // Don't chain .then()
    .then(callback)
    .catch(callback);
}
```

#### Memory Management
```javascript
// ✅ Efficient patterns
const results = [];
for (const item of items) {
  const processed = await processItem(item);
  if (processed) results.push(processed);
}

// ❌ Memory inefficient
const results = await Promise.all(
  items.map(async item => await processItem(item))  // Processes all at once
);
```

### Git Commit Standards

#### Commit Message Format
```
type(scope): brief description

Detailed explanation of the change including why the change is needed.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

#### Commit Types
- `feat:` New feature implementation
- `fix:` Bug fix
- `refactor:` Code refactoring without behavior changes
- `perf:` Performance optimization
- `test:` Adding or updating tests
- `docs:` Documentation updates
- `chore:` Maintenance tasks, dependency updates
- `style:` Code formatting, no logic changes

#### Examples
```bash
# ✅ Good commit messages
feat(auth): add JWT token validation middleware

Implements JWT token validation with configurable secret and expiration.
Adds comprehensive error handling for expired and invalid tokens.

fix(database): resolve connection pool exhaustion issue

Updates MongoDB connection configuration to prevent pool exhaustion
during high load scenarios. Increases pool size and adds retry logic.

# ❌ Poor commit messages
fix: bug fix                    # Too vague
update user controller          # Missing type and scope
```

### Configuration Standards

#### Environment Variables
Use descriptive, hierarchical naming:

```javascript
// ✅ Good environment variable names
NODE_ENV=production
PORT=4444
MONGODB_URI=mongodb://localhost:27017/waif
MONGODB_DATABASE_NAME=waif_production
REDIS_URL=redis://localhost:6379
LOG_LEVEL=info
RATE_LIMIT_MAX_REQUESTS=100

// ❌ Poor naming
ENV=prod                        # Too short
DB_URL=mongodb://...           # Not specific enough
REDIS=redis://localhost        # Missing context
```

#### Configuration Object Structure
```javascript
// src/config/index.js
export const config = {
  app: {
    port: parseInt(process.env.PORT) || 4444,
    environment: process.env.NODE_ENV || 'development'
  },
  database: {
    mongodb: {
      uri: process.env.MONGODB_URI || 'mongodb://localhost:27017',
      name: process.env.MONGODB_DATABASE_NAME || 'waif_development'
    },
    redis: {
      url: process.env.REDIS_URL || 'redis://localhost:6379'
    }
  },
  logging: {
    level: process.env.LOG_LEVEL || 'info'
  }
};
```

## Quality Assurance Standards

### Pre-commit Checklist
Before any commit:
- [ ] All functions have JSDoc documentation
- [ ] Error handling follows AppError patterns
- [ ] Tests added for new functionality
- [ ] ESLint passes with zero warnings
- [ ] No console.log statements in production code
- [ ] All imports use `.js` extensions

### Code Review Standards
Code must meet these criteria:
- [ ] Follows naming conventions consistently
- [ ] Implements proper error handling
- [ ] Has comprehensive test coverage (>80%)
- [ ] Uses structured logging throughout
- [ ] Follows Express v5 patterns
- [ ] No security vulnerabilities introduced

### Testing Requirements
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test complete API endpoints
- **Error Cases**: Test all error conditions
- **Edge Cases**: Test boundary conditions
- **Performance**: Test timeout and resource limits

## Related Documentation
- [API Patterns](./api-patterns.md)
- [Error Handling Patterns](./error-handling.md)
- [Testing Patterns](./testing-patterns.md)
- [Anti-patterns to Avoid](./anti-patterns.md)