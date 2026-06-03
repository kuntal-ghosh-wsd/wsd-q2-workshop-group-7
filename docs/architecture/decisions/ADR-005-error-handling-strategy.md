# ADR-005: Error Handling Strategy

## Status
**Accepted** - 2024-12-05

## Context

Consistent and comprehensive error handling is critical for API reliability, debugging, and user experience. The WAIF framework needed to establish a standardized approach for handling, classifying, and responding to errors across the entire application.

### Current Error Handling Challenges

#### 1. **Inconsistent Error Responses**
```javascript
// Different endpoints returning different error formats
{ error: "Something went wrong" }
{ message: "Invalid input", code: 400 }
{ status: "failed", details: "Database error" }
```

#### 2. **Mixed Error Classifications**
- Some errors caught and handled at controller level
- Others propagated to global middleware
- No clear distinction between operational vs programmer errors
- Inconsistent logging patterns

#### 3. **Security Concerns**
- Stack traces exposed in production
- Internal system details leaked to clients
- Sensitive information in error messages
- Insufficient error tracking for monitoring

#### 4. **Debugging Difficulties**
- Poor error context and correlation
- Missing request metadata in logs
- Difficult to trace errors across service calls
- Inadequate error aggregation

## Decision

We will implement a **comprehensive, hierarchical error handling strategy** that clearly separates operational errors from programmer errors, provides consistent API responses, and includes robust logging and monitoring capabilities.

### Error Handling Architecture

#### 1. **Error Classification Hierarchy**
```javascript
// Base Error Class
class AppError extends Error {
  constructor(message, code = 'GENERIC_ERROR', statusCode = 500, isOperational = true) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    this.timestamp = new Date().toISOString();
    
    // Capture stack trace
    Error.captureStackTrace(this, this.constructor);
  }
}

// Specific Error Types
class ValidationError extends AppError {
  constructor(message, field = null) {
    super(message, 'VALIDATION_ERROR', 400);
    this.field = field;
  }
}

class NotFoundError extends AppError {
  constructor(resource, identifier = null) {
    const message = identifier 
      ? `${resource} with identifier '${identifier}' not found`
      : `${resource} not found`;
    super(message, 'RESOURCE_NOT_FOUND', 404);
    this.resource = resource;
    this.identifier = identifier;
  }
}

class ConflictError extends AppError {
  constructor(message, conflictType = null) {
    super(message, 'RESOURCE_CONFLICT', 409);
    this.conflictType = conflictType;
  }
}
```

#### 2. **Operational vs Programmer Error Distinction**
```javascript
// Operational Errors (Expected, recoverable)
class DatabaseConnectionError extends AppError {
  constructor(originalError) {
    super('Database connection failed', 'DATABASE_CONNECTION_ERROR', 503);
    this.originalError = originalError;
  }
}

class RateLimitError extends AppError {
  constructor(limit, windowMs) {
    super('Rate limit exceeded', 'RATE_LIMIT_EXCEEDED', 429);
    this.limit = limit;
    this.windowMs = windowMs;
  }
}

// Programmer Errors (Unexpected, indicate bugs)
class ConfigurationError extends AppError {
  constructor(message) {
    super(message, 'CONFIGURATION_ERROR', 500, false); // isOperational = false
  }
}
```

## Implementation Strategy

### 1. **Standardized Error Response Format**
```javascript
// Success Response
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { /* response data */ }
}

// Error Response
{
  "status": "error",
  "message": "Human-readable error message",
  "code": "ERROR_CODE",
  "statusCode": 400,
  "requestId": "uuid-v4-correlation-id",
  "timestamp": "2024-12-05T10:30:00.000Z"
}

// Validation Error (Extended)
{
  "status": "error",
  "message": "Validation failed",
  "code": "VALIDATION_ERROR",
  "statusCode": 400,
  "requestId": "uuid-v4-correlation-id",
  "timestamp": "2024-12-05T10:30:00.000Z",
  "details": {
    "field": "email",
    "value": "invalid-email",
    "constraint": "Must be valid email format"
  }
}
```

### 2. **Global Error Handling Middleware**
```javascript
// src/api/v1.0/middleware/core/error.middleware.js
export const errorHandler = (error, request, response, next) => {
  // Generate correlation ID if not exists
  const requestId = request.correlationId || generateUUID();
  
  // Determine if error is operational
  const isOperational = error.isOperational || false;
  
  // Log error with context
  const logger = request.context?.logger || defaultLogger;
  const logLevel = isOperational ? 'warn' : 'error';
  
  logger[logLevel]('Request error', {
    error: {
      name: error.name,
      message: error.message,
      code: error.code,
      statusCode: error.statusCode,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    },
    request: {
      method: request.method,
      path: request.path,
      route: request.route?.path,
      correlationId: requestId,
      userAgent: request.get('User-Agent'),
      ip: request.ip,
    },
    user: {
      id: request.user?.id,
      role: request.user?.role
    },
    timestamp: new Date().toISOString()
  });\n  
  // Send appropriate response\n  if (error instanceof AppError) {\n    return response.status(error.statusCode).json({\n      status: 'error',\n      message: error.message,\n      code: error.code,\n      statusCode: error.statusCode,\n      requestId,\n      timestamp: error.timestamp,\n      ...(error.field && { details: { field: error.field } }),\n      ...(error.resource && { resource: error.resource })\n    });\n  }\n  \n  // Handle unexpected errors (programmer errors)\n  const statusCode = error.statusCode || 500;\n  const message = process.env.NODE_ENV === 'production' \n    ? 'Internal server error' \n    : error.message;\n    \n  response.status(statusCode).json({\n    status: 'error',\n    message,\n    code: 'INTERNAL_SERVER_ERROR',\n    statusCode,\n    requestId,\n    timestamp: new Date().toISOString()\n  });\n  \n  // For programmer errors, consider crashing in development\n  if (!isOperational && process.env.NODE_ENV === 'development') {\n    console.error('Programmer error detected:', error);\n    // Optionally crash the process to force fixes\n    // process.exit(1);\n  }\n};\n```\n\n### 3. **Async Error Handling Wrapper**\n```javascript\n// src/utils/async.handler.js\nexport const asyncHandler = (fn) => {\n  return (request, response, next) => {\n    // Wrap async functions to catch Promise rejections\n    Promise.resolve(fn(request, response, next)).catch(next);\n  };\n};\n\n// Usage in controllers\nexport const createUser = asyncHandler(async (request, response, next) => {\n  const { body } = request;\n  \n  // Input validation\n  if (!body.email) {\n    throw new ValidationError('Email is required', 'email');\n  }\n  \n  if (!isValidEmail(body.email)) {\n    throw new ValidationError('Invalid email format', 'email');\n  }\n  \n  try {\n    const user = await userService.createUser(body);\n    return request.context.success(response, 'User created successfully', user, 201);\n  } catch (error) {\n    if (error.code === 11000) { // MongoDB duplicate key\n      throw new ConflictError('User with this email already exists', 'email');\n    }\n    throw error; // Re-throw unexpected errors\n  }\n});\n```\n\n### 4. **Service Layer Error Handling**\n```javascript\n// src/api/v1.0/services/user.service.js\nexport class UserService {\n  async createUser(userData) {\n    try {\n      // Validate business rules\n      await this.validateUserData(userData);\n      \n      // Attempt database operation\n      const user = await this.mongoService.create('users', userData);\n      \n      // Log successful operation\n      this.logger.info('User created', { userId: user._id, email: user.email });\n      \n      return user;\n      \n    } catch (error) {\n      // Handle known database errors\n      if (error.name === 'MongoNetworkError') {\n        throw new DatabaseConnectionError(error);\n      }\n      \n      if (error.code === 11000) {\n        // Extract field from duplicate key error\n        const field = this.extractDuplicateField(error);\n        throw new ConflictError(`Duplicate ${field} value`, field);\n      }\n      \n      // Log and re-throw unexpected errors\n      this.logger.error('User creation failed', {\n        error: error.message,\n        stack: error.stack,\n        userData: this.sanitizeForLogging(userData)\n      });\n      \n      throw error;\n    }\n  }\n  \n  sanitizeForLogging(data) {\n    const sanitized = { ...data };\n    delete sanitized.password;\n    delete sanitized.token;\n    return sanitized;\n  }\n}\n```\n\n## Rationale\n\n### Why This Error Handling Strategy?\n\n#### 1. **Consistency Across API**\n```javascript\n// All endpoints return same error format\n// Makes client integration predictable\n// Reduces confusion for API consumers\n```\n\n#### 2. **Clear Error Classification**\n```javascript\n// Operational errors: Expected, recoverable\n// - Network timeouts\n// - Validation failures\n// - Resource not found\n\n// Programmer errors: Unexpected, indicate bugs\n// - Null pointer exceptions\n// - Configuration errors\n// - Logic errors\n```\n\n#### 3. **Security by Default**\n```javascript\n// Production mode hides sensitive details\n// Stack traces only in development\n// Sanitized logging of user data\n// No internal system information leaked\n```\n\n#### 4. **Debugging and Monitoring**\n```javascript\n// Correlation IDs for request tracing\n// Structured logging with context\n// Error aggregation and alerting\n// Performance impact tracking\n```\n\n### Why Not Other Approaches?\n\n#### Basic Try-Catch Only\n- **❌ Inconsistency**: Different error handling patterns\n- **❌ Poor UX**: Inconsistent client responses\n- **❌ Debugging**: Hard to trace errors across layers\n\n#### HTTP Status Codes Only\n- **❌ Limited Information**: Not enough context for clients\n- **❌ No Error Codes**: Can't programmatically handle specific errors\n- **❌ Poor Logging**: Missing structured error information\n\n#### Third-Party Error Libraries\n- **❌ Complexity**: Additional dependencies\n- **❌ Over-engineering**: More than needed for our use case\n- **❌ Learning Curve**: Team familiarity with custom approach\n\n## Error Handling Patterns\n\n### 1. **Controller Layer Pattern**\n```javascript\nexport const getUserById = asyncHandler(async (request, response, next) => {\n  const { id } = request.params;\n  \n  // Input validation at controller level\n  if (!id || !isValidObjectId(id)) {\n    throw new ValidationError('Valid user ID is required', 'id');\n  }\n  \n  try {\n    const user = await userService.getUserById(id);\n    return request.context.success(response, 'User retrieved', user);\n  } catch (error) {\n    // Let service layer handle business logic errors\n    // Controller just passes them through\n    throw error;\n  }\n});\n```\n\n### 2. **Service Layer Pattern**\n```javascript\nexport class UserService {\n  async getUserById(id) {\n    try {\n      // Check cache first\n      const cached = await this.redisService.get(`user:${id}`);\n      if (cached) {\n        return JSON.parse(cached);\n      }\n      \n      // Query database\n      const user = await this.mongoService.findOne('users', { _id: id });\n      if (!user) {\n        throw new NotFoundError('User', id);\n      }\n      \n      // Cache result\n      await this.redisService.set(`user:${id}`, JSON.stringify(user), 3600);\n      \n      return user;\n      \n    } catch (error) {\n      // Handle connection errors\n      if (this.isConnectionError(error)) {\n        throw new DatabaseConnectionError(error);\n      }\n      \n      // Re-throw known errors\n      if (error instanceof AppError) {\n        throw error;\n      }\n      \n      // Log and wrap unexpected errors\n      this.logger.error('Unexpected error in getUserById', {\n        error: error.message,\n        stack: error.stack,\n        userId: id\n      });\n      \n      throw new AppError('Failed to retrieve user', 'USER_RETRIEVAL_ERROR', 500, false);\n    }\n  }\n}\n```\n\n### 3. **Middleware Error Processing**\n```javascript\n// Rate limiting middleware with proper error handling\nexport const rateLimitMiddleware = (limit, windowMs) => {\n  return async (request, response, next) => {\n    try {\n      const key = `rate_limit:${request.ip}:${request.path}`;\n      const current = await redisService.get(key) || 0;\n      \n      if (current >= limit) {\n        throw new RateLimitError(limit, windowMs);\n      }\n      \n      await redisService.incr(key, windowMs);\n      next();\n      \n    } catch (error) {\n      if (error instanceof RateLimitError) {\n        throw error;\n      }\n      \n      // Redis connection issues shouldn't block requests\n      logger.warn('Rate limiting unavailable', { error: error.message });\n      next();\n    }\n  };\n};\n```\n\n## Monitoring and Alerting\n\n### 1. **Error Metrics Collection**\n```javascript\n// Error tracking middleware\nexport const errorMetrics = (error, request, response, next) => {\n  // Increment error counters\n  metrics.increment('api.errors.total', 1, {\n    code: error.code,\n    statusCode: error.statusCode,\n    endpoint: request.route?.path,\n    method: request.method\n  });\n  \n  // Track error rates\n  metrics.histogram('api.errors.rate', 1, {\n    endpoint: request.route?.path\n  });\n  \n  next();\n};\n```\n\n### 2. **Alert Thresholds**\n```javascript\n// Configure alerting based on error patterns\nconst alertThresholds = {\n  criticalErrors: {\n    // 5xx errors above 5% rate\n    condition: 'error_rate_5xx > 0.05',\n    severity: 'critical',\n    channels: ['pagerduty', 'slack']\n  },\n  validationErrors: {\n    // High validation error rates might indicate client issues\n    condition: 'validation_error_rate > 0.20',\n    severity: 'warning', \n    channels: ['slack']\n  },\n  databaseErrors: {\n    // Database connection issues\n    condition: 'database_error_count > 10 in 5min',\n    severity: 'high',\n    channels: ['pagerduty']\n  }\n};\n```\n\n### 3. **Error Aggregation and Analysis**\n```javascript\n// Error aggregation for analysis\nexport const errorAggregator = {\n  async aggregateErrors(timeWindow = '1h') {\n    const errors = await this.getErrorsInWindow(timeWindow);\n    \n    return {\n      totalErrors: errors.length,\n      errorsByCode: this.groupBy(errors, 'code'),\n      errorsByEndpoint: this.groupBy(errors, 'endpoint'),\n      errorsByStatusCode: this.groupBy(errors, 'statusCode'),\n      topErrors: this.getTopErrors(errors, 10),\n      trends: this.calculateErrorTrends(errors)\n    };\n  }\n};\n```\n\n## Testing Error Handling\n\n### 1. **Unit Testing Errors**\n```javascript\n// Test error handling in services\ndescribe('UserService Error Handling', () => {\n  it('should throw NotFoundError for non-existent user', async () => {\n    mockMongoService.findOne.mockResolvedValue(null);\n    \n    await assert.rejects(\n      () => userService.getUserById('nonexistent'),\n      NotFoundError\n    );\n  });\n  \n  it('should throw ValidationError for invalid email', async () => {\n    await assert.rejects(\n      () => userService.createUser({ email: 'invalid' }),\n      ValidationError\n    );\n  });\n  \n  it('should handle database connection errors', async () => {\n    const connectionError = new Error('Connection failed');\n    connectionError.name = 'MongoNetworkError';\n    mockMongoService.create.mockRejectedValue(connectionError);\n    \n    await assert.rejects(\n      () => userService.createUser(validUserData),\n      DatabaseConnectionError\n    );\n  });\n});\n```\n\n### 2. **Integration Testing Error Responses**\n```javascript\n// Test API error responses\ndescribe('API Error Responses', () => {\n  it('should return 404 for non-existent resource', async () => {\n    const response = await request(app)\n      .get('/api/users/507f1f77bcf86cd799439011')\n      \n      .expect(404);\n    \n    assert.strictEqual(response.body.status, 'error');\n    assert.strictEqual(response.body.code, 'RESOURCE_NOT_FOUND');\n    assert.ok(response.body.requestId);\n  });\n  \n  it('should return 400 for validation errors', async () => {\n    const response = await request(app)\n      .post('/api/users')\n      \n      .send({ email: 'invalid-email' })\n      .expect(400);\n    \n    assert.strictEqual(response.body.code, 'VALIDATION_ERROR');\n    assert.strictEqual(response.body.details.field, 'email');\n  });\n});\n```\n\n## Consequences\n\n### Positive\n\n#### 1. **Consistent API Experience**\n- Predictable error responses across all endpoints\n- Clear error codes for programmatic handling\n- Standardized error message formats\n\n#### 2. **Improved Debugging**\n- Correlation IDs for request tracing\n- Structured logging with full context\n- Clear separation of error types\n\n#### 3. **Better Security**\n- No sensitive information leaked in production\n- Sanitized error logging\n- Controlled error disclosure\n\n#### 4. **Enhanced Monitoring**\n- Automated error tracking and alerting\n- Error pattern analysis\n- Performance impact measurement\n\n### Negative\n\n#### 1. **Implementation Complexity**\n- More code to write and maintain\n- Additional error classes to manage\n- Comprehensive testing requirements\n\n#### 2. **Performance Overhead**\n- Additional error processing logic\n- Structured logging overhead\n- Error metrics collection impact\n\n#### 3. **Learning Curve**\n- Team needs to understand error hierarchy\n- Proper error classification training\n- Consistent error handling patterns\n\n### Mitigation Strategies\n\n#### 1. **Documentation and Training**\n```javascript\n// Comprehensive error handling guide\n// Code examples for common patterns\n// Best practices documentation\n```\n\n#### 2. **Automated Tools**\n```javascript\n// ESLint rules for error handling\n// Code generation for common error types\n// Testing utilities for error scenarios\n```\n\n#### 3. **Performance Optimization**\n```javascript\n// Efficient error logging\n// Conditional stack trace capture\n// Optimized error metrics collection\n```\n\n## Future Considerations\n\n### 1. **Error Analytics Enhancement**\n- Machine learning for error pattern detection\n- Predictive error analysis\n- Automated error resolution suggestions\n\n### 2. **Distributed Error Handling**\n- Cross-service error correlation\n- Distributed tracing integration\n- Microservice error propagation\n\n### 3. **Error Recovery Mechanisms**\n- Automatic retry logic for transient errors\n- Circuit breaker patterns\n- Graceful degradation strategies\n\n## References\n\n- [Node.js Error Handling Best Practices](https://nodejs.org/en/docs/guides/error-handling/)\n- [HTTP Status Codes](https://httpstatuses.com/)\n- [Structured Logging Patterns](https://www.structlog.org/en/stable/)\n\n## Review and Updates\n\n- **Decision Date**: 2024-12-05\n- **Last Reviewed**: 2024-12-05\n- **Next Review**: 2025-03-01 (3 months)\n- **Status**: Active implementation\n\n---\n\n*This ADR establishes comprehensive error handling as the standard for the WAIF framework, ensuring consistent, secure, and debuggable error management across all application layers.*