<!-- File: /docs/patterns/route-patterns.md -->
<!-- Last Updated: 2024-12-05 -->
<!-- Status: current -->

# WAIF Framework Route Patterns

## Overview

This document defines the routing patterns for the WAIF framework, focusing on Express v5 compliance, consistent URL structure, middleware integration, and proper route organization.

## Core Routing Principles

### 1. Express v5 Compliance
All routes must follow Express v5 syntax patterns to avoid breaking changes.

### 2. RESTful Conventions
Follow REST principles for resource-based URLs and HTTP methods.

### 3. Middleware Chain Consistency
Maintain consistent middleware application across all routes.

## Express v5 Route Syntax Patterns

### ⚠️ Critical Breaking Changes from v4

#### Named Wildcards Required
```javascript
// ❌ Express v4 - WILL BREAK in v5
app.use('*', corsMiddleware);
app.get('*', notFoundHandler);

// ✅ Express v5 - Named wildcards required
app.use('/*path', corsMiddleware);
app.get('/*path', notFoundHandler);
```

#### New Optional Parameter Syntax
```javascript
// ❌ Express v4 - DEPRECATED in v5
app.get('/api/files/:name/:ext?', fileHandler);
app.get('/api/users/:id/posts/:postId?', postsHandler);

// ✅ Express v5 - New optional parameter syntax
app.get('/api/files/:name{/:ext}?', fileHandler);
app.get('/api/users/:id/posts{/:postId}?', postsHandler);
```

#### Reserved Characters Handling
```javascript
// ❌ Characters ()[]?+! are now reserved
app.get('/search/:query+', searchHandler); // May break
app.get('/user/:id(\\d+)', userHandler); // May break

// ✅ Alternative approaches
app.get('/search/:query*', searchHandler); // Use asterisk
app.get('/search/{:query+}', searchHandler); // Or wrap in braces

// Better: Move validation to middleware
app.get('/user/:id', validateUserId, userHandler);
```

## Basic Route Patterns

### CRUD Route Pattern
```javascript
/**
 * Standard CRUD Routes Pattern
 * Follows REST conventions with Express v5 syntax
 */
import express from 'express';
import {
  create,
  getById,
  update,
  delete as deleteResource,
  list
} from '../controllers/resource.controller.js';

const router = express.Router();

/**
 * @swagger
 * /api/resources:
 *   post:
 *     summary: Create new resource
 *     tags: [Resources]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/CreateResourceRequest'
 *     responses:
 *       201:
 *         description: Resource created successfully
 *       400:
 *         description: Validation error
 */
router.post('/', create);

/**
 * @swagger
 * /api/resources:
 *   get:
 *     summary: List resources with pagination
 *     tags: [Resources]
 *     parameters:
 *       - in: query
 *         name: page
 *         schema:
 *           type: integer
 *           minimum: 1
 *         description: Page number
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           minimum: 1
 *           maximum: 100
 *         description: Items per page
 *     responses:
 *       200:
 *         description: Resources retrieved successfully
 */
router.get('/', list);

/**
 * @swagger
 * /api/resources/{id}:
 *   get:
 *     summary: Get resource by ID
 *     tags: [Resources]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *           pattern: '^[0-9a-fA-F]{24}$'
 *         description: Resource ID
 *     responses:
 *       200:
 *         description: Resource retrieved successfully
 *       404:
 *         description: Resource not found
 */
router.get('/:id', getById);

/**
 * @swagger
 * /api/resources/{id}:
 *   put:
 *     summary: Update resource
 *     tags: [Resources]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/UpdateResourceRequest'
 *     responses:
 *       200:
 *         description: Resource updated successfully
 */
router.put('/:id', update);

/**
 * @swagger
 * /api/resources/{id}:
 *   delete:
 *     summary: Delete resource
 *     tags: [Resources]
 *     parameters:
 *       - in: path
 *         name: id
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: Resource deleted successfully
 */
router.delete('/:id', deleteResource);

export default router;
```

### Nested Resource Pattern
```javascript
/**
 * Nested Resource Pattern
 * For handling related resources (e.g., user posts, order items)
 */
import express from 'express';
import { 
  getUserPosts, 
  createUserPost, 
  getUserPost, 
  updateUserPost, 
  deleteUserPost 
} from '../controllers/user-posts.controller.js';

const router = express.Router({ mergeParams: true }); // Important for nested routes

// GET /api/users/:userId/posts
router.get('/', getUserPosts);

// POST /api/users/:userId/posts  
router.post('/', createUserPost);

// GET /api/users/:userId/posts/:postId
router.get('/:postId', getUserPost);

// PUT /api/users/:userId/posts/:postId
router.put('/:postId', updateUserPost);

// DELETE /api/users/:userId/posts/:postId
router.delete('/:postId', deleteUserPost);

export default router;
```

### Optional Parameter Pattern (Express v5)
```javascript
/**
 * Optional Parameter Pattern with Express v5 Syntax
 * Handles routes with optional segments
 */
import express from 'express';

const router = express.Router();

// ✅ Express v5 optional parameter syntax
// Matches both /api/files/document and /api/files/document/pdf
router.get('/files/:name{/:ext}?', (req, res) => {
  const { name, ext } = req.params;
  
  if (ext) {
    // Handle file with extension
    res.json({ 
      message: `Requested file: ${name}.${ext}`,
      name,
      extension: ext
    });
  } else {
    // Handle file without extension
    res.json({ 
      message: `Requested file: ${name}`,
      name,
      extension: null
    });
  }
});

// Multiple optional segments
// Matches /api/reports, /api/reports/2024, /api/reports/2024/january
router.get('/reports{/:year}{/:month}?', (req, res) => {
  const { year, month } = req.params;
  
  const filters = {};
  if (year) filters.year = year;
  if (month) filters.month = month;
  
  // Generate report based on filters
  res.json({
    message: 'Report generated',
    filters,
    data: generateReport(filters)
  });
});

export default router;
```

## Middleware Integration Patterns

### Route-Level Middleware
```javascript
/**
 * Route-Level Middleware Pattern
 * Apply middleware to specific routes
 */
import express from 'express';
import { authenticate, authorize } from '../middleware/auth.middleware.js';
import { rateLimit } from '../middleware/rate-limit.middleware.js';
import { auditLog } from '../middleware/audit.middleware.js';

const router = express.Router();

// Public route - no authentication required
router.get('/public', publicHandler);

// Authenticated route
router.get('/private', authenticate, privateHandler);

// Admin-only route with role-based access
router.get('/admin', authenticate, authorize(['admin']), adminHandler);

// Rate-limited route (stricter limits)
router.post('/contact',
  rateLimit({ max: 5, windowMs: 15 * 60 * 1000 }), // 5 requests per 15 minutes
  auditLog({ action: 'contact_form_submitted' }),
  contactHandler
);

// Multiple middleware with different purposes
router.post('/users', [
  authenticate,
  authorize(['admin', 'manager']),
  rateLimit({ max: 100, windowMs: 60 * 1000 }), // 100 requests per minute
  auditLog({ action: 'user_created', sensitive: true }),
  createUser
]);

export default router;
```

### Router-Level Middleware
```javascript
/**
 * Router-Level Middleware Pattern
 * Apply middleware to all routes in a router
 */
import express from 'express';
import { authenticate } from '../middleware/auth.middleware.js';
import { auditLog } from '../middleware/audit.middleware.js';

const router = express.Router();

// Apply authentication to all routes in this router
router.use(authenticate);

// Apply audit logging to all routes
router.use(auditLog({ resource: 'users' }));

// Now all routes below require authentication and are audited
router.get('/', getAllUsers);
router.post('/', createUser);
router.get('/:id', getUser);
router.put('/:id', updateUser);
router.delete('/:id', deleteUser);

export default router;
```

## Advanced Route Patterns

### File Upload Route Pattern
```javascript
/**
 * File Upload Route Pattern
 * Handles multipart form data and file validation
 */
import express from 'express';
import multer from 'multer';
import { authenticate } from '../middleware/auth.middleware.js';
import { FileController } from '../controllers/file.controller.js';

const router = express.Router();

// Configure multer for different file types
const imageUpload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
    cb(null, allowedTypes.includes(file.mimetype));
  }
});

const documentUpload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['application/pdf', 'application/msword', 'text/plain'];
    cb(null, allowedTypes.includes(file.mimetype));
  }
});

// Single file upload routes
router.post('/images', 
  authenticate,
  imageUpload.single('image'),
  FileController.uploadImage
);

router.post('/documents',
  authenticate, 
  documentUpload.single('document'),
  FileController.uploadDocument
);

// Multiple file upload
router.post('/gallery',
  authenticate,
  imageUpload.array('images', 10), // Max 10 images
  FileController.uploadGallery
);

// Mixed form data (files + other data)
router.post('/profile',
  authenticate,
  imageUpload.fields([
    { name: 'avatar', maxCount: 1 },
    { name: 'cover', maxCount: 1 }
  ]),
  FileController.updateProfile
);

export default router;
```

### Search and Filter Route Pattern
```javascript
/**
 * Search and Filter Route Pattern
 * Complex query parameters with validation
 */
import express from 'express';
import { SearchController } from '../controllers/search.controller.js';
import { validateSearchParams } from '../middleware/search.middleware.js';

const router = express.Router();

// Basic search
// GET /api/search?q=query&page=1&limit=20
router.get('/', validateSearchParams, SearchController.search);

// Advanced search with filters
// GET /api/search/advanced?q=query&category=electronics&minPrice=100&maxPrice=500
router.get('/advanced', validateSearchParams, SearchController.advancedSearch);

// Faceted search
// GET /api/search/facets?category=electronics
router.get('/facets', SearchController.getFacets);

// Search suggestions/autocomplete
// GET /api/search/suggest?q=partial_query
router.get('/suggest', SearchController.getSuggestions);

// Saved searches (authenticated users)
router.get('/saved', authenticate, SearchController.getSavedSearches);
router.post('/saved', authenticate, SearchController.saveSearch);
router.delete('/saved/:id', authenticate, SearchController.deleteSavedSearch);

export default router;
```

## Route Organization Patterns

### Domain-Based Organization
```javascript
/**
 * Domain-Based Route Organization
 * Group routes by business domain
 */

// src/api/v1.0/routes/index.js
import express from 'express';

// User management domain
import userRoutes from './users.routes.js';
import authRoutes from './auth.routes.js';
import profileRoutes from './profiles.routes.js';

// E-commerce domain  
import productRoutes from './products.routes.js';
import orderRoutes from './orders.routes.js';
import cartRoutes from './cart.routes.js';

// Content management domain
import postRoutes from './posts.routes.js';
import commentRoutes from './comments.routes.js';
import mediaRoutes from './media.routes.js';

// System/utility domain
import healthRoutes from './health.routes.js';
import adminRoutes from './admin.routes.js';

const router = express.Router();

// User Management Domain
router.use('/users', userRoutes);
router.use('/auth', authRoutes);  
router.use('/profiles', profileRoutes);

// E-commerce Domain
router.use('/products', productRoutes);
router.use('/orders', orderRoutes);
router.use('/cart', cartRoutes);

// Content Management Domain
router.use('/posts', postRoutes);
router.use('/comments', commentRoutes);
router.use('/media', mediaRoutes);

// System Domain
router.use('/health', healthRoutes);
router.use('/admin', adminRoutes);

export default router;
```

### Feature-Based Organization  
```javascript
/**
 * Feature-Based Route Organization
 * Routes organized by specific features
 */

// src/api/v1.0/routes/user-management.routes.js
import express from 'express';

const router = express.Router();

// User CRUD operations
router.get('/users', getAllUsers);
router.post('/users', createUser);
router.get('/users/:id', getUser);
router.put('/users/:id', updateUser);
router.delete('/users/:id', deleteUser);

// User authentication
router.post('/users/login', loginUser);
router.post('/users/logout', logoutUser);
router.post('/users/refresh', refreshToken);

// User profile management  
router.get('/users/:id/profile', getUserProfile);
router.put('/users/:id/profile', updateUserProfile);
router.post('/users/:id/avatar', uploadAvatar);

// User preferences
router.get('/users/:id/preferences', getUserPreferences);
router.put('/users/:id/preferences', updateUserPreferences);

export default router;
```

## Error Handling in Routes

### Route Error Patterns
```javascript
/**
 * Route-Level Error Handling Patterns
 */
import express from 'express';
import { asyncHandler } from '../../../utils/async.handler.js';

const router = express.Router();

// Route with proper async error handling
router.get('/users/:id', asyncHandler(async (req, res, next) => {
  try {
    const { id } = req.params;
    
    // Input validation at route level
    if (!id || !/^[0-9a-fA-F]{24}$/.test(id)) {
      return res.status(400).json({
        status: 'error',
        message: 'Valid user ID is required',
        code: 'INVALID_USER_ID'
      });
    }

    const user = await userService.findById(id);
    
    return req.context.success(res, 'User retrieved successfully', user);
    
  } catch (error) {
    // Pass error to global error handler
    next(error);
  }
}));

// Route with async error handling
router.post('/users',
  asyncHandler(async (req, res, next) => {
    try {
      const user = await userService.create(req.body);
      return req.context.success(res, 'User created successfully', user, 201);
    } catch (error) {
      next(error);
    }
  })
);
```

## Route Testing Patterns

### Route Integration Tests
```javascript
/**
 * Route Testing Pattern
 * Integration tests for route behavior
 */
// tests/integration/routes/users.routes.test.js
import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import request from 'supertest';
import { app } from '../../../src/app.js';

describe('User Routes', () => {
  let testUser;

  beforeEach(async () => {
    // Setup test data
    testUser = await createTestUser();
  });

  afterEach(async () => {
    // Cleanup test data
    await cleanupTestData();
  });

  describe('GET /api/users/:id', () => {
    it('should return user for valid ID', async () => {
      const response = await request(app)
        .get(`/api/users/${testUser._id}`)
        .expect(200);

      assert.strictEqual(response.body.status, 'success');
      assert.strictEqual(response.body.data._id, testUser._id.toString());
    });

    it('should return 400 for invalid ID format', async () => {
      const response = await request(app)
        .get('/api/users/invalid-id')
        .expect(400);

      assert.strictEqual(response.body.status, 'error');
      assert.strictEqual(response.body.code, 'VALIDATION_ERROR');
    });

    it('should return 404 for non-existent user', async () => {
      const nonExistentId = '507f1f77bcf86cd799439011';
      
      const response = await request(app)
        .get(`/api/users/${nonExistentId}`)
        .expect(404);

      assert.strictEqual(response.body.code, 'RESOURCE_NOT_FOUND');
    });
  });

  describe('Express v5 Compliance', () => {
    it('should handle optional parameters correctly', async () => {
      // Test route: /api/files/:name{/:ext}?
      
      // Without optional parameter
      const response1 = await request(app)
        .get('/api/files/document')
        .expect(200);
      
      assert.ok(response1.body.data.name);
      assert.strictEqual(response1.body.data.extension, null);
      
      // With optional parameter
      const response2 = await request(app)
        .get('/api/files/document/pdf')
        .expect(200);
      
      assert.ok(response2.body.data.name);
      assert.strictEqual(response2.body.data.extension, 'pdf');
    });

    it('should handle named wildcards correctly', async () => {
      // Test catch-all route with named wildcard
      const response = await request(app)
        .get('/api/some/unknown/path')
        .expect(404);

      // Should be handled by /*path catch-all
      assert.strictEqual(response.body.status, 'error');
    });
  });
});
```

## Best Practices

### ✅ Route Best Practices

1. **Use Express v5 Syntax**: Always use named wildcards and new optional parameter syntax
2. **Header-Based Versioning**: Never expose version numbers in URLs
3. **RESTful Conventions**: Follow REST principles for URL structure
4. **Consistent Middleware**: Apply middleware consistently across similar routes
5. **Proper HTTP Methods**: Use appropriate HTTP methods for different operations
6. **Input Validation**: Validate parameters and body data
7. **Error Handling**: Use asyncHandler and pass errors to middleware
8. **Documentation**: Add Swagger/OpenAPI documentation to routes
9. **Testing**: Write integration tests for all route behaviors

### ❌ Route Anti-Patterns

1. **Express v4 Syntax**
   ```javascript
   // Wrong - will break in Express v5
   app.use('*', middleware);
   app.get('/files/:name/:ext?', handler);
   ```

2. **URL Versioning**
   ```javascript
   // Wrong - breaks versioning contract
   app.use('/api/v1.0/users', userRoutes);
   ```

3. **Business Logic in Routes**
   ```javascript
   // Wrong - business logic should be in services
   app.post('/users', async (req, res) => {
     const user = await User.create(req.body);
     await sendWelcomeEmail(user.email);
     res.json(user);
   });
   ```

4. **Inconsistent Route Patterns**
   ```javascript
   // Wrong - inconsistent patterns
   app.get('/getUser/:id', handler);     // Not RESTful
   app.post('/user/create', handler);    // Inconsistent with REST
   ```

Remember: Routes should be thin layers that handle HTTP concerns while maintaining Express v5 compliance and following RESTful conventions consistently throughout the WAIF framework.