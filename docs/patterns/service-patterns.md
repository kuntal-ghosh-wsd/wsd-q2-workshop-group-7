<!-- File: /docs/patterns/service-patterns.md -->
<!-- Last Updated: 2024-12-05 -->
<!-- Status: current -->

# WAIF Framework Service Patterns

## Overview

This document defines the service layer patterns for the WAIF framework, establishing consistent approaches for business logic implementation, data access, and service architecture.

## Service Layer Architecture

### Core Principles

1. **Singleton Pattern**: All services use singleton pattern for resource management
2. **Clear Separation of Concerns**: Business logic separated from data access
3. **Error Handling**: Comprehensive error handling with proper error types
4. **Logging**: Structured logging with context
5. **Testing**: High testability with dependency injection support

## Service Base Pattern

### Service Class Structure
```javascript
/**
 * Base Service Pattern
 * All services should follow this structure
 */
import { MongoDBService } from './mongodb.service.js';
import { RedisService } from './redis.service.js';
import { logger } from '../../utils/logger.js';
import { ValidationError, NotFoundError, ConflictError } from '../../utils/errors.js';

export class BaseService {
  constructor() {
    // Singleton service instances
    this.mongoService = MongoDBService.getInstance();
    this.redisService = RedisService.getInstance();
    
    // Service-specific logger
    this.logger = logger.child({ 
      service: this.constructor.name 
    });
  }

  /**
   * Validate input data
   * @param {Object} data - Data to validate
   * @throws {ValidationError} Invalid input data
   * @protected
   */
  validateInput(data) {
    // Override in child classes
    if (!data || typeof data !== 'object') {
      throw new ValidationError('Input data is required');
    }
  }

  /**
   * Sanitize data for logging (remove sensitive fields)
   * @param {Object} data - Data to sanitize
   * @returns {Object} Sanitized data
   * @protected
   */
  sanitizeForLogging(data) {
    const sanitized = { ...data };
    delete sanitized.password;
    delete sanitized.token;
    delete sanitized.secret;
    delete sanitized.apiKey;
    return sanitized;
  }

  /**
   * Handle service errors with proper logging
   * @param {Error} error - Original error
   * @param {string} operation - Operation that failed
   * @param {Object} context - Additional context
   * @throws {AppError} Properly categorized error
   * @protected
   */
  handleError(error, operation, context = {}) {
    this.logger.error(`${operation} failed`, {
      error: error.message,
      stack: error.stack,
      context: this.sanitizeForLogging(context)
    });

    // Re-throw AppError instances
    if (error.isOperational) {
      throw error;
    }

    // Handle known database errors
    if (error.name === 'MongoNetworkError') {
      throw new DatabaseConnectionError(error);
    }

    if (error.code === 11000) {
      const field = this.extractDuplicateField(error);
      throw new ConflictError(`Duplicate ${field} value`, field);
    }

    // Wrap unexpected errors
    throw new AppError(
      `${operation} failed`,
      'SERVICE_ERROR',
      500,
      false // Not operational - indicates bug
    );
  }
}
```

## Specific Service Patterns

### CRUD Service Pattern
```javascript
/**
 * CRUD Service Pattern
 * Standard Create, Read, Update, Delete operations
 */
export class CrudService extends BaseService {
  constructor(collectionName) {
    super();
    this.collectionName = collectionName;
  }

  /**
   * Create new entity
   * @param {Object} data - Entity data
   * @returns {Promise<Object>} Created entity
   * @throws {ValidationError} Invalid input data
   * @throws {ConflictError} Duplicate entity
   */
  async create(data) {
    try {
      // Validate input
      this.validateCreateInput(data);

      // Add timestamps
      const entityData = {
        ...data,
        createdAt: new Date(),
        updatedAt: new Date()
      };

      // Save to database
      const result = await this.mongoService.create(
        this.collectionName, 
        entityData
      );

      // Cache if applicable
      await this.setCacheIfApplicable(result._id, result);

      this.logger.info('Entity created', { 
        entityId: result._id,
        collection: this.collectionName 
      });

      return result;

    } catch (error) {
      this.handleError(error, 'create', data);
    }
  }

  /**
   * Find entity by ID
   * @param {string} id - Entity ID
   * @returns {Promise<Object>} Found entity
   * @throws {ValidationError} Invalid ID
   * @throws {NotFoundError} Entity not found
   */
  async findById(id) {
    try {
      // Validate ID
      if (!id || !this.isValidObjectId(id)) {
        throw new ValidationError('Valid entity ID is required');
      }

      // Check cache first
      const cached = await this.getCacheIfApplicable(id);
      if (cached) {
        this.logger.debug('Entity retrieved from cache', { entityId: id });
        return cached;
      }

      // Query database
      const result = await this.mongoService.findOne(
        this.collectionName,
        { _id: id }
      );

      if (!result) {
        throw new NotFoundError(this.collectionName, id);
      }

      // Cache result
      await this.setCacheIfApplicable(id, result);

      this.logger.debug('Entity retrieved from database', { entityId: id });
      return result;

    } catch (error) {
      this.handleError(error, 'findById', { id });
    }
  }

  /**
   * Update entity
   * @param {string} id - Entity ID
   * @param {Object} updateData - Data to update
   * @returns {Promise<Object>} Updated entity
   */
  async update(id, updateData) {
    try {
      // Validate inputs
      if (!id || !this.isValidObjectId(id)) {
        throw new ValidationError('Valid entity ID is required');
      }
      this.validateUpdateInput(updateData);

      // Add updated timestamp
      const data = {
        ...updateData,
        updatedAt: new Date()
      };

      // Update in database
      const result = await this.mongoService.updateOne(
        this.collectionName,
        { _id: id },
        { $set: data }
      );

      if (!result.matchedCount) {
        throw new NotFoundError(this.collectionName, id);
      }

      // Get updated entity
      const updated = await this.mongoService.findOne(
        this.collectionName,
        { _id: id }
      );

      // Update cache
      await this.setCacheIfApplicable(id, updated);

      this.logger.info('Entity updated', { entityId: id });
      return updated;

    } catch (error) {
      this.handleError(error, 'update', { id, updateData });
    }
  }

  /**
   * Delete entity
   * @param {string} id - Entity ID
   * @returns {Promise<boolean>} Success status
   */
  async delete(id) {
    try {
      // Validate ID
      if (!id || !this.isValidObjectId(id)) {
        throw new ValidationError('Valid entity ID is required');
      }

      // Delete from database
      const result = await this.mongoService.deleteOne(
        this.collectionName,
        { _id: id }
      );

      if (!result.deletedCount) {
        throw new NotFoundError(this.collectionName, id);
      }

      // Remove from cache
      await this.removeCacheIfApplicable(id);

      this.logger.info('Entity deleted', { entityId: id });
      return true;

    } catch (error) {
      this.handleError(error, 'delete', { id });
    }
  }
}
```

### Business Logic Service Pattern
```javascript
/**
 * Business Logic Service Pattern
 * For complex business operations beyond simple CRUD
 */
export class BusinessService extends BaseService {
  /**
   * Complex business operation with multiple steps
   * @param {Object} params - Operation parameters
   * @returns {Promise<Object>} Operation result
   */
  async performBusinessOperation(params) {
    const session = this.mongoService.client.startSession();
    
    try {
      // Validate business rules
      await this.validateBusinessRules(params);

      // Start transaction for consistency
      await session.withTransaction(async () => {
        // Step 1: Perform first operation
        const step1Result = await this.performStep1(params, session);
        
        // Step 2: Perform dependent operation
        const step2Result = await this.performStep2(step1Result, session);
        
        // Step 3: Update related entities
        await this.updateRelatedEntities(step2Result, session);
        
        // Step 4: Send notifications/events
        await this.triggerBusinessEvents(step2Result);
        
        return step2Result;
      });

      this.logger.info('Business operation completed', {
        operation: 'performBusinessOperation',
        params: this.sanitizeForLogging(params)
      });

    } catch (error) {
      this.handleError(error, 'performBusinessOperation', params);
    } finally {
      await session.endSession();
    }
  }

  /**
   * Validate business rules
   * @param {Object} params - Parameters to validate
   * @throws {ValidationError} Business rule violation
   * @private
   */
  async validateBusinessRules(params) {
    // Example: Check user permissions
    if (params.userId) {
      const user = await this.userService.findById(params.userId);
      if (!user.isActive) {
        throw new ValidationError('User account is not active');
      }
    }

    // Example: Check business constraints
    if (params.amount && params.amount > 10000) {
      throw new ValidationError('Amount exceeds maximum limit');
    }
  }
}
```

## Caching Patterns

### Cache-Aside Pattern
```javascript
/**
 * Cache-Aside Pattern Implementation
 * Application manages cache explicitly
 */
export class CacheAsideService extends BaseService {
  /**
   * Get data with cache-aside pattern
   * @param {string} key - Cache key
   * @param {Function} dataLoader - Function to load data if not cached
   * @param {number} ttl - Time to live in seconds
   * @returns {Promise<Object>} Data
   */
  async getWithCache(key, dataLoader, ttl = 3600) {
    try {
      // Try cache first
      const cached = await this.redisService.get(key);
      if (cached) {
        this.logger.debug('Cache hit', { key });
        return JSON.parse(cached);
      }

      // Load from data source
      this.logger.debug('Cache miss', { key });
      const data = await dataLoader();
      
      // Store in cache
      if (data) {
        await this.redisService.setex(key, ttl, JSON.stringify(data));
        this.logger.debug('Data cached', { key, ttl });
      }

      return data;

    } catch (error) {
      // If cache fails, still return data
      this.logger.warn('Cache operation failed', { 
        error: error.message, 
        key 
      });
      return await dataLoader();
    }
  }

  /**
   * Invalidate cache entries
   * @param {string|Array<string>} keys - Cache keys to invalidate
   */
  async invalidateCache(keys) {
    try {
      const keyArray = Array.isArray(keys) ? keys : [keys];
      await this.redisService.del(...keyArray);
      this.logger.debug('Cache invalidated', { keys: keyArray });
    } catch (error) {
      this.logger.warn('Cache invalidation failed', { 
        error: error.message, 
        keys 
      });
    }
  }
}
```

### Write-Through Pattern
```javascript
/**
 * Write-Through Pattern Implementation
 * Cache is updated synchronously with database
 */
export class WriteThroughService extends BaseService {
  /**
   * Create entity with write-through caching
   * @param {Object} data - Entity data
   * @returns {Promise<Object>} Created entity
   */
  async createWithWriteThrough(data) {
    try {
      // Validate input
      this.validateInput(data);

      // Write to database
      const result = await this.mongoService.create('entities', data);

      // Write to cache immediately
      const cacheKey = `entity:${result._id}`;
      await this.redisService.setex(
        cacheKey, 
        3600, 
        JSON.stringify(result)
      );

      this.logger.info('Entity created with write-through cache', { 
        entityId: result._id 
      });

      return result;

    } catch (error) {
      this.handleError(error, 'createWithWriteThrough', data);
    }
  }
}
```

## Data Access Patterns

### Repository Pattern
```javascript
/**
 * Repository Pattern Implementation
 * Encapsulates data access logic
 */
export class EntityRepository extends BaseService {
  constructor() {
    super();
    this.collectionName = 'entities';
  }

  /**
   * Find entities with complex query
   * @param {Object} criteria - Search criteria
   * @param {Object} options - Query options
   * @returns {Promise<Array>} Found entities
   */
  async findByCriteria(criteria, options = {}) {
    try {
      const {
        page = 1,
        limit = 20,
        sortBy = 'createdAt',
        sortOrder = -1,
        fields = null
      } = options;

      // Build query
      const query = this.buildQuery(criteria);
      
      // Build projection
      const projection = fields ? this.buildProjection(fields) : {};

      // Execute query with pagination
      const skip = (page - 1) * limit;
      const [results, total] = await Promise.all([
        this.mongoService.findMany(
          this.collectionName,
          query,
          {
            limit,
            skip,
            sort: { [sortBy]: sortOrder },
            projection
          }
        ),
        this.mongoService.countDocuments(this.collectionName, query)
      ]);

      return {
        results,
        pagination: {
          page,
          limit,
          total,
          pages: Math.ceil(total / limit)
        }
      };

    } catch (error) {
      this.handleError(error, 'findByCriteria', { criteria, options });
    }
  }

  /**
   * Build MongoDB query from criteria
   * @param {Object} criteria - Search criteria
   * @returns {Object} MongoDB query
   * @private
   */
  buildQuery(criteria) {
    const query = {};

    if (criteria.name) {
      query.name = { $regex: criteria.name, $options: 'i' };
    }

    if (criteria.status) {
      query.status = { $in: Array.isArray(criteria.status) ? criteria.status : [criteria.status] };
    }

    if (criteria.dateRange) {
      query.createdAt = {
        $gte: new Date(criteria.dateRange.start),
        $lte: new Date(criteria.dateRange.end)
      };
    }

    return query;
  }
}
```

## Service Integration Patterns

### Service Composition
```javascript
/**
 * Service Composition Pattern
 * Combine multiple services for complex operations
 */
export class CompositeService extends BaseService {
  constructor() {
    super();
    this.userService = new UserService();
    this.orderService = new OrderService();
    this.paymentService = new PaymentService();
    this.notificationService = new NotificationService();
  }

  /**
   * Process order with multiple service coordination
   * @param {Object} orderData - Order information
   * @returns {Promise<Object>} Order processing result
   */
  async processOrder(orderData) {
    const session = this.mongoService.client.startSession();
    
    try {
      await session.withTransaction(async () => {
        // Step 1: Validate user
        const user = await this.userService.findById(orderData.userId);
        if (!user.isActive) {
          throw new ValidationError('User account is inactive');
        }

        // Step 2: Create order
        const order = await this.orderService.create({
          ...orderData,
          status: 'pending',
          userId: user._id
        }, { session });

        // Step 3: Process payment
        const payment = await this.paymentService.processPayment({
          orderId: order._id,
          amount: order.total,
          paymentMethod: orderData.paymentMethod
        });

        // Step 4: Update order status
        await this.orderService.update(order._id, {
          status: 'confirmed',
          paymentId: payment._id
        }, { session });

        // Step 5: Send notifications (outside transaction)
        setImmediate(async () => {
          await this.notificationService.sendOrderConfirmation({
            userId: user._id,
            orderId: order._id,
            email: user.email
          });
        });

        return { order, payment };
      });

    } catch (error) {
      this.handleError(error, 'processOrder', orderData);
    } finally {
      await session.endSession();
    }
  }
}
```

## Error Handling in Services

### Service Error Patterns
```javascript
/**
 * Service Error Handling Patterns
 */
export class ServiceErrorHandler extends BaseService {
  /**
   * Handle database connection errors
   * @param {Error} error - Database error
   * @throws {DatabaseConnectionError} Connection error
   * @private
   */
  handleDatabaseError(error) {
    const connectionErrors = [
      'MongoNetworkError',
      'MongoServerSelectionError',
      'MongoTimeoutError'
    ];

    if (connectionErrors.includes(error.name)) {
      throw new DatabaseConnectionError(error);
    }

    if (error.code === 11000) {
      const field = this.extractDuplicateField(error);
      throw new ConflictError(`Duplicate ${field} value`, field);
    }

    throw error;
  }

  /**
   * Handle external service errors
   * @param {Error} error - External service error
   * @param {string} serviceName - Name of external service
   * @throws {ExternalServiceError} External service error
   * @private
   */
  handleExternalServiceError(error, serviceName) {
    this.logger.error('External service error', {
      service: serviceName,
      error: error.message,
      stack: error.stack
    });

    throw new ExternalServiceError(
      `${serviceName} service unavailable`,
      serviceName,
      error
    );
  }
}
```

## Testing Service Patterns

### Service Testing Pattern
```javascript
/**
 * Service Testing Patterns
 * How to properly test services
 */
// tests/unit/services/user.service.test.js
import { describe, it, beforeEach, afterEach, mock } from 'node:test';
import assert from 'node:assert';
import { UserService } from '../../../src/api/v1.0/services/user.service.js';

describe('UserService', () => {
  let userService;
  let mockMongoService;
  let mockRedisService;

  beforeEach(() => {
    // Create mocks
    mockMongoService = {
      create: mock.fn(),
      findOne: mock.fn(),
      updateOne: mock.fn(),
      deleteOne: mock.fn()
    };

    mockRedisService = {
      get: mock.fn(),
      set: mock.fn(),
      setex: mock.fn(),
      del: mock.fn()
    };

    // Override singleton instances for testing
    UserService.prototype.mongoService = mockMongoService;
    UserService.prototype.redisService = mockRedisService;

    userService = new UserService();
  });

  describe('create', () => {
    it('should create user successfully', async () => {
      const userData = { name: 'Test User', email: 'test@example.com' };
      const expectedUser = { _id: 'user123', ...userData };

      mockMongoService.create.mock.mockImplementation(() => 
        Promise.resolve(expectedUser)
      );

      const result = await userService.create(userData);

      assert.deepStrictEqual(result, expectedUser);
      assert.strictEqual(mockMongoService.create.mock.callCount(), 1);
    });

    it('should handle validation errors', async () => {
      const invalidData = { email: 'invalid-email' };

      await assert.rejects(
        () => userService.create(invalidData),
        {
          name: 'ValidationError',
          message: /email/i
        }
      );
    });
  });
});
```

## Performance Optimization Patterns

### Batch Operations
```javascript
/**
 * Batch Operation Patterns
 * Efficient bulk data processing
 */
export class BatchService extends BaseService {
  /**
   * Process data in batches
   * @param {Array} items - Items to process
   * @param {Function} processor - Processing function
   * @param {number} batchSize - Batch size
   * @returns {Promise<Array>} Processing results
   */
  async processBatch(items, processor, batchSize = 100) {
    const results = [];
    
    for (let i = 0; i < items.length; i += batchSize) {
      const batch = items.slice(i, i + batchSize);
      
      try {
        const batchResults = await Promise.all(
          batch.map(item => processor(item))
        );
        
        results.push(...batchResults);
        
        this.logger.debug('Batch processed', {
          batchIndex: Math.floor(i / batchSize) + 1,
          batchSize: batch.length,
          totalProcessed: results.length,
          totalItems: items.length
        });

      } catch (error) {
        this.logger.error('Batch processing failed', {
          batchIndex: Math.floor(i / batchSize) + 1,
          error: error.message
        });
        
        // Continue with next batch or throw based on strategy
        throw error;
      }
    }
    
    return results;
  }
}
```

## Best Practices

### 1. Service Construction
- Use singleton pattern for shared resources
- Initialize dependencies in constructor
- Create service-specific logger instance

### 2. Error Handling
- Always use try-catch blocks in service methods
- Categorize errors appropriately (operational vs programmer)
- Log errors with sufficient context
- Don't expose sensitive information

### 3. Caching Strategy
- Implement caching at service layer
- Use appropriate TTL values
- Handle cache failures gracefully
- Implement cache invalidation strategies

### 4. Database Operations
- Use transactions for multi-step operations
- Implement proper connection handling
- Add indexes for query performance
- Use batch operations for bulk data

### 5. Testing
- Mock external dependencies
- Test both success and error scenarios
- Use dependency injection for testability
- Maintain high test coverage

## Common Anti-Patterns

### ❌ What to Avoid

1. **Direct Database Access in Controllers**
   ```javascript
   // Wrong - controller accessing database directly
   export const getUser = async (req, res) => {
     const user = await db.collection('users').findOne({_id: req.params.id});
   };
   ```

2. **Missing Error Handling**
   ```javascript
   // Wrong - no error handling
   export const createUser = async (userData) => {
     return await mongoService.create('users', userData);
   };
   ```

3. **Synchronous Cache Operations**
   ```javascript
   // Wrong - blocking cache operations
   const cached = redisService.getSync(key);
   ```

4. **God Services**
   ```javascript
   // Wrong - single service handling too many responsibilities
   class EverythingService {
     async createUser() {}
     async processPayment() {}
     async sendEmail() {}
     async generateReport() {}
   }
   ```

Remember: Services should be focused, testable, and follow the single responsibility principle while maintaining consistency with the WAIF framework patterns.