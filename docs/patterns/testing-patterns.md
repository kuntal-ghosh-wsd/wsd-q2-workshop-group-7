<!-- File: /docs/patterns/testing-patterns.md -->
<!-- Last Updated: 2024-12-05 -->
<!-- Status: current -->

# WAIF Framework Testing Patterns

## Overview

The WAIF framework uses Node.js native test runner with comprehensive unit and integration testing strategies. All tests follow consistent patterns for reliability, maintainability, and clear documentation.

## Testing Architecture

### Test Directory Structure
```
tests/
├── unit/                    # Unit tests (isolated component testing)
│   └── api/v1.0/
│       ├── controllers/     # Controller tests with mocked services
│       ├── services/        # Service tests with mocked dependencies
│       ├── middleware/      # Middleware tests with mocked req/res
│       └── utils/           # Utility function tests
├── integration/             # Integration tests (full system testing)
│   └── api/v1.0/
│       ├── routes/          # Full HTTP request/response tests
│       ├── services/        # Service tests with real databases
│       └── middleware/      # Middleware chain integration tests
├── fixtures/               # Test data and mock responses
│   └── data/               # Sample data for tests
└── helpers/                # Test utilities and common setup
    ├── api.client.js       # HTTP client for integration tests
    ├── fixtures.js         # Test data management
    └── test.cleanup.js     # Database cleanup utilities
```

### Test Execution Commands
```bash
npm test                    # Run unit tests with coverage
npm run test:integration   # Run integration tests with real services
npm run test:ci            # Run all tests in CI environment
npm run test:watch         # Watch mode for development
```

## Unit Testing Patterns

### Test File Structure
```javascript
/**
 * Standard unit test structure
 * File: tests/unit/api/v1.0/services/user.service.test.js
 */
import { describe, it, beforeEach, afterEach, mock } from 'node:test';
import assert from 'node:assert';

// Import the component being tested
import UserService from '../../../../src/api/v1.0/services/user.service.js';

// Import dependencies for mocking
import { MongoDBService } from '../../../../src/api/v1.0/services/mongodb.service.js';
import { RedisService } from '../../../../src/api/v1.0/services/redis.service.js';
import { logger } from '../../../../src/utils/logger.js';

describe('UserService', () => {
  let userService;
  let mockMongoDB;
  let mockRedis;
  
  beforeEach(() => {
    // Setup fresh mocks for each test
    mockMongoDB = {
      findOne: mock.fn(),
      insertOne: mock.fn(),
      updateOne: mock.fn(),
      deleteOne: mock.fn(),
      isConnected: mock.fn().mockReturnValue(true)
    };
    
    mockRedis = {
      get: mock.fn(),
      set: mock.fn(),
      delete: mock.fn()
    };
    
    // Mock singleton instances
    mock.method(MongoDBService, 'getInstance', () => mockMongoDB);
    mock.method(RedisService, 'getInstance', () => mockRedis);
    mock.method(logger, 'info', () => {});
    mock.method(logger, 'error', () => {});
    
    // Create service instance
    userService = new UserService();
  });
  
  afterEach(() => {
    mock.restoreAll();
  });
  
  describe('createUser', () => {
    it('should create user with valid data', async () => {
      // Arrange
      const userData = {
        email: 'test@example.com',
        name: 'Test User'
      };
      
      const expectedUser = {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        createdAt: new Date()
      };
      
      mockMongoDB.findOne.mockResolvedValue(null); // No existing user
      mockMongoDB.insertOne.mockResolvedValue(expectedUser);
      mockRedis.set.mockResolvedValue('OK');
      
      // Act
      const result = await userService.createUser(userData);
      
      // Assert
      assert.strictEqual(result.email, userData.email);
      assert.strictEqual(result.name, userData.name);
      assert.ok(result.id);
      assert.ok(result.createdAt);
      
      // Verify mocks were called correctly
      assert.strictEqual(mockMongoDB.findOne.mock.callCount(), 1);
      assert.strictEqual(mockMongoDB.insertOne.mock.callCount(), 1);
      assert.strictEqual(mockRedis.set.mock.callCount(), 1);
    });
    
    it('should throw ValidationError for missing email', async () => {
      // Arrange
      const userData = { name: 'Test User' }; // Missing email
      
      // Act & Assert
      await assert.rejects(
        async () => await userService.createUser(userData),
        {
          name: 'ValidationError',
          message: 'Email is required'
        }
      );
      
      // Verify no database calls were made
      assert.strictEqual(mockMongoDB.insertOne.mock.callCount(), 0);
    });
    
    it('should throw ConflictError for duplicate email', async () => {
      // Arrange
      const userData = {
        email: 'existing@example.com',
        name: 'Test User'
      };
      
      mockMongoDB.findOne.mockResolvedValue({ 
        email: 'existing@example.com' 
      });
      
      // Act & Assert
      await assert.rejects(
        async () => await userService.createUser(userData),
        {
          name: 'ConflictError',
          message: 'Email already registered'
        }
      );
    });
    
    it('should handle database connection errors', async () => {
      // Arrange
      const userData = {
        email: 'test@example.com',
        name: 'Test User'
      };
      
      const dbError = new Error('Connection refused');
      dbError.name = 'MongoNetworkError';
      mockMongoDB.findOne.mockRejectedValue(dbError);
      
      // Act & Assert
      await assert.rejects(
        async () => await userService.createUser(userData),
        {
          name: 'AppError',
          code: 'DB_CONNECTION_ERROR'
        }
      );
    });
  });
  
  describe('findById', () => {
    it('should return cached user when available', async () => {
      // Arrange
      const userId = 'user-123';
      const cachedUser = {
        id: userId,
        email: 'cached@example.com',
        name: 'Cached User'
      };
      
      mockRedis.get.mockResolvedValue(JSON.stringify(cachedUser));
      
      // Act
      const result = await userService.findById(userId);
      
      // Assert
      assert.deepStrictEqual(result, cachedUser);
      
      // Verify cache was checked but database wasn't queried
      assert.strictEqual(mockRedis.get.mock.callCount(), 1);
      assert.strictEqual(mockMongoDB.findOne.mock.callCount(), 0);
    });
    
    it('should query database when not cached', async () => {
      // Arrange
      const userId = 'user-123';
      const dbUser = {
        id: userId,
        email: 'db@example.com',
        name: 'DB User'
      };
      
      mockRedis.get.mockResolvedValue(null); // Not in cache
      mockMongoDB.findOne.mockResolvedValue(dbUser);
      mockRedis.set.mockResolvedValue('OK');
      
      // Act
      const result = await userService.findById(userId);
      
      // Assert
      assert.deepStrictEqual(result, dbUser);
      
      // Verify both cache and database were accessed
      assert.strictEqual(mockRedis.get.mock.callCount(), 1);
      assert.strictEqual(mockMongoDB.findOne.mock.callCount(), 1);
      assert.strictEqual(mockRedis.set.mock.callCount(), 1);
    });
  });
});
```

### Controller Testing Patterns
```javascript
/**
 * Controller testing with mocked services and request/response
 */
import { describe, it, beforeEach, mock } from 'node:test';
import assert from 'node:assert';

import UserController from '../../../../src/api/v1.0/controllers/user.controller.js';
import UserService from '../../../../src/api/v1.0/services/user.service.js';

describe('UserController', () => {
  let userController;
  let mockUserService;
  let mockRequest;
  let mockResponse;
  let mockNext;
  
  beforeEach(() => {
    // Mock service methods
    mockUserService = {
      createUser: mock.fn(),
      findById: mock.fn()
    };
    
    // Mock UserService singleton
    mock.method(UserService, 'getInstance', () => mockUserService);
    
    // Mock request context
    mockRequest = {
      body: {},
      params: {},
      context: {
        success: mock.fn(),
        error: mock.fn(),
        logger: {
          info: mock.fn(),
          error: mock.fn()
        }
      }
    };
    
    mockResponse = {};
    mockNext = mock.fn();
    
    userController = new UserController();
  });
  
  afterEach(() => {
    mock.restoreAll();
  });
  
  describe('createUser', () => {
    it('should create user and return success response', async () => {
      // Arrange
      const userData = {
        email: 'test@example.com',
        name: 'Test User'
      };
      
      const createdUser = {
        id: 'user-123',
        ...userData,
        createdAt: new Date()
      };
      
      mockRequest.body = userData;
      mockUserService.createUser.mockResolvedValue(createdUser);
      
      // Act
      await userController.createUser(mockRequest, mockResponse, mockNext);
      
      // Assert
      assert.strictEqual(mockUserService.createUser.mock.callCount(), 1);
      assert.deepStrictEqual(
        mockUserService.createUser.mock.calls[0].arguments[0],
        userData
      );
      
      // Verify success response was called
      assert.strictEqual(mockRequest.context.success.mock.callCount(), 1);
      const successCall = mockRequest.context.success.mock.calls[0].arguments;
      assert.strictEqual(successCall[0], 'User created successfully');
      assert.deepStrictEqual(successCall[1], createdUser);
      assert.strictEqual(successCall[2], 201);
      
      // Verify error handler wasn't called
      assert.strictEqual(mockNext.mock.callCount(), 0);
    });
    
    it('should return 400 for missing required fields', async () => {
      // Arrange
      mockRequest.body = { name: 'Test User' }; // Missing email
      
      // Act
      await userController.createUser(mockRequest, mockResponse, mockNext);
      
      // Assert
      assert.strictEqual(mockUserService.createUser.mock.callCount(), 0);
      
      // Verify error response was called
      assert.strictEqual(mockRequest.context.error.mock.callCount(), 1);
      const errorCall = mockRequest.context.error.mock.calls[0].arguments;
      assert.ok(errorCall[0].includes('required'));
      assert.strictEqual(errorCall[1], 400);
    });
    
    it('should handle service errors by calling next', async () => {
      // Arrange
      const userData = {
        email: 'test@example.com',
        name: 'Test User'
      };
      
      const serviceError = new Error('Database connection failed');
      mockRequest.body = userData;
      mockUserService.createUser.mockRejectedValue(serviceError);
      
      // Act
      await userController.createUser(mockRequest, mockResponse, mockNext);
      
      // Assert
      assert.strictEqual(mockNext.mock.callCount(), 1);
      assert.strictEqual(mockNext.mock.calls[0].arguments[0], serviceError);
      
      // Verify response handlers weren't called
      assert.strictEqual(mockRequest.context.success.mock.callCount(), 0);
      assert.strictEqual(mockRequest.context.error.mock.callCount(), 0);
    });
  });
});
```

### Middleware Testing Patterns
```javascript
/**
 * Middleware testing patterns
 */
import { describe, it, beforeEach, mock } from 'node:test';
import assert from 'node:assert';

import { contextMiddleware } from '../../../../src/api/v1.0/middleware/core/context.middleware.js';

describe('Context Middleware', () => {
  let mockRequest;
  let mockResponse;
  let mockNext;
  
  beforeEach(() => {
    mockRequest = {
      headers: {},
      ip: '127.0.0.1',
      method: 'GET',
      path: '/api/test'
    };
    
    mockResponse = {
      setHeader: mock.fn()
    };
    
    mockNext = mock.fn();
  });
  
  it('should generate request and correlation IDs', () => {
    // Act
    contextMiddleware(mockRequest, mockResponse, mockNext);
    
    // Assert
    assert.ok(mockRequest.context);
    assert.ok(mockRequest.context.requestId);
    assert.ok(mockRequest.context.correlationId);
    assert.strictEqual(mockRequest.context.requestId.length, 36); // UUID length
    
    // Verify response header was set
    assert.strictEqual(mockResponse.setHeader.mock.callCount(), 1);
    const setHeaderCall = mockResponse.setHeader.mock.calls[0].arguments;
    assert.strictEqual(setHeaderCall[0], 'X-Request-ID');
    assert.strictEqual(setHeaderCall[1], mockRequest.context.requestId);
    
    // Verify next was called
    assert.strictEqual(mockNext.mock.callCount(), 1);
  });
  
  it('should use provided request ID from headers', () => {
    // Arrange
    const providedId = 'custom-request-id';
    mockRequest.headers['x-request-id'] = providedId;
    
    // Act
    contextMiddleware(mockRequest, mockResponse, mockNext);
    
    // Assert
    assert.strictEqual(mockRequest.context.requestId, providedId);
  });
  
  it('should bind response handlers to context', () => {
    // Act
    contextMiddleware(mockRequest, mockResponse, mockNext);
    
    // Assert
    assert.ok(mockRequest.context.success);
    assert.ok(mockRequest.context.error);
    assert.ok(mockRequest.context.paginated);
    assert.strictEqual(typeof mockRequest.context.success, 'function');
    assert.strictEqual(typeof mockRequest.context.error, 'function');
    assert.strictEqual(typeof mockRequest.context.paginated, 'function');
  });
});
```

## Integration Testing Patterns

### API Integration Tests
```javascript
/**
 * Full API integration testing
 * File: tests/integration/api/v1.0/routes/user.routes.integration.test.js
 */
import { describe, it, before, after, beforeEach } from 'node:test';
import assert from 'node:assert';
import request from 'supertest';

import app from '../../../../../src/app.js';
import { MongoDBService } from '../../../../../src/api/v1.0/services/mongodb.service.js';
import { testCleanup } from '../../../helpers/test.cleanup.js';

describe('User Routes Integration', () => {
  let mongodb;
  
  before(async () => {
    // Connect to test database
    mongodb = MongoDBService.getInstance();
    await mongodb.connect();
  });
  
  after(async () => {
    // Cleanup after all tests
    await testCleanup.clearAllCollections();
    await mongodb.disconnect();
  });
  
  beforeEach(async () => {
    // Clear data before each test
    await testCleanup.clearCollection('users');
  });
  
  describe('POST /api/users', () => {
    it('should create user with valid data', async () => {
      // Arrange
      const userData = {
        email: 'integration@example.com',
        name: 'Integration Test User'
      };
      
      // Act
      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(201);
      
      // Assert response format
      assert.strictEqual(response.body.status, 'success');
      assert.strictEqual(response.body.message, 'User created successfully');
      assert.ok(response.body.data);
      assert.strictEqual(response.body.data.email, userData.email);
      assert.strictEqual(response.body.data.name, userData.name);
      assert.ok(response.body.data.id);
      assert.ok(response.body.data.createdAt);
      
      // Verify user was actually saved to database
      const savedUser = await mongodb.findOne('users', {
        email: userData.email
      });
      assert.ok(savedUser);
      assert.strictEqual(savedUser.email, userData.email);
    });
    
    it('should return 400 for missing email', async () => {
      // Arrange
      const invalidData = { name: 'Test User' }; // Missing email
      
      // Act
      const response = await request(app)
        .post('/api/users')
        .send(invalidData)
        .expect(400);
      
      // Assert error response format
      assert.strictEqual(response.body.status, 'error');
      assert.ok(response.body.message.includes('required'));
      assert.strictEqual(response.body.statusCode, 400);
      assert.ok(response.body.requestId);
      
      // Verify no user was created
      const userCount = await mongodb.countDocuments('users', {});
      assert.strictEqual(userCount, 0);
    });
    
    it('should return 409 for duplicate email', async () => {
      // Arrange - create initial user
      const userData = {
        email: 'duplicate@example.com',
        name: 'First User'
      };
      
      await request(app)
        .post('/api/users')
        .send(userData)
        .expect(201);
      
      // Act - try to create duplicate
      const duplicateData = {
        email: 'duplicate@example.com',
        name: 'Second User'
      };
      
      const response = await request(app)
        .post('/api/users')
        .send(duplicateData)
        .expect(409);
      
      // Assert
      assert.strictEqual(response.body.status, 'error');
      assert.ok(response.body.message.includes('already'));
      assert.strictEqual(response.body.statusCode, 409);
      
      // Verify only one user exists
      const userCount = await mongodb.countDocuments('users', {
        email: userData.email
      });
      assert.strictEqual(userCount, 1);
    });
    
    it('should require API version header', async () => {
      // Arrange
      const userData = {
        email: 'version@example.com',
        name: 'Version Test'
      };
      
      // Act - request without version header
      const response = await request(app)
        .post('/api/users')
        .send(userData)
        .expect(400);
      
      // Assert
      assert.strictEqual(response.body.status, 'error');
      assert.ok(response.body.message.includes('version'));
    });
  });
  
  describe('GET /api/users/:id', () => {
    it('should retrieve user by ID', async () => {
      // Arrange - create user first
      const createResponse = await request(app)
        .post('/api/users')
        .send({
          email: 'retrieve@example.com',
          name: 'Retrieve Test'
        })
        .expect(201);
      
      const userId = createResponse.body.data.id;
      
      // Act
      const response = await request(app)
        .get(`/api/users/${userId}`)
        .expect(200);
      
      // Assert
      assert.strictEqual(response.body.status, 'success');
      assert.strictEqual(response.body.data.id, userId);
      assert.strictEqual(response.body.data.email, 'retrieve@example.com');
    });
    
    it('should return 404 for non-existent user', async () => {
      // Act
      const response = await request(app)
        .get('/api/users/non-existent-id')
        .expect(404);
      
      // Assert
      assert.strictEqual(response.body.status, 'error');
      assert.strictEqual(response.body.statusCode, 404);
    });
  });
});
```

### Service Integration Tests
```javascript
/**
 * Service integration testing with real database
 */
import { describe, it, before, after, beforeEach } from 'node:test';
import assert from 'node:assert';

import { MongoDBService } from '../../../../src/api/v1.0/services/mongodb.service.js';
import { RedisService } from '../../../../src/api/v1.0/services/redis.service.js';
import { testCleanup } from '../../helpers/test.cleanup.js';

describe('MongoDB Service Integration', () => {
  let mongodb;
  
  before(async () => {
    mongodb = MongoDBService.getInstance();
    await mongodb.connect();
  });
  
  after(async () => {
    await testCleanup.clearAllCollections();
    await mongodb.disconnect();
  });
  
  beforeEach(async () => {
    await testCleanup.clearCollection('test_users');
  });
  
  describe('CRUD operations', () => {
    it('should insert and retrieve document', async () => {
      // Arrange
      const testDoc = {
        name: 'Integration Test',
        email: 'integration@test.com',
        createdAt: new Date()
      };
      
      // Act - Insert
      const inserted = await mongodb.insertOne('test_users', testDoc);
      
      // Assert insert result
      assert.ok(inserted._id);
      assert.strictEqual(inserted.name, testDoc.name);
      
      // Act - Retrieve
      const retrieved = await mongodb.findOne('test_users', {
        name: testDoc.name
      });
      
      // Assert retrieve result
      assert.ok(retrieved);
      assert.strictEqual(retrieved.name, testDoc.name);
      assert.strictEqual(retrieved.email, testDoc.email);
    });
    
    it('should handle transactions correctly', async () => {
      // Arrange
      const doc1 = { name: 'Transaction Test 1' };
      const doc2 = { name: 'Transaction Test 2' };
      
      // Act - Transaction that should succeed
      const session = await mongodb.startTransaction();
      try {
        await mongodb.insertOne('test_users', doc1, { session });
        await mongodb.insertOne('test_users', doc2, { session });
        await mongodb.commitTransaction(session);
      } finally {
        await mongodb.endSession(session);
      }
      
      // Assert - Both documents should exist
      const count = await mongodb.countDocuments('test_users', {
        name: { $in: ['Transaction Test 1', 'Transaction Test 2'] }
      });
      assert.strictEqual(count, 2);
    });
    
    it('should rollback failed transactions', async () => {
      // Arrange
      const doc1 = { name: 'Rollback Test 1' };
      const doc2 = { name: 'Rollback Test 2' };
      
      // Act - Transaction that should fail
      const session = await mongodb.startTransaction();
      try {
        await mongodb.insertOne('test_users', doc1, { session });
        
        // Simulate error
        throw new Error('Simulated transaction error');
        
        await mongodb.insertOne('test_users', doc2, { session });
        await mongodb.commitTransaction(session);
      } catch (error) {
        await mongodb.abortTransaction(session);
      } finally {
        await mongodb.endSession(session);
      }
      
      // Assert - No documents should exist
      const count = await mongodb.countDocuments('test_users', {
        name: { $in: ['Rollback Test 1', 'Rollback Test 2'] }
      });
      assert.strictEqual(count, 0);
    });
  });
});
```

## Test Data Management

### Fixtures and Test Data
```javascript
/**
 * Test fixtures for consistent test data
 * File: tests/fixtures/fixtures.js
 */

export const userFixtures = {
  validUser: {
    email: 'valid@example.com',
    name: 'Valid User',
    status: 'active'
  },
  
  invalidUser: {
    // Missing required email field
    name: 'Invalid User'
  },
  
  existingUser: {
    id: 'existing-user-id',
    email: 'existing@example.com',
    name: 'Existing User',
    createdAt: new Date('2024-01-01T00:00:00Z')
  },
  
  multipleUsers: [
    {
      email: 'user1@example.com',
      name: 'User One'
    },
    {
      email: 'user2@example.com',
      name: 'User Two'
    },
    {
      email: 'user3@example.com',
      name: 'User Three'
    }
  ]
};

export const apiResponses = {
  successResponse: {
    status: 'success',
    message: 'Operation completed successfully',
    data: {}
  },
  
  errorResponse: {
    status: 'error',
    message: 'Operation failed',
    statusCode: 400,
    requestId: 'test-request-id'
  },
  
  paginatedResponse: {
    status: 'success',
    message: 'Data retrieved successfully',
    data: [],
    meta: {
      pagination: {
        page: 1,
        limit: 10,
        total: 0,
        pages: 0
      }
    }
  }
};
```

### Test Cleanup Utilities
```javascript
/**
 * Test cleanup utilities
 * File: tests/helpers/test.cleanup.js
 */
import { MongoDBService } from '../../src/api/v1.0/services/mongodb.service.js';
import { RedisService } from '../../src/api/v1.0/services/redis.service.js';

class TestCleanup {
  constructor() {
    this.mongodb = MongoDBService.getInstance();
    this.redis = RedisService.getInstance();
  }
  
  async clearCollection(collectionName) {
    try {
      await this.mongodb.deleteMany(collectionName, {});
    } catch (error) {
      console.warn(`Failed to clear collection ${collectionName}:`, error.message);
    }
  }
  
  async clearAllCollections() {
    const collections = ['users', 'test_users', 'orders', 'products'];
    
    for (const collection of collections) {
      await this.clearCollection(collection);
    }
  }
  
  async clearRedisCache(keyPattern = '*') {
    try {
      const keys = await this.redis.keys(keyPattern);
      if (keys.length > 0) {
        await this.redis.del(...keys);
      }
    } catch (error) {
      console.warn('Failed to clear Redis cache:', error.message);
    }
  }
  
  async seedTestData(collection, data) {
    try {
      if (Array.isArray(data)) {
        await this.mongodb.insertMany(collection, data);
      } else {
        await this.mongodb.insertOne(collection, data);
      }
    } catch (error) {
      console.error(`Failed to seed test data in ${collection}:`, error.message);
      throw error;
    }
  }
}

export const testCleanup = new TestCleanup();
```

## Testing Best Practices

### Test Organization
1. **Group by Component**: Tests mirror the source code structure
2. **Descriptive Names**: Test names describe behavior being tested
3. **Arrange-Act-Assert**: Clear separation of test phases
4. **One Assertion per Test**: Focus on single behavior
5. **Isolated Tests**: Each test is independent

### Mock Strategy
1. **Mock External Dependencies**: Database, Redis, external APIs
2. **Use Real Objects**: For unit under test and its direct dependencies
3. **Verify Interactions**: Check that mocks were called correctly
4. **Reset Mocks**: Clean state between tests

### Error Testing
1. **Test All Error Paths**: Validation, business logic, infrastructure
2. **Verify Error Types**: Specific error classes and codes
3. **Check Error Handling**: Proper logging and response formatting
4. **Test Edge Cases**: Boundary conditions and unusual inputs

### Performance Testing
1. **Measure Response Times**: For critical API endpoints
2. **Test Under Load**: Concurrent requests and high volume
3. **Memory Usage**: Monitor for memory leaks
4. **Database Performance**: Query execution times

## Coverage Requirements

### Minimum Coverage Thresholds
- **Overall Coverage**: 80%
- **Statement Coverage**: 85%
- **Branch Coverage**: 75%
- **Function Coverage**: 90%

### Coverage Analysis
```bash
# Generate coverage report
npm test

# View detailed HTML coverage report
open coverage/index.html

# Check coverage thresholds
npm run coverage:check
```

### Excluded from Coverage
- Configuration files
- Database migration scripts
- Development utilities
- External library wrappers

## Continuous Integration

### Test Execution in CI
```yaml
# GitHub Actions example
- name: Run Unit Tests
  run: npm test

- name: Run Integration Tests
  run: |
    docker-compose up -d waif-mongodb waif-redis
    npm run test:integration
  
- name: Upload Coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage/lcov.info
```

### Quality Gates
- All tests must pass before merge
- Coverage must meet minimum thresholds
- No new lint violations
- Integration tests must pass with real services

## Related Documentation

- [Code Standards](./STANDARDS.md) - Coding conventions and requirements
- [API Patterns](./api-patterns.md) - API implementation guidance
- [Error Handling](./error-handling.md) - Error handling strategies
- [Anti-patterns](./anti-patterns.md) - Common mistakes to avoid