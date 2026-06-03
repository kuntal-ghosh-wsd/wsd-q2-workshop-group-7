<!-- File: /docs/patterns/error-handling.md -->
<!-- Last Updated: 2024-12-05 -->
<!-- Status: current -->

# WAIF Framework Error Handling Patterns

## Overview

The WAIF framework implements a comprehensive error handling system that distinguishes between operational and programmer errors, provides consistent error responses, and maintains detailed error context for debugging and monitoring.

## Error Hierarchy

### AppError Base Class

All application errors MUST extend the `AppError` base class:

```javascript
// Located: src/utils/errors.js
class AppError extends Error {
  constructor(message, code = 'INTERNAL_ERROR', statusCode = 500, data = null) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.statusCode = statusCode;
    this.data = data;
    this.isOperational = true;  // Key flag for error middleware
    this.timestamp = new Date().toISOString();
    
    Error.captureStackTrace(this, this.constructor);
  }
}
```

### Specific Error Types

#### ValidationError (400 Bad Request)
```javascript
class ValidationError extends AppError {
  constructor(message, data = null) {
    super(message, 'VALIDATION_ERROR', 400, data);
  }
}

// Usage examples
throw new ValidationError('Email is required');
throw new ValidationError('Invalid email format', { field: 'email' });
throw new ValidationError('Multiple validation errors', { 
  errors: ['Name too short', 'Invalid phone number'] 
});
```

#### ConflictError (409 Conflict)
```javascript
class ConflictError extends AppError {
  constructor(message, data = null) {
    super(message, 'CONFLICT_ERROR', 409, data);
  }
}

// Usage examples
throw new ConflictError('Email already exists');
throw new ConflictError('Resource locked by another process', { 
  resourceId: 'user-123',
  lockedBy: 'process-456' 
});
```

#### NotFoundError (404 Not Found)
```javascript
class NotFoundError extends AppError {
  constructor(message, data = null) {
    super(message, 'NOT_FOUND', 404, data);
  }
}

// Usage examples
throw new NotFoundError('User not found');
throw new NotFoundError('Resource not found', { 
  resourceType: 'user',
  resourceId: 'user-123' 
});
```

#### AuthenticationError (401 Unauthorized)
```javascript
class AuthenticationError extends AppError {
  constructor(message, data = null) {
    super(message, 'AUTHENTICATION_ERROR', 401, data);
  }
}

// Usage examples
throw new AuthenticationError('Authentication required');
throw new AuthenticationError('Invalid token', { tokenType: 'JWT' });
```

#### AuthorizationError (403 Forbidden)
```javascript
class AuthorizationError extends AppError {
  constructor(message, data = null) {
    super(message, 'AUTHORIZATION_ERROR', 403, data);
  }
}

// Usage examples
throw new AuthorizationError('Insufficient permissions');
throw new AuthorizationError('Access denied to resource', { 
  requiredRole: 'admin',
  userRole: 'user' 
});
```

## Error Handling Patterns

### Controller Error Handling

Controllers should handle **expected errors** directly and delegate **unexpected errors** to error middleware:

```javascript
/**
 * Standard controller error handling pattern
 */
class UserController {
  async createUser(request, response, next) {
    try {
      // Input validation - handle expected validation errors
      const { email, name } = request.body;
      if (!email || !name) {
        return request.context.error(
          'Email and name are required',
          400,
          'VALIDATION_ERROR'
        );
      }
      
      // Delegate to service layer
      const user = await userService.createUser({ email, name });
      
      return request.context.success(
        'User created successfully',
        user,
        201
      );
      
    } catch (error) {
      // Handle specific expected errors
      if (error instanceof ConflictError) {
        return request.context.error(
          error.message,
          error.statusCode,
          error.code
        );
      }
      
      if (error instanceof ValidationError) {
        return request.context.error(
          error.message,
          error.statusCode,
          error.code
        );
      }
      
      // Let error middleware handle unexpected errors
      next(error);
    }
  }
  
  async getUserById(request, response, next) {
    try {
      const { id } = request.params;
      
      // Simple validation
      if (!id) {
        return request.context.error('User ID is required', 400);
      }
      
      const user = await userService.findById(id);
      
      if (!user) {
        return request.context.error('User not found', 404);
      }
      
      return request.context.success(
        'User retrieved successfully',
        user
      );
      
    } catch (error) {
      // All unexpected errors go to error middleware
      next(error);
    }
  }
}
```

### Service Layer Error Handling

Services should focus on **business logic errors** and throw **appropriate AppError types**:

```javascript
/**
 * Service layer error handling pattern
 */
class UserService {
  constructor() {
    this.mongodb = MongoDBService.getInstance();
    this.redis = RedisService.getInstance();
  }
  
  async createUser(userData) {
    try {
      // Business validation
      await this.validateUserData(userData);
      
      // Transform data
      const userToCreate = {
        ...userData,
        id: this.generateUserId(),
        email: userData.email.toLowerCase(),
        createdAt: new Date(),
        status: 'active'
      };
      
      // Database operation
      const createdUser = await this.mongodb.insertOne('users', userToCreate);
      
      // Cache the user
      await this.cacheUser(createdUser);
      
      logger.info('User created successfully', {
        userId: createdUser.id,
        email: createdUser.email
      });
      
      return this.sanitizeUserData(createdUser);
      
    } catch (error) {
      // Handle database-specific errors
      if (error.code === 11000) {  // MongoDB duplicate key
        throw new ConflictError('Email already exists', {
          field: 'email',
          value: userData.email
        });
      }
      
      // Handle connection errors
      if (error.name === 'MongoNetworkError') {
        logger.error('Database connection error', {
          error: error.message,
          operation: 'createUser'
        });
        throw new AppError(
          'Database connection failed',
          'DB_CONNECTION_ERROR',
          503,
          { retryable: true }
        );
      }
      
      // Re-throw AppErrors without modification
      if (error instanceof AppError) {
        throw error;
      }
      
      // Wrap unexpected errors
      logger.error('Unexpected error in createUser', {
        error: error.message,
        stack: error.stack,
        userData: { email: userData.email } // Don't log sensitive data
      });
      
      throw new AppError(
        'User creation failed',
        'USER_CREATION_ERROR',
        500,
        { originalError: error.message }
      );
    }
  }
  
  async validateUserData(userData) {
    const errors = [];
    
    // Required field validation
    if (!userData.email) {
      errors.push('Email is required');
    }
    
    if (!userData.name) {
      errors.push('Name is required');
    }
    
    // Format validation
    if (userData.email && !this.isValidEmail(userData.email)) {
      errors.push('Invalid email format');
    }
    
    if (userData.name && userData.name.length < 2) {
      errors.push('Name must be at least 2 characters');
    }
    
    // Business rule validation
    if (userData.email && await this.emailExists(userData.email)) {
      throw new ConflictError('Email already registered');
    }
    
    if (errors.length > 0) {
      throw new ValidationError(
        errors.length === 1 ? errors[0] : 'Multiple validation errors',
        { errors }
      );
    }
  }
  
  async findById(id) {
    try {
      if (!id) {
        throw new ValidationError('User ID is required');
      }
      
      // Check cache first
      const cachedUser = await this.getCachedUser(id);
      if (cachedUser) {
        return cachedUser;
      }
      
      // Query database
      const user = await this.mongodb.findOne('users', { id });
      
      if (user) {
        await this.cacheUser(user);
        return this.sanitizeUserData(user);
      }
      
      return null;
      
    } catch (error) {
      if (error instanceof AppError) {
        throw error;
      }
      
      logger.error('Error finding user by ID', {
        error: error.message,
        userId: id
      });
      
      throw new AppError(
        'Failed to retrieve user',
        'USER_RETRIEVAL_ERROR',
        500
      );
    }
  }
}
```

### Middleware Error Handling

The error middleware handles all **unexpected errors** and formats responses consistently:

```javascript
/**
 * Global error handling middleware
 * Located: src/api/v1.0/middleware/core/error.middleware.js
 */
export function errorMiddleware(error, request, response, next) {
  // Get logger from context or use global logger
  const logger = request.context?.logger || globalLogger;
  
  // Log error with full context
  const logContext = {
    error: error.message,
    stack: error.stack,
    requestId: request.context?.requestId,
    correlationId: request.context?.correlationId,
    method: request.method,
    url: request.url,
    userAgent: request.headers['user-agent'],
    ip: request.ip
  };
  
  // Add request body for debugging (but sanitize sensitive data)
  if (request.body) {
    logContext.requestBody = sanitizeRequestBody(request.body);
  }
  
  // Log based on error type and environment
  if (error.isOperational) {
    // Operational errors - log as info or warn
    if (error.statusCode >= 500) {
      logger.error('Operational error', logContext);
    } else {
      logger.warn('Client error', logContext);
    }
  } else {
    // Programmer errors - always log as error
    logger.error('Programmer error', logContext);
  }
  
  // Format error response
  const errorResponse = {
    status: 'error',
    message: getErrorMessage(error, process.env.NODE_ENV),
    statusCode: getStatusCode(error),
    requestId: request.context?.requestId
  };
  
  // Add error code for operational errors
  if (error.isOperational && error.code) {
    errorResponse.code = error.code;
  }
  
  // Add timestamp
  errorResponse.timestamp = new Date().toISOString();
  
  // Add debug info in development
  if (process.env.NODE_ENV === 'development' && !error.isOperational) {
    errorResponse.stack = error.stack;
    errorResponse.details = error.data;
  }
  
  return response.status(errorResponse.statusCode).json(errorResponse);
}

function getErrorMessage(error, environment) {
  // For operational errors, show the actual message
  if (error.isOperational) {
    return error.message;
  }
  
  // For programmer errors, show generic message in production
  if (environment === 'production') {
    return 'Internal server error';
  }
  
  // In development, show actual error message
  return error.message;
}

function getStatusCode(error) {
  if (error.statusCode && error.statusCode >= 400 && error.statusCode < 600) {
    return error.statusCode;
  }
  return 500;
}

function sanitizeRequestBody(body) {
  const sanitized = { ...body };
  
  // Remove sensitive fields
  const sensitiveFields = ['password', 'token', 'secret', 'key', 'auth'];
  
  for (const field of sensitiveFields) {
    if (field in sanitized) {
      sanitized[field] = '[REDACTED]';
    }
  }
  
  return sanitized;
}
```

## Database Error Handling

### MongoDB Error Patterns

```javascript
/**
 * Handle MongoDB-specific errors
 */
class MongoDBService {
  async insertOne(collection, document, options = {}) {
    try {
      const result = await this.db.collection(collection).insertOne(document, options);
      return result.ops[0];
    } catch (error) {
      // Handle specific MongoDB errors
      if (error.code === 11000) {  // Duplicate key error
        const field = this.extractDuplicateField(error);
        throw new ConflictError(`Duplicate ${field}`, {
          field,
          code: error.code
        });
      }
      
      if (error.name === 'MongoNetworkError') {
        throw new AppError(
          'Database connection failed',
          'DB_CONNECTION_ERROR',
          503,
          { retryable: true }
        );
      }
      
      if (error.name === 'MongoTimeoutError') {
        throw new AppError(
          'Database operation timeout',
          'DB_TIMEOUT_ERROR',
          504,
          { retryable: true }
        );
      }
      
      // Validation errors from MongoDB schema
      if (error.name === 'ValidationError') {
        throw new ValidationError('Document validation failed', {
          details: error.errors
        });
      }
      
      // Generic database error
      logger.error('MongoDB operation failed', {
        error: error.message,
        collection,
        operation: 'insertOne'
      });
      
      throw new AppError(
        'Database operation failed',
        'DB_OPERATION_ERROR',
        500,
        { collection, operation: 'insertOne' }
      );
    }
  }
  
  extractDuplicateField(error) {
    // Extract field name from duplicate key error message
    const match = error.message.match(/index: (\w+)/);
    return match ? match[1] : 'key';
  }
}
```

### Redis Error Patterns

```javascript
/**
 * Handle Redis-specific errors
 */
class RedisService {
  async get(key) {
    try {
      const value = await this.client.get(this.getKeyWithPrefix(key));
      return value ? JSON.parse(value) : null;
    } catch (error) {
      if (error.code === 'ECONNREFUSED') {
        logger.warn('Redis connection refused, falling back to null', {
          key,
          error: error.message
        });
        return null;  // Graceful degradation
      }
      
      if (error.code === 'ETIMEDOUT') {
        logger.warn('Redis timeout, falling back to null', {
          key,
          error: error.message
        });
        return null;  // Graceful degradation
      }
      
      // JSON parsing errors
      if (error.name === 'SyntaxError') {
        logger.error('Redis data corruption detected', {
          key,
          error: error.message
        });
        // Delete corrupted data and return null
        await this.delete(key).catch(() => {}); // Ignore delete errors
        return null;
      }
      
      // Other Redis errors
      logger.error('Redis operation failed', {
        error: error.message,
        key,
        operation: 'get'
      });
      
      throw new AppError(
        'Cache operation failed',
        'CACHE_ERROR',
        500,
        { key, operation: 'get' }
      );
    }
  }
}
```

## Transaction Error Handling

```javascript
/**
 * Handle transaction errors properly
 */
class OrderService {
  async createOrderWithInventory(orderData) {
    const session = await mongodb.startTransaction();
    
    try {
      // Step 1: Create order
      const order = await mongodb.insertOne('orders', {
        ...orderData,
        id: generateOrderId(),
        status: 'pending',
        createdAt: new Date()
      }, { session });
      
      // Step 2: Update inventory
      const inventoryUpdate = await mongodb.updateMany('products',
        { id: { $in: orderData.productIds } },
        { $inc: { stock: -1 } },
        { session }
      );
      
      // Business validation
      if (inventoryUpdate.modifiedCount !== orderData.productIds.length) {
        throw new ValidationError('Some products are out of stock', {
          requestedProducts: orderData.productIds.length,
          updatedProducts: inventoryUpdate.modifiedCount
        });
      }
      
      // Step 3: Create audit log
      await mongodb.insertOne('audit_logs', {
        action: 'order_created',
        orderId: order.id,
        userId: orderData.userId,
        timestamp: new Date()
      }, { session });
      
      // Commit transaction
      await mongodb.commitTransaction(session);
      
      logger.info('Order created successfully with inventory update', {
        orderId: order.id,
        productCount: orderData.productIds.length
      });
      
      return order;
      
    } catch (error) {
      // Rollback transaction
      await mongodb.abortTransaction(session);
      
      // Handle specific transaction errors
      if (error.hasErrorLabel && error.hasErrorLabel('TransientTransactionError')) {
        logger.warn('Transient transaction error, could retry', {
          error: error.message,
          orderData: { userId: orderData.userId }
        });
        throw new AppError(
          'Transaction failed, please try again',
          'TRANSACTION_RETRY',
          503,
          { retryable: true }
        );
      }
      
      if (error.hasErrorLabel && error.hasErrorLabel('UnknownTransactionCommitResult')) {
        logger.error('Unknown transaction commit result', {
          error: error.message,
          orderData: { userId: orderData.userId }
        });
        throw new AppError(
          'Order processing uncertain, please contact support',
          'TRANSACTION_UNCERTAIN',
          500,
          { requiresManualCheck: true }
        );
      }
      
      // Re-throw AppErrors
      if (error instanceof AppError) {
        throw error;
      }
      
      // Handle unexpected transaction errors
      logger.error('Transaction failed unexpectedly', {
        error: error.message,
        stack: error.stack,
        orderData: { userId: orderData.userId }
      });
      
      throw new AppError(
        'Order creation failed',
        'ORDER_CREATION_ERROR',
        500
      );
      
    } finally {
      // Always end the session
      await mongodb.endSession(session);
    }
  }
}
```

## Async Error Handling Patterns

### Promise Error Handling

```javascript
/**
 * Proper async error handling patterns
 */

// ✅ Correct: Using async/await with try/catch
async function processUserData(userId) {
  try {
    const user = await userService.findById(userId);
    const profile = await profileService.getProfile(user.id);
    const settings = await settingsService.getSettings(user.id);
    
    return { user, profile, settings };
  } catch (error) {
    logger.error('Failed to process user data', {
      error: error.message,
      userId
    });
    throw error;  // Re-throw for caller to handle
  }
}

// ✅ Correct: Handling multiple async operations
async function processMultipleUsers(userIds) {
  const results = [];
  const errors = [];
  
  for (const userId of userIds) {
    try {
      const userData = await processUserData(userId);
      results.push(userData);
    } catch (error) {
      errors.push({ userId, error: error.message });
      // Continue processing other users
    }
  }
  
  if (errors.length > 0) {
    logger.warn('Some users failed to process', { errors });
  }
  
  return { results, errors };
}

// ❌ Wrong: Unhandled promise rejection
async function badAsyncPattern() {
  processUserData('user-123');  // Missing await and error handling
  return 'done';
}

// ✅ Correct: Handling promise rejections in parallel operations
async function processUsersInParallel(userIds) {
  const promises = userIds.map(async (userId) => {
    try {
      return await processUserData(userId);
    } catch (error) {
      logger.error('User processing failed', { userId, error: error.message });
      return null;  // Return null for failed users
    }
  });
  
  const results = await Promise.all(promises);
  return results.filter(result => result !== null);
}
```

### Event Emitter Error Handling

```javascript
/**
 * Handle errors in event-driven code
 */
class DataProcessor extends EventEmitter {
  constructor() {
    super();
    
    // Always handle error events
    this.on('error', (error) => {
      logger.error('Data processor error', {
        error: error.message,
        stack: error.stack
      });
    });
  }
  
  async processData(data) {
    try {
      const processed = await this.transform(data);
      this.emit('data', processed);
    } catch (error) {
      this.emit('error', error);  // Emit error event
    }
  }
  
  async transform(data) {
    // Transformation logic that might throw
    if (!data || typeof data !== 'object') {
      throw new ValidationError('Invalid data format');
    }
    
    return { ...data, processed: true, timestamp: new Date() };
  }
}

// Usage with proper error handling
const processor = new DataProcessor();

processor.on('data', (processed) => {
  logger.info('Data processed successfully', { processed });
});

processor.on('error', (error) => {
  if (error instanceof ValidationError) {
    // Handle validation errors
    logger.warn('Data validation failed', { error: error.message });
  } else {
    // Handle unexpected errors
    logger.error('Data processing error', { error: error.message });
  }
});
```

## Error Response Formats

### Standard Error Response

All error responses follow this format:

```json
{
  "status": "error",
  "message": "Human-readable error description",
  "statusCode": 400,
  "code": "VALIDATION_ERROR",
  "requestId": "b47ac10b-58cc-4372-a567-0e02b2c3d479",
  "timestamp": "2024-12-05T10:30:00.000Z"
}
```

### Validation Error with Details

```json
{
  "status": "error",
  "message": "Multiple validation errors",
  "statusCode": 400,
  "code": "VALIDATION_ERROR",
  "requestId": "uuid",
  "timestamp": "2024-12-05T10:30:00.000Z",
  "details": {
    "errors": [
      "Email is required",
      "Password must be at least 8 characters"
    ]
  }
}
```

### Development vs Production Responses

```javascript
// Development environment - detailed error info
{
  "status": "error",
  "message": "Database connection failed",
  "statusCode": 500,
  "code": "DB_CONNECTION_ERROR",
  "requestId": "uuid",
  "timestamp": "2024-12-05T10:30:00.000Z",
  "stack": "Error: connect ECONNREFUSED 127.0.0.1:27017\n    at TCPConnectWrap.afterConnect...",
  "details": {
    "host": "localhost",
    "port": 27017
  }
}

// Production environment - sanitized error info
{
  "status": "error",
  "message": "Internal server error",
  "statusCode": 500,
  "requestId": "uuid",
  "timestamp": "2024-12-05T10:30:00.000Z"
}
```

## Logging and Monitoring

### Error Logging Patterns

```javascript
// Structured error logging
logger.error('Database operation failed', {
  error: error.message,
  stack: error.stack,
  operation: 'insertUser',
  collection: 'users',
  requestId: request.context.requestId,
  userId: request.user?.id,
  duration: Date.now() - startTime
});

// Business error logging
logger.warn('User registration failed due to duplicate email', {
  email: userData.email,
  requestId: request.context.requestId,
  ipAddress: request.ip
});

// Security-related error logging
logger.security('Authentication attempt failed', {
  email: loginData.email,
  ipAddress: request.ip,
  userAgent: request.headers['user-agent'],
  reason: 'invalid_credentials'
});
```

### Error Metrics and Monitoring

```javascript
// Increment error counters for monitoring
const errorMetrics = {
  totalErrors: 0,
  errorsByType: {},
  errorsByStatusCode: {},
  errorsByEndpoint: {}
};

function trackError(error, request) {
  errorMetrics.totalErrors++;
  
  const errorType = error.constructor.name;
  errorMetrics.errorsByType[errorType] = (errorMetrics.errorsByType[errorType] || 0) + 1;
  
  const statusCode = error.statusCode || 500;
  errorMetrics.errorsByStatusCode[statusCode] = (errorMetrics.errorsByStatusCode[statusCode] || 0) + 1;
  
  const endpoint = `${request.method} ${request.path}`;
  errorMetrics.errorsByEndpoint[endpoint] = (errorMetrics.errorsByEndpoint[endpoint] || 0) + 1;
}
```

## Testing Error Scenarios

### Unit Testing Error Handling

```javascript
describe('UserService', () => {
  describe('createUser', () => {
    it('should throw ValidationError for missing email', async () => {
      const userData = { name: 'John Doe' };  // Missing email
      
      await assert.rejects(
        async () => await userService.createUser(userData),
        {
          name: 'ValidationError',
          message: 'Email is required'
        }
      );
    });
    
    it('should throw ConflictError for duplicate email', async () => {
      // Setup
      mockMongoDB.findOne.resolves({ email: 'existing@example.com' });
      
      const userData = { email: 'existing@example.com', name: 'John' };
      
      await assert.rejects(
        async () => await userService.createUser(userData),
        {
          name: 'ConflictError',
          message: 'Email already registered'
        }
      );
    });
    
    it('should handle database connection errors', async () => {
      // Setup
      const dbError = new Error('Connection refused');
      dbError.name = 'MongoNetworkError';
      mockMongoDB.insertOne.rejects(dbError);
      
      const userData = { email: 'test@example.com', name: 'John' };
      
      await assert.rejects(
        async () => await userService.createUser(userData),
        {
          name: 'AppError',
          code: 'DB_CONNECTION_ERROR',
          statusCode: 503
        }
      );
    });
  });
});
```

### Integration Testing Error Scenarios

```javascript
describe('User API Integration', () => {
  it('should return 400 for validation errors', async () => {
    const response = await request(app)
      .post('/api/users')
      .send({ name: 'John' })  // Missing email
      .expect(400);
    
    assert.strictEqual(response.body.status, 'error');
    assert.strictEqual(response.body.code, 'VALIDATION_ERROR');
    assert.ok(response.body.requestId);
  });
  
  it('should return 409 for duplicate email', async () => {
    // Create user first
    await request(app)
      .post('/api/users')
      .send({ email: 'test@example.com', name: 'John' })
      .expect(201);
    
    // Try to create duplicate
    const response = await request(app)
      .post('/api/users')
      .send({ email: 'test@example.com', name: 'Jane' })
      .expect(409);
    
    assert.strictEqual(response.body.status, 'error');
    assert.strictEqual(response.body.code, 'CONFLICT_ERROR');
  });
});
```

## Related Documentation

- [API Patterns](./api-patterns.md) - API implementation patterns
- [Anti-patterns](./anti-patterns.md) - Common mistakes to avoid
- [Code Standards](./STANDARDS.md) - Complete coding standards
- [Critical Knowledge](../lessons/CRITICAL.md) - System gotchas
- [Testing Patterns](./testing-patterns.md) - Testing approaches