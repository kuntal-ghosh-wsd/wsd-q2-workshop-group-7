<!-- File: /docs/patterns/controller-patterns.md -->
<!-- Last Updated: 2024-12-05 -->
<!-- Status: current -->

# WAIF Framework Controller Patterns

## Overview

This document defines the controller layer patterns for the WAIF framework, establishing consistent approaches for request handling, input validation, response formatting, and error management.

## Controller Architecture

### Core Principles

1. **Single Responsibility**: Each controller handles one resource or related operations
2. **Async/Await**: All controller methods use async/await patterns
3. **Input Validation**: Validate and sanitize all user inputs at controller level
4. **Standardized Responses**: Use consistent response formats via request.context
5. **Error Propagation**: Let error middleware handle errors appropriately
6. **Thin Controllers**: Business logic belongs in service layer

## Base Controller Pattern

### Controller Structure Template
```javascript
/**
 * Base Controller Pattern
 * All controllers should follow this structure
 */
import { asyncHandler } from '../../../utils/async.handler.js';
import { ValidationError, NotFoundError } from '../../../utils/errors.js';
import { ResourceService } from '../services/resource.service.js';

// Initialize service instance
const resourceService = new ResourceService();

/**
 * Resource Controller
 * Handles HTTP requests for resource operations
 */
export class ResourceController {
  /**
   * Create new resource
   * @route POST /api/resources
   * @param {Object} request - Express request object
   * @param {Object} response - Express response object
   * @param {Function} next - Express next function
   */
  static create = asyncHandler(async (request, response, next) => {
    try {
      // Extract request data
      const { body } = request;

      // Input validation at controller level
      ResourceController.validateCreateInput(body);

      // Call service layer
      const result = await resourceService.create(body);

      // Return standardized success response
      return request.context.success(
        response,
        'Resource created successfully',
        result,
        201
      );

    } catch (error) {
      // Pass error to error handling middleware
      next(error);
    }
  });

  /**
   * Get resource by ID
   * @route GET /api/resources/:id
   */
  static getById = asyncHandler(async (request, response, next) => {
    try {
      const { id } = request.params;

      // Parameter validation
      if (!id || !ResourceController.isValidObjectId(id)) {
        throw new ValidationError('Valid resource ID is required', 'id');
      }

      // Service call
      const result = await resourceService.findById(id);

      return request.context.success(
        response,
        'Resource retrieved successfully',
        result
      );

    } catch (error) {
      next(error);
    }
  });

  /**
   * Update resource
   * @route PUT /api/resources/:id
   */
  static update = asyncHandler(async (request, response, next) => {
    try {
      const { id } = request.params;
      const { body } = request;

      // Validate inputs
      if (!id || !ResourceController.isValidObjectId(id)) {
        throw new ValidationError('Valid resource ID is required', 'id');
      }
      ResourceController.validateUpdateInput(body);

      // Service call
      const result = await resourceService.update(id, body);

      return request.context.success(
        response,
        'Resource updated successfully',
        result
      );

    } catch (error) {
      next(error);
    }
  });

  /**
   * Delete resource
   * @route DELETE /api/resources/:id
   */
  static delete = asyncHandler(async (request, response, next) => {
    try {
      const { id } = request.params;

      // Parameter validation
      if (!id || !ResourceController.isValidObjectId(id)) {
        throw new ValidationError('Valid resource ID is required', 'id');
      }

      // Service call
      await resourceService.delete(id);

      return request.context.success(
        response,
        'Resource deleted successfully',
        null,
        200
      );

    } catch (error) {
      next(error);
    }
  });

  /**
   * List resources with pagination
   * @route GET /api/resources
   */
  static list = asyncHandler(async (request, response, next) => {
    try {
      const { query } = request;

      // Parse and validate query parameters
      const options = ResourceController.parseListOptions(query);

      // Service call
      const result = await resourceService.findMany(options);

      return request.context.paginated(
        response,
        'Resources retrieved successfully',
        result.results,
        result.pagination
      );

    } catch (error) {
      next(error);
    }
  });

  // --- Validation Helper Methods ---

  /**
   * Validate input for create operation
   * @param {Object} data - Input data to validate
   * @throws {ValidationError} Invalid input
   * @private
   */
  static validateCreateInput(data) {
    if (!data || typeof data !== 'object') {
      throw new ValidationError('Request body is required');
    }

    // Required field validation
    if (!data.name || typeof data.name !== 'string' || data.name.trim().length === 0) {
      throw new ValidationError('Name is required and must be non-empty string', 'name');
    }

    if (!data.email || !ResourceController.isValidEmail(data.email)) {
      throw new ValidationError('Valid email address is required', 'email');
    }

    // Optional field validation
    if (data.age !== undefined && (!Number.isInteger(data.age) || data.age < 0 || data.age > 150)) {
      throw new ValidationError('Age must be integer between 0 and 150', 'age');
    }
  }

  /**
   * Validate input for update operation
   * @param {Object} data - Input data to validate
   * @throws {ValidationError} Invalid input
   * @private
   */
  static validateUpdateInput(data) {
    if (!data || typeof data !== 'object') {
      throw new ValidationError('Request body is required');
    }

    // At least one field required for update
    const updateableFields = ['name', 'email', 'age', 'status'];
    const hasValidField = updateableFields.some(field => data[field] !== undefined);
    
    if (!hasValidField) {
      throw new ValidationError('At least one updateable field is required');
    }

    // Validate individual fields if present
    if (data.name !== undefined) {
      if (typeof data.name !== 'string' || data.name.trim().length === 0) {
        throw new ValidationError('Name must be non-empty string', 'name');
      }
    }

    if (data.email !== undefined) {
      if (!ResourceController.isValidEmail(data.email)) {
        throw new ValidationError('Valid email address is required', 'email');
      }
    }

    if (data.age !== undefined) {
      if (!Number.isInteger(data.age) || data.age < 0 || data.age > 150) {
        throw new ValidationError('Age must be integer between 0 and 150', 'age');
      }
    }
  }

  // --- Utility Helper Methods ---

  /**
   * Parse and validate list query options
   * @param {Object} query - Query parameters
   * @returns {Object} Parsed options
   * @private
   */
  static parseListOptions(query) {
    const options = {
      page: 1,
      limit: 20,
      sortBy: 'createdAt',
      sortOrder: -1
    };

    // Parse page
    if (query.page) {
      const page = parseInt(query.page, 10);
      if (isNaN(page) || page < 1) {
        throw new ValidationError('Page must be positive integer', 'page');
      }
      options.page = page;
    }

    // Parse limit
    if (query.limit) {
      const limit = parseInt(query.limit, 10);
      if (isNaN(limit) || limit < 1 || limit > 100) {
        throw new ValidationError('Limit must be integer between 1 and 100', 'limit');
      }
      options.limit = limit;
    }

    // Parse sort
    if (query.sortBy) {
      const allowedSortFields = ['name', 'email', 'createdAt', 'updatedAt'];
      if (!allowedSortFields.includes(query.sortBy)) {
        throw new ValidationError(`SortBy must be one of: ${allowedSortFields.join(', ')}`, 'sortBy');
      }
      options.sortBy = query.sortBy;
    }

    if (query.sortOrder) {
      const order = query.sortOrder.toLowerCase();
      if (order === 'asc' || order === '1') {
        options.sortOrder = 1;
      } else if (order === 'desc' || order === '-1') {
        options.sortOrder = -1;
      } else {
        throw new ValidationError('SortOrder must be asc/desc or 1/-1', 'sortOrder');
      }
    }

    // Parse filters
    if (query.status) {
      options.filters = { status: query.status };
    }

    if (query.search) {
      options.search = query.search.trim();
    }

    return options;
  }

  /**
   * Validate MongoDB ObjectId
   * @param {string} id - ID to validate
   * @returns {boolean} Valid ObjectId
   * @private
   */
  static isValidObjectId(id) {
    return /^[0-9a-fA-F]{24}$/.test(id);
  }

  /**
   * Validate email address
   * @param {string} email - Email to validate
   * @returns {boolean} Valid email
   * @private
   */
  static isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}

// Export individual methods for routes
export const {
  create,
  getById,
  update,
  delete: deleteResource,
  list
} = ResourceController;
```

## Specialized Controller Patterns

### File Upload Controller Pattern
```javascript
/**
 * File Upload Controller Pattern
 * Handles file uploads with validation and storage
 */
import multer from 'multer';
import { FileService } from '../services/file.service.js';

const fileService = new FileService();

// Configure multer for file uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB limit
    files: 1 // Single file
  },
  fileFilter: (req, file, cb) => {
    // Allow only specific file types
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new ValidationError('File type not allowed', 'file'));
    }
  }
});

export class FileController {
  /**
   * Upload single file
   * @route POST /api/files
   */
  static uploadSingle = [
    upload.single('file'),
    asyncHandler(async (request, response, next) => {
      try {
        // Check if file was uploaded
        if (!request.file) {
          throw new ValidationError('File is required', 'file');
        }

        // Additional file validation
        FileController.validateFile(request.file);

        // Process file upload
        const result = await fileService.uploadFile({
          buffer: request.file.buffer,
          mimetype: request.file.mimetype,
          originalname: request.file.originalname,
          size: request.file.size,
          userId: request.user?.id
        });

        return request.context.success(
          response,
          'File uploaded successfully',
          result,
          201
        );

      } catch (error) {
        next(error);
      }
    })
  ];

  /**
   * Upload multiple files
   * @route POST /api/files/multiple
   */
  static uploadMultiple = [
    upload.array('files', 5), // Max 5 files
    asyncHandler(async (request, response, next) => {
      try {
        if (!request.files || request.files.length === 0) {
          throw new ValidationError('At least one file is required', 'files');
        }

        // Validate each file
        request.files.forEach((file, index) => {
          FileController.validateFile(file, `files[${index}]`);
        });

        // Process file uploads
        const results = await Promise.all(
          request.files.map(file => 
            fileService.uploadFile({
              buffer: file.buffer,
              mimetype: file.mimetype,
              originalname: file.originalname,
              size: file.size,
              userId: request.user?.id
            })
          )
        );

        return request.context.success(
          response,
          'Files uploaded successfully',
          results,
          201
        );

      } catch (error) {
        next(error);
      }
    })
  ];

  /**
   * Validate uploaded file
   * @param {Object} file - Multer file object
   * @param {string} fieldName - Field name for error context
   * @throws {ValidationError} Invalid file
   * @private
   */
  static validateFile(file, fieldName = 'file') {
    // File size validation
    if (file.size === 0) {
      throw new ValidationError('File cannot be empty', fieldName);
    }

    // File name validation
    if (!file.originalname || file.originalname.length > 255) {
      throw new ValidationError('Invalid file name', fieldName);
    }

    // Check for malicious file names
    const dangerousPatterns = ['../', '.\\', '<script', '<?php'];
    if (dangerousPatterns.some(pattern => 
      file.originalname.toLowerCase().includes(pattern))) {
      throw new ValidationError('File name contains dangerous characters', fieldName);
    }
  }
}
```

### Search Controller Pattern
```javascript
/**
 * Search Controller Pattern
 * Handles complex search operations with filters
 */
export class SearchController {
  /**
   * Advanced search with multiple filters
   * @route GET /api/search
   */
  static search = asyncHandler(async (request, response, next) => {
    try {
      const { query } = request;

      // Parse search parameters
      const searchParams = SearchController.parseSearchParams(query);

      // Validate search parameters
      SearchController.validateSearchParams(searchParams);

      // Perform search
      const results = await searchService.search(searchParams);

      return request.context.paginated(
        response,
        'Search completed successfully',
        results.results,
        results.pagination,
        {
          query: searchParams.query,
          filters: searchParams.filters,
          facets: results.facets
        }
      );

    } catch (error) {
      next(error);
    }
  });

  /**
   * Parse search query parameters
   * @param {Object} query - Query parameters
   * @returns {Object} Parsed search parameters
   * @private
   */
  static parseSearchParams(query) {
    const params = {
      query: '',
      filters: {},
      page: 1,
      limit: 20,
      sortBy: 'relevance',
      sortOrder: -1
    };

    // Search query
    if (query.q) {
      params.query = query.q.trim();
    }

    // Category filter
    if (query.category) {
      params.filters.category = Array.isArray(query.category) 
        ? query.category 
        : [query.category];
    }

    // Price range filter
    if (query.minPrice || query.maxPrice) {
      params.filters.priceRange = {};
      if (query.minPrice) {
        params.filters.priceRange.min = parseFloat(query.minPrice);
      }
      if (query.maxPrice) {
        params.filters.priceRange.max = parseFloat(query.maxPrice);
      }
    }

    // Date range filter
    if (query.fromDate || query.toDate) {
      params.filters.dateRange = {};
      if (query.fromDate) {
        params.filters.dateRange.from = new Date(query.fromDate);
      }
      if (query.toDate) {
        params.filters.dateRange.to = new Date(query.toDate);
      }
    }

    // Pagination
    if (query.page) {
      params.page = Math.max(1, parseInt(query.page, 10) || 1);
    }
    if (query.limit) {
      params.limit = Math.min(100, Math.max(1, parseInt(query.limit, 10) || 20));
    }

    return params;
  }

  /**
   * Validate search parameters
   * @param {Object} params - Search parameters
   * @throws {ValidationError} Invalid parameters
   * @private
   */
  static validateSearchParams(params) {
    // Query length validation
    if (params.query && params.query.length > 500) {
      throw new ValidationError('Search query too long (max 500 characters)', 'q');
    }

    // Price range validation
    if (params.filters.priceRange) {
      const { min, max } = params.filters.priceRange;
      if (min && (isNaN(min) || min < 0)) {
        throw new ValidationError('Minimum price must be non-negative number', 'minPrice');
      }
      if (max && (isNaN(max) || max < 0)) {
        throw new ValidationError('Maximum price must be non-negative number', 'maxPrice');
      }
      if (min && max && min > max) {
        throw new ValidationError('Minimum price cannot be greater than maximum price');
      }
    }

    // Date range validation
    if (params.filters.dateRange) {
      const { from, to } = params.filters.dateRange;
      if (from && isNaN(from.getTime())) {
        throw new ValidationError('Invalid from date format', 'fromDate');
      }
      if (to && isNaN(to.getTime())) {
        throw new ValidationError('Invalid to date format', 'toDate');
      }
      if (from && to && from > to) {
        throw new ValidationError('From date cannot be after to date');
      }
    }
  }
}
```

### Batch Operation Controller Pattern
```javascript
/**
 * Batch Operation Controller Pattern
 * Handles bulk operations efficiently
 */
export class BatchController {
  /**
   * Bulk create resources
   * @route POST /api/resources/batch
   */
  static bulkCreate = asyncHandler(async (request, response, next) => {
    try {
      const { body } = request;

      // Validate batch input
      BatchController.validateBatchInput(body);

      // Validate individual items
      body.items.forEach((item, index) => {
        try {
          ResourceController.validateCreateInput(item);
        } catch (error) {
          throw new ValidationError(
            `Item ${index + 1}: ${error.message}`,
            `items[${index}]`
          );
        }
      });

      // Process batch operation
      const result = await resourceService.bulkCreate(body.items);

      return request.context.success(
        response,
        `Successfully created ${result.successful} of ${body.items.length} resources`,
        {
          successful: result.successful,
          failed: result.failed,
          results: result.results,
          errors: result.errors
        },
        201
      );

    } catch (error) {
      next(error);
    }
  });

  /**
   * Bulk update resources
   * @route PUT /api/resources/batch
   */
  static bulkUpdate = asyncHandler(async (request, response, next) => {
    try {
      const { body } = request;

      // Validate batch update input
      BatchController.validateBatchUpdateInput(body);

      // Process bulk update
      const result = await resourceService.bulkUpdate(body.updates);

      return request.context.success(
        response,
        `Successfully updated ${result.successful} of ${body.updates.length} resources`,
        result
      );

    } catch (error) {
      next(error);
    }
  });

  /**
   * Validate batch operation input
   * @param {Object} body - Request body
   * @throws {ValidationError} Invalid input
   * @private
   */
  static validateBatchInput(body) {
    if (!body || typeof body !== 'object') {
      throw new ValidationError('Request body is required');
    }

    if (!Array.isArray(body.items)) {
      throw new ValidationError('Items array is required', 'items');
    }

    if (body.items.length === 0) {
      throw new ValidationError('At least one item is required', 'items');
    }

    if (body.items.length > 100) {
      throw new ValidationError('Maximum 100 items allowed per batch', 'items');
    }
  }

  /**
   * Validate batch update input
   * @param {Object} body - Request body
   * @throws {ValidationError} Invalid input
   * @private
   */
  static validateBatchUpdateInput(body) {
    if (!body || typeof body !== 'object') {
      throw new ValidationError('Request body is required');
    }

    if (!Array.isArray(body.updates)) {
      throw new ValidationError('Updates array is required', 'updates');
    }

    if (body.updates.length === 0) {
      throw new ValidationError('At least one update is required', 'updates');
    }

    if (body.updates.length > 100) {
      throw new ValidationError('Maximum 100 updates allowed per batch', 'updates');
    }

    // Validate each update item
    body.updates.forEach((update, index) => {
      if (!update.id || !ResourceController.isValidObjectId(update.id)) {
        throw new ValidationError(
          `Update ${index + 1}: Valid ID is required`,
          `updates[${index}].id`
        );
      }

      if (!update.data || typeof update.data !== 'object') {
        throw new ValidationError(
          `Update ${index + 1}: Update data is required`,
          `updates[${index}].data`
        );
      }
    });
  }
}
```

## Response Handling Patterns

### Success Response Patterns
```javascript
/**
 * Success Response Patterns
 * Standardized success responses
 */
export class ResponsePatterns {
  /**
   * Single resource response
   */
  static singleResource = (request, response, message, data, statusCode = 200) => {
    return request.context.success(response, message, data, statusCode);
  };

  /**
   * List response with pagination
   */
  static pagedList = (request, response, message, results, pagination) => {
    return request.context.paginated(response, message, results, pagination);
  };

  /**
   * No content response (for deletes)
   */
  static noContent = (request, response) => {
    return response.status(204).send();
  };

  /**
   * Created response
   */
  static created = (request, response, message, data) => {
    return request.context.success(response, message, data, 201);
  };

  /**
   * Accepted response (for async operations)
   */
  static accepted = (request, response, message, data) => {
    return request.context.success(response, message, data, 202);
  };
}
```

## Controller Testing Patterns

### Controller Test Template
```javascript
/**
 * Controller Testing Patterns
 */
// tests/unit/controllers/resource.controller.test.js
import { describe, it, beforeEach, mock } from 'node:test';
import assert from 'node:assert';
import request from 'supertest';
import { app } from '../../../src/app.js';

describe('ResourceController', () => {
  let mockService;

  beforeEach(() => {
    // Mock service layer
    mockService = {
      create: mock.fn(),
      findById: mock.fn(),
      update: mock.fn(),
      delete: mock.fn(),
      findMany: mock.fn()
    };

    // Override service instance
    jest.doMock('../../../src/api/v1.0/services/resource.service.js', () => ({
      ResourceService: jest.fn(() => mockService)
    }));
  });

  describe('POST /api/resources', () => {
    it('should create resource with valid data', async () => {
      const resourceData = {
        name: 'Test Resource',
        email: 'test@example.com'
      };

      const expectedResult = {
        _id: 'resource123',
        ...resourceData
      };

      mockService.create.mock.mockImplementation(() => 
        Promise.resolve(expectedResult)
      );

      const response = await request(app)
        .post('/api/resources')
        .send(resourceData)
        .expect(201);

      assert.strictEqual(response.body.status, 'success');
      assert.strictEqual(response.body.message, 'Resource created successfully');
      assert.deepStrictEqual(response.body.data, expectedResult);
    });

    it('should return 400 for invalid input', async () => {
      const invalidData = {
        email: 'invalid-email' // Missing name, invalid email
      };

      const response = await request(app)
        .post('/api/resources')
        .send(invalidData)
        .expect(400);

      assert.strictEqual(response.body.status, 'error');
      assert.strictEqual(response.body.code, 'VALIDATION_ERROR');
    });
  });

  describe('GET /api/resources/:id', () => {
    it('should return resource for valid ID', async () => {
      const resourceId = '507f1f77bcf86cd799439011';
      const expectedResult = {
        _id: resourceId,
        name: 'Test Resource',
        email: 'test@example.com'
      };

      mockService.findById.mock.mockImplementation(() => 
        Promise.resolve(expectedResult)
      );

      const response = await request(app)
        .get(`/api/resources/${resourceId}`)
        .expect(200);

      assert.strictEqual(response.body.status, 'success');
      assert.deepStrictEqual(response.body.data, expectedResult);
    });

    it('should return 400 for invalid ID format', async () => {
      const invalidId = 'invalid-id';

      const response = await request(app)
        .get(`/api/resources/${invalidId}`)
        .expect(400);

      assert.strictEqual(response.body.code, 'VALIDATION_ERROR');
    });
  });
});
```

## Common Controller Anti-Patterns

### ❌ What to Avoid

1. **Business Logic in Controllers**
   ```javascript
   // Wrong - business logic in controller
   export const createUser = async (req, res) => {
     const user = await User.create(req.body);
     await EmailService.sendWelcomeEmail(user.email);
     await AuditLog.create({action: 'user_created', userId: user.id});
     res.json(user);
   };
   ```

2. **Direct Database Access**
   ```javascript
   // Wrong - controller accessing database directly
   export const getUsers = async (req, res) => {
     const users = await db.collection('users').find({}).toArray();
     res.json(users);
   };
   ```

3. **Missing Input Validation**
   ```javascript
   // Wrong - no input validation
   export const createUser = async (req, res) => {
     const user = await userService.create(req.body);
     res.json(user);
   };
   ```

4. **Inconsistent Response Formats**
   ```javascript
   // Wrong - different response formats
   res.json({success: true, user}); // Sometimes this
   res.json({status: 'ok', data: user}); // Sometimes this
   res.json(user); // Sometimes just data
   ```

## Best Practices Summary

### ✅ Controller Best Practices

1. **Use Async Handler Wrapper**: Always wrap async functions with asyncHandler
2. **Validate Early**: Validate inputs at the controller level
3. **Use Services**: Delegate business logic to service layer
4. **Consistent Responses**: Use standardized response formats
5. **Error Propagation**: Let middleware handle errors
6. **Single Responsibility**: One controller per resource/domain
7. **Static Methods**: Use static methods for stateless operations
8. **Proper HTTP Status Codes**: Use appropriate status codes for different scenarios

Remember: Controllers should be thin layers that handle HTTP-specific concerns while delegating business logic to services and using consistent patterns throughout the WAIF framework.