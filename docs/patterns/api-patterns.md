<!-- File: /docs/patterns/api-patterns.md -->
<!-- Last Updated: 2024-12-05 -->
<!-- Status: current -->

# WAIF Framework API Patterns

## Overview

This document defines the standard patterns for implementing REST APIs in the WAIF framework, ensuring consistency, maintainability, and optimal performance.

## Controller Patterns

### Standard Controller Structure

```javascript
/**
 * Standard controller implementation pattern
 * All controllers follow this exact structure
 */
import { AppError, ValidationError } from '../../../utils/errors.js';
import { TestService } from '../services/test.service.js';

class TestController {
  /**
   * Creates a new resource following standard pattern.
   * 
   * Pattern: validate → delegate to service → return response
   * 
   * @param {Object} request - Express request object
   * @param {Object} response - Express response object  
   * @param {Function} next - Express next function
   */
  async createResource(request, response, next) {
    try {
      // Step 1: Input validation
      const { requiredField, optionalField } = request.body;
      
      if (!requiredField) {
        return request.context.error(
          'Required field is missing',
          400,
          'VALIDATION_ERROR'
        );
      }
      
      // Step 2: Delegate to service layer
      const result = await TestService.createResource({
        requiredField,
        optionalField,
        createdBy: request.user?.id
      });
      
      // Step 3: Return success response
      return request.context.success(
        'Resource created successfully',
        result,
        201
      );
      
    } catch (error) {
      // Let error middleware handle all errors
      next(error);
    }
  }
  
  /**
   * Retrieves resource by ID following standard pattern.
   */
  async getResourceById(request, response, next) {
    try {
      const { id } = request.params;
      
      // Validate ID format if needed
      if (!this.isValidId(id)) {
        return request.context.error(
          'Invalid resource ID format',
          400,
          'INVALID_ID'
        );
      }
      
      const result = await TestService.findResourceById(id);
      
      if (!result) {
        return request.context.error(
          'Resource not found',
          404,
          'RESOURCE_NOT_FOUND'
        );
      }
      
      return request.context.success(
        'Resource retrieved successfully',
        result
      );
      
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Lists resources with pagination following standard pattern.
   */
  async listResources(request, response, next) {
    try {
      // Parse query parameters with defaults
      const page = parseInt(request.query.page) || 1;
      const limit = Math.min(parseInt(request.query.limit) || 10, 100); // Cap at 100
      const sortBy = request.query.sortBy || 'createdAt';
      const sortOrder = request.query.sortOrder === 'asc' ? 1 : -1;
      
      const options = {
        page,
        limit,
        sortBy,
        sortOrder,
        filter: this.buildFilter(request.query)
      };
      
      const result = await TestService.listResources(options);
      
      return request.context.paginated(
        'Resources retrieved successfully',
        result.data,
        {
          page,
          limit,
          total: result.total,
          pages: Math.ceil(result.total / limit)
        }
      );
      
    } catch (error) {
      next(error);
    }
  }
  
  // Private helper methods
  isValidId(id) {
    return /^[a-zA-Z0-9-_]+$/.test(id) && id.length >= 3;
  }
  
  buildFilter(query) {
    const filter = {};
    
    // Add supported filter fields
    if (query.status) filter.status = query.status;
    if (query.category) filter.category = query.category;
    if (query.search) {
      filter.$text = { $search: query.search };
    }
    
    return filter;
  }
}

export default TestController;
```

### Controller Error Handling Patterns

```javascript
class UserController {
  async updateUser(request, response, next) {
    try {
      const { id } = request.params;
      const updates = request.body;
      
      // Validate ownership or permissions
      const currentUser = await UserService.findById(id);
      if (!currentUser) {
        return request.context.error('User not found', 404);
      }
      
      if (!this.canUserUpdate(request.user, currentUser)) {
        return request.context.error('Insufficient permissions', 403);
      }
      
      const updatedUser = await UserService.updateUser(id, updates);
      
      return request.context.success(
        'User updated successfully',
        updatedUser
      );
      
    } catch (error) {
      // Handle specific known errors
      if (error.code === 11000) {
        return request.context.error(
          'Email already exists',
          409,
          'EMAIL_CONFLICT'
        );
      }
      
      // Let error middleware handle unexpected errors
      next(error);
    }
  }
}
```

## Service Layer Patterns

### Service Implementation Pattern

```javascript
/**
 * Standard service layer implementation
 * Pure business logic, no HTTP concerns
 */
import { AppError, ValidationError, ConflictError } from '../../../utils/errors.js';
import { MongoDBService } from './mongodb.service.js';
import { RedisService } from './redis.service.js';
import { logger } from '../../../utils/logger.js';
import { secureRandomBase36 } from '../../../utils/crypto.helper.js';

class UserService {
  constructor() {
    this.mongodb = MongoDBService.getInstance();
    this.redis = RedisService.getInstance();
    this.collectionName = 'users';
  }
  
  /**
   * Creates a new user with business logic validation.
   * 
   * Pattern: validate → transform → persist → cache → return
   * 
   * @param {Object} userData - User data to create
   * @returns {Promise<Object>} Created user object
   * @throws {ValidationError} When validation fails
   * @throws {ConflictError} When user already exists
   */
  async createUser(userData) {
    // Step 1: Business validation
    await this.validateUserData(userData);
    
    // Step 2: Transform and prepare data
    const userToCreate = {
      ...userData,
      id: this.generateUserId(),
      email: userData.email.toLowerCase(),
      status: 'active',
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    // Step 3: Persist to database
    try {
      const createdUser = await this.mongodb.insertOne(
        this.collectionName,
        userToCreate
      );
      
      // Step 4: Cache user data
      await this.cacheUser(createdUser);
      
      // Step 5: Log success
      logger.info('User created successfully', {
        userId: createdUser.id,
        email: createdUser.email
      });
      
      return this.sanitizeUserData(createdUser);
      
    } catch (error) {
      logger.error('User creation failed', {
        error: error.message,
        userData: { email: userData.email } // Don't log sensitive data
      });
      throw error;
    }
  }
  
  /**
   * Finds user by ID with caching.
   * 
   * Pattern: check cache → query database → cache result → return
   */
  async findUserById(id) {
    // Check cache first
    const cachedUser = await this.getCachedUser(id);
    if (cachedUser) {
      return cachedUser;
    }
    
    // Query database
    const user = await this.mongodb.findOne(this.collectionName, { id });
    
    if (user) {
      // Cache for future requests
      await this.cacheUser(user);
      return this.sanitizeUserData(user);
    }
    
    return null;
  }
  
  /**
   * Lists users with pagination and filtering.
   * 
   * Pattern: build query → execute → transform → return with metadata
   */
  async listUsers(options = {}) {
    const {
      page = 1,
      limit = 10,
      sortBy = 'createdAt',
      sortOrder = -1,
      filter = {}
    } = options;
    
    const skip = (page - 1) * limit;
    const query = { ...filter, status: 'active' }; // Only active users
    const sort = { [sortBy]: sortOrder };
    
    try {
      // Execute queries in parallel
      const [users, totalCount] = await Promise.all([
        this.mongodb.find(this.collectionName, query, {
          skip,
          limit,
          sort
        }),
        this.mongodb.countDocuments(this.collectionName, query)
      ]);
      
      return {
        data: users.map(user => this.sanitizeUserData(user)),
        total: totalCount,
        page,
        limit
      };
      
    } catch (error) {
      logger.error('User list query failed', {
        error: error.message,
        options
      });
      throw new AppError(
        'Failed to retrieve users',
        'USER_QUERY_ERROR',
        500
      );
    }
  }
  
  // Private helper methods
  async validateUserData(userData) {
    const { email, name } = userData;
    
    if (!email || !name) {
      throw new ValidationError('Email and name are required');
    }
    
    if (!this.isValidEmail(email)) {
      throw new ValidationError('Invalid email format');
    }
    
    // Check for existing user
    const existingUser = await this.mongodb.findOne(
      this.collectionName,
      { email: email.toLowerCase() }
    );
    
    if (existingUser) {
      throw new ConflictError('Email already registered');
    }
  }
  
  generateUserId() {
    return `user_${Date.now()}_${secureRandomBase36(9)}`;
  }
  
  sanitizeUserData(user) {
    const { password, ...sanitized } = user;
    return sanitized;
  }
  
  async cacheUser(user) {
    const cacheKey = `user:${user.id}`;
    await this.redis.set(cacheKey, JSON.stringify(user), 3600); // 1 hour TTL
  }
  
  async getCachedUser(id) {
    const cacheKey = `user:${id}`;
    const cached = await this.redis.get(cacheKey);
    return cached ? JSON.parse(cached) : null;
  }
}

export default UserService;
```

## Route Definition Patterns

### Standard Route Structure

```javascript
/**
 * Route definition following WAIF patterns
 * Located: src/api/v1.0/routes/users.routes.js
 */
import { Router } from 'express';
import UserController from '../controllers/user.controller.js';

const router = Router();
const userController = new UserController();

/**
 * @swagger
 * /api/users:
 *   post:
 *     summary: Create a new user
 *     tags: [Users]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - name
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *               name:
 *                 type: string
 *               avatar:
 *                 type: string
 *                 format: uri
 *     responses:
 *       201:
 *         description: User created successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/SuccessResponse'
 *       400:
 *         description: Validation error
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ErrorResponse'
 */
router.post('/', userController.createUser.bind(userController));

/**
 * @swagger
 * /api/users/{id}:
 *   get:
 *     summary: Get user by ID
 *     tags: [Users]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *         description: User ID
 *     responses:
 *       200:
 *         description: User retrieved successfully
 *       404:
 *         description: User not found
 */
router.get('/:id', userController.getUserById.bind(userController));

/**
 * @swagger
 * /api/users:
 *   get:
 *     summary: List users with pagination
 *     tags: [Users]
 *     parameters:
 *       - in: query
 *         name: page
 *         schema:
 *           type: integer
 *           minimum: 1
 *           default: 1
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           minimum: 1
 *           maximum: 100
 *           default: 10
 *     responses:
 *       200:
 *         description: Users retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/PaginatedResponse'
 */
router.get('/', userController.listUsers.bind(userController));

export default router;
```

## Response Format Patterns

### Standard Response Handlers

All responses MUST use the standardized response handlers:

```javascript
// Located: src/utils/response.handler.js

/**
 * Success response with data
 */
request.context.success(
  'Operation completed successfully',
  { id: 123, name: 'Example' },
  200  // Optional status code, defaults to 200
);
// Returns:
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": { "id": 123, "name": "Example" }
}

/**
 * Success response without data
 */
request.context.success('Operation completed successfully');
// Returns:
{
  "status": "success", 
  "message": "Operation completed successfully"
}

/**
 * Error response
 */
request.context.error(
  'Validation failed',
  400,
  'VALIDATION_ERROR'
);
// Returns:
{
  "status": "error",
  "message": "Validation failed", 
  "statusCode": 400,
  "requestId": "uuid-v4-request-id"
}

/**
 * Paginated response
 */
request.context.paginated(
  'Users retrieved successfully',
  [{ id: 1 }, { id: 2 }],
  {
    page: 1,
    limit: 10,
    total: 25,
    pages: 3
  }
);
// Returns:
{
  "status": "success",
  "message": "Users retrieved successfully",
  "data": [{ "id": 1 }, { "id": 2 }],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 10, 
      "total": 25,
      "pages": 3
    }
  }
}
```

## Middleware Patterns

### Custom Middleware Implementation

```javascript
/**
 * Standard middleware pattern for WAIF framework
 */
import { AppError } from '../../utils/errors.js';
import { logger } from '../../utils/logger.js';

/**
 * Authentication middleware example
 */
export function requireAuthentication(request, response, next) {
  try {
    const authHeader = request.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new AppError('Authentication required', 'AUTH_REQUIRED', 401);
    }
    
    const token = authHeader.substring(7);
    const user = validateToken(token);
    
    if (!user) {
      throw new AppError('Invalid authentication token', 'INVALID_TOKEN', 401);
    }
    
    // Add user to request context
    request.user = user;
    request.context.logger.info('User authenticated', { userId: user.id });
    
    next();
  } catch (error) {
    next(error);
  }
}

/**
 * Rate limiting middleware pattern
 */
export function createRateLimiter(options = {}) {
  const {
    maxRequests = 100,
    windowMs = 15 * 60 * 1000, // 15 minutes
    skipSuccessfulRequests = false,
    skipFailedRequests = false
  } = options;
  
  return async (request, response, next) => {
    try {
      const key = `rate_limit:${request.ip}`;
      const current = await redis.get(key) || 0;
      
      if (current >= maxRequests) {
        throw new AppError(
          'Too many requests',
          'RATE_LIMIT_EXCEEDED', 
          429
        );
      }
      
      // Increment counter
      await redis.incr(key);
      await redis.expire(key, Math.ceil(windowMs / 1000));
      
      // Set rate limit headers
      response.setHeader('X-RateLimit-Limit', maxRequests);
      response.setHeader('X-RateLimit-Remaining', maxRequests - current - 1);
      
      next();
    } catch (error) {
      next(error);
    }
  };
}
```

## Validation Patterns

### Input Validation Middleware

```javascript
/**
 * Request validation middleware pattern
 */
import { ValidationError } from '../../utils/errors.js';

export function validateCreateUser(request, response, next) {
  try {
    const { body } = request;
    const errors = [];
    
    // Required fields
    if (!body.email) errors.push('Email is required');
    if (!body.name) errors.push('Name is required');
    
    // Format validation
    if (body.email && !isValidEmail(body.email)) {
      errors.push('Invalid email format');
    }
    
    if (body.name && body.name.length < 2) {
      errors.push('Name must be at least 2 characters');
    }
    
    // Optional field validation
    if (body.avatar && !isValidUrl(body.avatar)) {
      errors.push('Invalid avatar URL');
    }
    
    if (errors.length > 0) {
      throw new ValidationError(errors.join(', '));
    }
    
    // Sanitize input
    request.body = {
      email: body.email?.toLowerCase().trim(),
      name: body.name?.trim(),
      avatar: body.avatar?.trim()
    };
    
    next();
  } catch (error) {
    next(error);
  }
}

// Usage in routes
router.post('/', validateCreateUser, userController.createUser.bind(userController));
```

## Database Integration Patterns

### Service-Database Integration

```javascript
/**
 * Database integration pattern through services
 */
class OrderService {
  constructor() {
    this.mongodb = MongoDBService.getInstance();
    this.redis = RedisService.getInstance();
  }
  
  /**
   * Create order with transaction pattern
   */
  async createOrder(orderData) {
    const session = await this.mongodb.startTransaction();
    
    try {
      // Step 1: Create order
      const order = await this.mongodb.insertOne('orders', {
        ...orderData,
        id: this.generateOrderId(),
        status: 'pending',
        createdAt: new Date()
      }, { session });
      
      // Step 2: Update inventory
      await this.mongodb.updateMany('products', 
        { id: { $in: orderData.productIds } },
        { $inc: { stock: -1 } },
        { session }
      );
      
      // Step 3: Create audit log
      await this.mongodb.insertOne('audit_logs', {
        action: 'order_created',
        orderId: order.id,
        userId: orderData.userId,
        timestamp: new Date()
      }, { session });
      
      await this.mongodb.commitTransaction(session);
      
      // Cache order after successful transaction
      await this.cacheOrder(order);
      
      return order;
      
    } catch (error) {
      await this.mongodb.abortTransaction(session);
      throw error;
    } finally {
      await this.mongodb.endSession(session);
    }
  }
}
```

## Error Handling Patterns

### API Error Response Pattern

```javascript
/**
 * Consistent error handling across all API endpoints
 */

// In controllers - return structured errors
async createUser(request, response, next) {
  try {
    // Business logic
  } catch (error) {
    // Transform specific errors
    if (error.name === 'ValidationError') {
      return request.context.error(
        error.message,
        400,
        'VALIDATION_ERROR'
      );
    }
    
    if (error.code === 11000) {
      return request.context.error(
        'Email already exists',
        409,
        'DUPLICATE_EMAIL'
      );
    }
    
    // Let error middleware handle unexpected errors
    next(error);
  }
}

// Error middleware handles all unhandled errors
export function errorMiddleware(error, request, response, next) {
  // Log error with full context
  const logger = request.context?.logger || globalLogger;
  logger.error('API Error', {
    error: error.message,
    stack: error.stack,
    requestId: request.context?.requestId,
    method: request.method,
    path: request.path,
    userId: request.user?.id
  });
  
  // Send appropriate response
  if (error.isOperational) {
    return response.status(error.statusCode).json({
      status: 'error',
      message: error.message,
      statusCode: error.statusCode,
      requestId: request.context?.requestId
    });
  }
  
  // Generic error for programming errors
  return response.status(500).json({
    status: 'error',
    message: 'Internal server error',
    statusCode: 500,
    requestId: request.context?.requestId
  });
}
```

## Performance Optimization Patterns

### Caching Strategies

```javascript
/**
 * Multi-layer caching pattern
 */
class ProductService {
  async getProduct(id) {
    // Layer 1: Memory cache (fastest)
    if (this.memoryCache.has(id)) {
      return this.memoryCache.get(id);
    }
    
    // Layer 2: Redis cache (fast)
    const cached = await this.redis.get(`product:${id}`);
    if (cached) {
      const product = JSON.parse(cached);
      this.memoryCache.set(id, product); // Populate memory cache
      return product;
    }
    
    // Layer 3: Database (slow)
    const product = await this.mongodb.findOne('products', { id });
    if (product) {
      // Cache in both layers
      await this.redis.set(`product:${id}`, JSON.stringify(product), 3600);
      this.memoryCache.set(id, product);
    }
    
    return product;
  }
}
```

## API Documentation Patterns

### OpenAPI Integration

```javascript
/**
 * OpenAPI documentation integration pattern
 */

// Swagger/OpenAPI annotations in route files
/**
 * @swagger
 * components:
 *   schemas:
 *     User:
 *       type: object
 *       required:
 *         - id
 *         - email
 *         - name
 *       properties:
 *         id:
 *           type: string
 *           description: Unique user identifier
 *         email:
 *           type: string
 *           format: email
 *         name:
 *           type: string
 *           minLength: 2
 *         createdAt:
 *           type: string
 *           format: date-time
 */

// Route documentation
/**
 * @swagger
 * /api/users:
 *   get:
 *     summary: List all users
 *     description: Retrieves a paginated list of active users
 *     responses:
 *       200:
 *         description: Success
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/PaginatedResponse'
 */
```

## Testing Patterns

### API Testing Pattern

```javascript
/**
 * Integration test pattern for API endpoints
 */
import { describe, it } from 'node:test';
import assert from 'node:assert';
import { apiClient } from '../helpers/api.client.js';

describe('Users API', () => {
  describe('POST /api/users', () => {
    it('should create user with valid data', async () => {
      const userData = {
        email: 'test@example.com',
        name: 'Test User'
      };
      
      const response = await apiClient.post('/api/users')
        .send(userData)
        .expect(201);
      
      assert.strictEqual(response.body.status, 'success');
      assert.strictEqual(response.body.data.email, userData.email);
      assert.ok(response.body.data.id);
    });
    
    it('should return 400 for missing email', async () => {
      const userData = { name: 'Test User' };
      
      const response = await apiClient.post('/api/users')
        .send(userData)
        .expect(400);
      
      assert.strictEqual(response.body.status, 'error');
      assert.ok(response.body.message.includes('email'));
    });
  });
});
```

## Related Documentation

- [Code Standards](./STANDARDS.md) - Complete coding standards
- [Error Handling Patterns](./error-handling.md) - Error handling strategies
- [Testing Patterns](./testing-patterns.md) - Testing approaches
- [Anti-patterns](./anti-patterns.md) - What to avoid
- [API Reference](../api/README.md) - Complete API documentation