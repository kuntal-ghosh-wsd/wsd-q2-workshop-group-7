<!-- File: /docs/patterns/anti-patterns.md -->
<!-- Last Updated: 2024-12-05 -->
<!-- Status: current -->

# WAIF Framework Anti-Patterns

## Overview

This document identifies common anti-patterns that violate WAIF framework principles and cause issues in production. Avoiding these patterns is critical for maintaining system reliability, performance, and maintainability.

## Critical Anti-Patterns (Will Break System)

### 1. Missing .js Extensions in ES Module Imports

**❌ Anti-Pattern:**
```javascript
// These WILL cause MODULE_NOT_FOUND errors
import { MongoDBService } from '../services/mongodb.service';
import { logger } from '../../utils/logger';
import express from 'express';  // This one is OK (external package)
```

**✅ Correct Pattern:**
```javascript
// Always include .js extension for local modules
import { MongoDBService } from '../services/mongodb.service.js';
import { logger } from '../../utils/logger.js';
import express from 'express';  // External packages don't need extension
```

**Why Critical**: Node.js ESM requires explicit extensions for local modules. Missing extensions cause immediate runtime failures.

### 2. Express v4 Route Syntax (Breaks in Express v5)

**❌ Anti-Pattern:**
```javascript
// These patterns WILL fail in Express v5
app.use('*', middleware);                    // Unnamed wildcard
app.get('/users/:id/:format?', handler);     // Old optional syntax
app.get('/files/:name(\\w+)', handler);      // Regex patterns in parens
```

**✅ Correct Pattern:**
```javascript
// Express v5 compliant syntax
app.use('/*splat', middleware);              // Named wildcard
app.get('/users/:id{/:format}?', handler);   // New optional syntax
app.get('/files/:name', handler);            // Simplified patterns
```

**Why Critical**: Express v5 breaks on unnamed wildcards and old parameter syntax.

### 3. Using CommonJS in ESM Environment

**❌ Anti-Pattern:**
```javascript
// These WILL cause errors in pure ESM environment
const express = require('express');
const config = require('./config');
module.exports = { someFunction };

// Mixed syntax - also problematic
import express from 'express';
module.exports = router;  // Don't mix import/require syntax
```

**✅ Correct Pattern:**
```javascript
// Pure ES module syntax only
import express from 'express';
import { config } from './config.js';
export { someFunction };
export default router;
```

**Why Critical**: CommonJS breaks in pure ESM environment and causes module loading failures.

### 4. Wrong Middleware Chain Order

**❌ Anti-Pattern:**
```javascript
// This order WILL cause context errors
app.use('/api', routes);              // Routes before context
app.use(contextMiddleware);           // Context too late
app.use(errorMiddleware);             // Error handling in wrong place
app.use(rateLimiter);                 // Rate limiting after routes
```

**✅ Correct Pattern:**
```javascript
// REQUIRED middleware order
app.use(configureHelmet());           // 1. Security first
app.use(configureCors());             // 2. CORS after security
app.use(rateLimiter);                 // 3. Rate limiting before parsing
app.use(express.json({ limit: '10mb' })); // 4. Body parsing
app.use(contextMiddleware);           // 5. Context creation
app.use(requestResponseLogger);       // 6. Logging after context
app.use('/api', routes);              // 7. Routes after all setup
app.use(errorMiddleware);             // 8. Error handling LAST
```

**Why Critical**: Wrong middleware order causes undefined context errors and security vulnerabilities.

### 5. URL-Based API Versioning

**❌ Anti-Pattern:**
```javascript
// NEVER expose version in URLs to clients
app.get('/api/v1.0/users', handler);
app.get('/api/v2.0/users', handler);

// Client code
fetch('/api/v1.0/users');  // Wrong versioning approach
```

**✅ Correct Pattern:**
```javascript
// Use URL path versioning for code organization
app.get('/api/users', handler);
```

## High-Impact Anti-Patterns

### 6. Direct Response Object Usage

**❌ Anti-Pattern:**
```javascript
// Bypasses standardized response format
async function createUser(request, response) {
  try {
    const user = await userService.create(request.body);
    return response.status(201).json(user);          // No standard format
  } catch (error) {
    return response.status(500).json({ error: error.message }); // Inconsistent error format
  }
}
```

**✅ Correct Pattern:**
```javascript
// Use standardized response handlers
async function createUser(request, response, next) {
  try {
    const user = await userService.create(request.body);
    return request.context.success('User created successfully', user, 201);
  } catch (error) {
    next(error);  // Let error middleware handle formatting
  }
}
```

**Why High-Impact**: Breaks response format consistency and error handling patterns.

### 7. Service Singleton Violations

**❌ Anti-Pattern:**
```javascript
// Creates multiple connections and exhausts pools
class UserService {
  constructor() {
    this.mongodb = new MongoDBService();  // Wrong! Creates new instance
    this.redis = new RedisService();      // Wrong! Bypasses singleton
  }
}

// Multiple service instances
const service1 = new UserService();  // Different MongoDB connection
const service2 = new UserService();  // Different MongoDB connection
```

**✅ Correct Pattern:**
```javascript
// Use singleton instances
class UserService {
  constructor() {
    this.mongodb = MongoDBService.getInstance();  // Reuses connection
    this.redis = RedisService.getInstance();      // Reuses connection
  }
}
```

**Why High-Impact**: Connection pool exhaustion and resource waste.

### 8. Generic Error Throwing

**❌ Anti-Pattern:**
```javascript
// Generic errors lose context and proper handling
async function createUser(userData) {
  if (!userData.email) {
    throw new Error('Email required');           // Generic error
  }
  
  if (await emailExists(userData.email)) {
    throw new Error('Email exists');             // No error code
  }
  
  throw 'Database error';                        // String, not Error object
}
```

**✅ Correct Pattern:**
```javascript
// Use AppError hierarchy for proper error handling
async function createUser(userData) {
  if (!userData.email) {
    throw new ValidationError('Email is required');
  }
  
  if (await emailExists(userData.email)) {
    throw new ConflictError('Email already registered');
  }
  
  // Proper error with context
  throw new AppError('Database operation failed', 'DB_ERROR', 500, { userData });
}
```

**Why High-Impact**: Improper error handling affects error middleware and client responses.

### 9. Business Logic in Controllers

**❌ Anti-Pattern:**
```javascript
// Controller doing business logic
async function createUser(request, response, next) {
  try {
    const { email, name } = request.body;
    
    // Business logic in controller - WRONG
    if (!email || !name) {
      return request.context.error('Validation failed', 400);
    }
    
    // More business logic - WRONG
    const existingUser = await mongodb.findOne('users', { email });
    if (existingUser) {
      return request.context.error('User exists', 409);
    }
    
    // Database operations in controller - WRONG
    const user = await mongodb.insertOne('users', {
      email: email.toLowerCase(),
      name,
      createdAt: new Date()
    });
    
    return request.context.success('User created', user, 201);
  } catch (error) {
    next(error);
  }
}
```

**✅ Correct Pattern:**
```javascript
// Controller delegates to service
async function createUser(request, response, next) {
  try {
    // Simple validation only
    const { email, name } = request.body;
    if (!email || !name) {
      return request.context.error('Email and name required', 400);
    }
    
    // Delegate business logic to service
    const user = await userService.createUser({ email, name });
    
    return request.context.success('User created successfully', user, 201);
  } catch (error) {
    next(error);  // Service errors handled by middleware
  }
}
```

**Why High-Impact**: Breaks layer separation and makes testing/maintenance difficult.

## Medium-Impact Anti-Patterns

### 10. Missing Transaction Management

**❌ Anti-Pattern:**
```javascript
// Multi-collection operations without transactions
async function createOrderWithInventory(orderData) {
  // This can leave data in inconsistent state
  const order = await mongodb.insertOne('orders', orderData);
  
  // If this fails, order is created but inventory not updated
  await mongodb.updateMany('products', 
    { id: { $in: orderData.productIds } },
    { $inc: { stock: -1 } }
  );
  
  // If this fails, order and inventory updated but no audit
  await mongodb.insertOne('audit_logs', {
    action: 'order_created',
    orderId: order.id
  });
  
  return order;
}
```

**✅ Correct Pattern:**
```javascript
// Use transactions for multi-collection operations
async function createOrderWithInventory(orderData) {
  const session = await mongodb.startTransaction();
  try {
    const order = await mongodb.insertOne('orders', orderData, { session });
    
    await mongodb.updateMany('products', 
      { id: { $in: orderData.productIds } },
      { $inc: { stock: -1 } },
      { session }
    );
    
    await mongodb.insertOne('audit_logs', {
      action: 'order_created',
      orderId: order.id
    }, { session });
    
    await mongodb.commitTransaction(session);
    return order;
  } catch (error) {
    await mongodb.abortTransaction(session);
    throw error;
  } finally {
    await mongodb.endSession(session);
  }
}
```

**Why Medium-Impact**: Data consistency issues that can cause business problems.

### 11. Synchronous Operations in Async Context

**❌ Anti-Pattern:**
```javascript
// Blocks event loop with sync operations
async function processLargeDataset(items) {
  const results = [];
  
  // Blocking synchronous loop
  for (let i = 0; i < items.length; i++) {
    const processed = processItemSync(items[i]);  // Sync operation
    results.push(processed);
  }
  
  // Blocking file operations
  const data = fs.readFileSync('large-file.json');  // Blocks event loop
  
  return results;
}
```

**✅ Correct Pattern:**
```javascript
// Non-blocking async operations
async function processLargeDataset(items) {
  const results = [];
  
  // Process items asynchronously
  for (const item of items) {
    const processed = await processItemAsync(item);  // Non-blocking
    results.push(processed);
  }
  
  // Non-blocking file operations
  const data = await fs.promises.readFile('large-file.json');
  
  return results;
}
```

**Why Medium-Impact**: Performance degradation and potential system freezing.

### 12. Missing Input Sanitization

**❌ Anti-Pattern:**
```javascript
// Using raw input without sanitization
async function createUser(request, response, next) {
  try {
    // Using raw request.body - dangerous
    const user = await userService.create(request.body);
    return request.context.success('User created', user, 201);
  } catch (error) {
    next(error);
  }
}
```

**✅ Correct Pattern:**
```javascript
// Sanitize and validate input
async function createUser(request, response, next) {
  try {
    const { email, name } = request.body;
    
    // Validate required fields
    if (!email || !name) {
      return request.context.error('Email and name required', 400);
    }
    
    // Sanitize input
    const sanitizedData = {
      email: email.toLowerCase().trim(),
      name: name.trim(),
      // Don't pass unexpected fields
    };
    
    const user = await userService.create(sanitizedData);
    return request.context.success('User created', user, 201);
  } catch (error) {
    next(error);
  }
}
```

**Why Medium-Impact**: Security vulnerabilities and data integrity issues.

## Low-Impact Anti-Patterns

### 13. Inconsistent Naming Conventions

**❌ Anti-Pattern:**
```javascript
// Mixed naming conventions
const user_service = new UserService();      // Snake_case
const UserData = { name: 'test' };          // PascalCase for data
const api_version = 'v1.0';                 // Snake_case for constant
function Get_User_By_Id() {}                 // Mixed case function

// File names
user-Service.js                              // Mixed kebab-PascalCase
UserController.js                            // PascalCase file name
```

**✅ Correct Pattern:**
```javascript
// Consistent naming conventions
const userService = new UserService();       // camelCase variables
const userData = { name: 'test' };          // camelCase data objects
const API_VERSION = 'v1.0';                 // UPPER_CASE constants
function getUserById() {}                    // camelCase functions

// File names (all kebab-case)
user-service.js
user-controller.js
```

**Why Low-Impact**: Reduces code readability but doesn't break functionality.

### 14. Missing JSDoc Documentation

**❌ Anti-Pattern:**
```javascript
// No documentation
function createUser(userData, options) {
  // Complex logic without explanation
  if (!userData.email) return null;
  return processUser(userData, options);
}
```

**✅ Correct Pattern:**
```javascript
/**
 * Creates a new user account with validation.
 * 
 * @param {Object} userData - User information
 * @param {string} userData.email - User's email address
 * @param {string} userData.name - User's full name
 * @param {Object} [options={}] - Additional options
 * @param {boolean} [options.sendWelcome=true] - Send welcome email
 * @returns {Promise<Object>} Created user object
 * @throws {ValidationError} When email is invalid
 */
async function createUser(userData, options = {}) {
  if (!userData.email) {
    throw new ValidationError('Email is required');
  }
  return processUser(userData, options);
}
```

**Why Low-Impact**: Affects maintainability but doesn't impact runtime.

## Detection and Prevention

### Automated Detection

Use these tools to catch anti-patterns:

```bash
# ESLint for code quality and patterns
npm run lint

# Pattern validation command
claude validate-patterns

# Health analysis
claude analyze-health
```

### Code Review Checklist

- [ ] All imports have .js extensions
- [ ] No CommonJS syntax (require/module.exports)
- [ ] Express v5 compliant route syntax
- [ ] Middleware chain order preserved
- [ ] Response handlers used (not direct response)
- [ ] Service singletons used correctly
- [ ] AppError hierarchy for error handling
- [ ] Business logic in service layer
- [ ] Input validation and sanitization
- [ ] Transaction management for multi-collection ops

### Prevention Strategies

1. **Use IDE/Editor Extensions**
   - ESLint integration for real-time feedback
   - Auto-import with .js extensions
   - Syntax highlighting for Express v5

2. **Pre-commit Hooks**
   - Pattern validation before commits
   - Lint checking and auto-fixing
   - Test execution requirements

3. **CI/CD Integration**
   - Pattern compliance checks
   - Anti-pattern detection in PRs
   - Automated code quality reports

4. **Team Education**
   - Regular pattern review sessions
   - Anti-pattern examples and explanations
   - Best practice sharing

## Migration from Anti-Patterns

### Step-by-Step Remediation

1. **Identify Anti-Patterns**
   ```bash
   claude validate-patterns
   ```

2. **Prioritize by Impact**
   - Fix critical anti-patterns first (system-breaking)
   - Address high-impact patterns (reliability issues)
   - Schedule medium/low-impact improvements

3. **Fix with Tests**
   - Write tests before fixing anti-patterns
   - Ensure behavior doesn't change
   - Verify fixes with integration tests

4. **Update Documentation**
   - Document pattern changes
   - Update examples and guidelines
   - Share learnings with team

## Related Documentation

- [Code Standards](./STANDARDS.md) - Complete coding standards
- [API Patterns](./api-patterns.md) - Correct API implementation patterns
- [Critical Knowledge](../lessons/CRITICAL.md) - System gotchas and must-knows
- [Error Handling Patterns](./error-handling.md) - Proper error handling
- [Testing Patterns](./testing-patterns.md) - Testing best practices