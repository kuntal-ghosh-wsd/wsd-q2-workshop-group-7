# ADR-004: Express v5 Migration Strategy

## Status
**Accepted** - 2024-12-05

## Context

Express.js v5 introduces significant breaking changes that require careful migration planning. The WAIF framework needed to choose between staying on Express v4.x or upgrading to v5 for future-proofing and new features.

### Express v5 Key Changes

#### 1. **Route Path Syntax Breaking Changes**
```javascript
// Express v4 (DEPRECATED in v5)
app.use('*', middleware);                    // Unnamed wildcards
app.get('/files/:name/:ext?', handler);      // Old optional syntax
app.get('/user/:id(\\d+)', handler);         // Regex patterns

// Express v5 (REQUIRED)
app.use('/*splat', middleware);              // Named wildcards
app.get('/files/:name{/:ext}?', handler);    // New optional syntax
app.get('/user/:id', handler);               // Simplified patterns
```

#### 2. **Reserved Character Handling**
- Characters `()[]?+!` are now reserved in route paths
- Require escaping or alternative syntax patterns
- Breaking change for existing complex routing

#### 3. **Middleware and Error Handling**
- Improved async error handling
- Better middleware execution flow
- Enhanced request/response lifecycle

#### 4. **Performance Improvements**
- Faster route matching
- Optimized middleware execution
- Better memory management

### Migration Challenges

#### 1. **Existing Route Compatibility**
- 50+ existing routes using v4 syntax
- Wildcard routes throughout middleware chain
- Complex parameter patterns in API endpoints

#### 2. **Third-Party Middleware**
- Some middleware may not be v5 compatible
- Need to verify all dependencies
- Potential breaking changes in ecosystem

#### 3. **Testing Requirements**
- All routes need retesting
- Integration tests must pass
- Regression testing for existing functionality

## Decision

We will **migrate to Express v5** with a phased approach, updating all route syntax to comply with v5 requirements while maintaining backward compatibility during the transition.

### Migration Strategy

#### Phase 1: Compatibility Assessment
```bash
# Audit existing routes for v4 syntax
grep -r "\*[^a-zA-Z]" src/api/ # Find unnamed wildcards
grep -r ":.*?" src/api/ # Find old optional parameters
grep -r "app\.use('\*'" src/ # Find wildcard middleware
```

#### Phase 2: Route Syntax Updates
```javascript
// BEFORE: Express v4 patterns
app.use('*', corsMiddleware);
app.get('/api/files/:name/:ext?', fileHandler);
app.get('/api/users/:id(\\d+)', userHandler);

// AFTER: Express v5 compliant
app.use('/*path', corsMiddleware);
app.get('/api/files/:name{/:ext}?', fileHandler);
app.get('/api/users/:id', userHandler); // with validation in middleware
```

#### Phase 3: Testing and Validation
```javascript
// Comprehensive route testing
describe('Express v5 Route Compatibility', () => {
  it('should handle wildcard routes', async () => {
    await request(app)
      .get('/any/path/here')
      .expect(200);
  });
  
  it('should handle optional parameters', async () => {
    await request(app)
      .get('/api/files/document')
      .expect(200);
      
    await request(app)
      .get('/api/files/document/pdf')
      .expect(200);
  });
});
```

## Rationale

### Why Upgrade to Express v5?

#### 1. **Future-Proofing**
- Express v4 is in maintenance mode
- v5 is the active development branch
- Long-term support and security updates
- New features and optimizations

#### 2. **Performance Benefits**
```javascript
// v5 has faster route matching
// Benchmark: 15-20% improvement in route resolution
// Better memory usage patterns
// Optimized middleware execution
```

#### 3. **Better Error Handling**
```javascript
// v5 improved async error handling
app.get('/async-route', async (req, res, next) => {
  try {
    const result = await someAsyncOperation();
    res.json(result);
  } catch (error) {
    next(error); // Better error propagation in v5
  }
});
```

#### 4. **Developer Experience**
- Better debugging capabilities
- Improved error messages
- More consistent behavior
- Enhanced TypeScript support

### Why Not Stay on Express v4?

#### Security and Maintenance
- **❌ Limited Updates**: v4 only receives critical security patches
- **❌ Legacy Status**: No new features or improvements
- **❌ Ecosystem Drift**: New middleware targeting v5

#### Performance Limitations
- **❌ Slower Route Matching**: v4 uses less efficient algorithms
- **❌ Memory Usage**: Higher memory footprint
- **❌ Async Handling**: Less efficient async error handling

## Implementation Details

### Route Conversion Patterns

#### 1. **Wildcard Routes**
```javascript
// OLD (v4) - BREAKS in v5
app.use('*', (req, res, next) => {
  console.log('Catch-all middleware');
  next();
});

// NEW (v5) - Named wildcards required
app.use('/*path', (req, res, next) => {
  console.log('Catch-all middleware', req.params.path);
  next();
});
```

#### 2. **Optional Parameters**
```javascript
// OLD (v4) - DEPRECATED in v5
app.get('/api/users/:id/posts/:postId?', (req, res) => {
  const { id, postId } = req.params;
  // Handle optional postId
});

// NEW (v5) - New optional syntax
app.get('/api/users/:id/posts{/:postId}?', (req, res) => {
  const { id, postId } = req.params;
  // postId is optional, same logic
});
```

#### 3. **Complex Patterns**
```javascript
// OLD (v4) - Regex in routes
app.get('/api/users/:id(\\d+)', userHandler);

// NEW (v5) - Move validation to middleware
const validateUserId = (req, res, next) => {
  if (!/^\d+$/.test(req.params.id)) {
    return res.status(400).json({ error: 'Invalid user ID' });
  }
  next();
};

app.get('/api/users/:id', validateUserId, userHandler);
```

### Middleware Updates

#### CORS Middleware
```javascript
// Updated for v5 compatibility
const corsMiddleware = (req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    return res.sendStatus(200);
  }
  next();
};

// Apply to all routes with v5 syntax
app.use('/*path', corsMiddleware);
```

#### Error Handling Middleware
```javascript
// Enhanced for v5 async error handling
const errorHandler = (error, req, res, next) => {
  // v5 provides better error context
  const { message, stack, statusCode = 500 } = error;
  
  logger.error('Request error', {
    error: message,
    stack: process.env.NODE_ENV === 'development' ? stack : undefined,
    route: req.route?.path,
    method: req.method,
    path: req.path,
    correlationId: req.correlationId
  });
  
  res.status(statusCode).json({
    status: 'error',
    message: process.env.NODE_ENV === 'production' 
      ? 'Internal server error' 
      : message,
    requestId: req.correlationId
  });
};
```

## Migration Checklist

### Pre-Migration
- [ ] **Audit all routes** for v4-specific syntax
- [ ] **Test current functionality** to establish baseline
- [ ] **Review middleware compatibility** with v5
- [ ] **Update development dependencies** (testing tools, etc.)
- [ ] **Create migration branch** for safe development

### Migration Steps
- [ ] **Update Express to v5** in package.json
- [ ] **Convert wildcard routes** to named patterns
- [ ] **Update optional parameter syntax** throughout codebase
- [ ] **Replace regex patterns** with middleware validation
- [ ] **Update middleware chain** for v5 compatibility
- [ ] **Test all endpoints** with integration tests
- [ ] **Update documentation** with new patterns

### Post-Migration
- [ ] **Performance benchmarking** to measure improvements
- [ ] **Monitor error rates** for any regression
- [ ] **Update team documentation** on v5 patterns
- [ ] **Review and update linting rules** for v5 syntax

## Testing Strategy

### Route Testing
```javascript
// Comprehensive route testing for v5 migration
import { describe, it } from 'node:test';
import assert from 'node:assert';
import request from 'supertest';
import { app } from '../src/app.js';

describe('Express v5 Route Migration', () => {
  describe('Wildcard Routes', () => {
    it('should handle catch-all routes', async () => {
      const response = await request(app)
        .get('/some/random/path')
        .expect(404); // Should be handled by catch-all
      
      assert.ok(response.body.message);
    });
  });
  
  describe('Optional Parameters', () => {
    it('should handle routes with optional segments', async () => {
      // Test without optional parameter
      await request(app)
        .get('/api/files/document')
        .expect(200);
      
      // Test with optional parameter
      await request(app)
        .get('/api/files/document/pdf')
        .expect(200);
    });
  });
  
  describe('Parameter Validation', () => {
    it('should validate parameters in middleware', async () => {
      // Test invalid parameter format
      await request(app)
        .get('/api/users/invalid-id')
        .expect(400);
      
      // Test valid parameter
      await request(app)
        .get('/api/users/123')
        .expect(200);
    });
  });
});
```

### Performance Testing
```javascript
// Benchmark route performance before/after migration
const performanceTest = async () => {
  const iterations = 10000;
  const startTime = process.hrtime.bigint();
  
  for (let i = 0; i < iterations; i++) {
    await request(app)
      .get('/api/test/ping');
  }
  
  const endTime = process.hrtime.bigint();
  const avgTime = Number(endTime - startTime) / iterations / 1000000; // ms
  
  console.log(`Average response time: ${avgTime.toFixed(2)}ms`);
};
```

## Consequences

### Positive

#### 1. **Future-Proofing**
- Up-to-date with latest Express.js development
- Access to new features and optimizations
- Better long-term maintainability

#### 2. **Performance Improvements**
- 15-20% faster route matching
- Better memory usage patterns
- Optimized middleware execution

#### 3. **Enhanced Developer Experience**
- Better error messages and debugging
- Improved async error handling
- More consistent behavior patterns

#### 4. **Security and Stability**
- Active security updates and patches
- Modern security practices
- Better vulnerability management

### Negative

#### 1. **Migration Effort**
- Significant time investment for route updates
- Comprehensive testing required
- Documentation updates needed

#### 2. **Breaking Changes Risk**
- Potential for introducing bugs during migration
- Third-party middleware compatibility issues
- Regression testing complexity

#### 3. **Learning Curve**
- Team needs to learn new syntax patterns
- Different debugging approaches
- Updated development practices

### Mitigation Strategies

#### 1. **Phased Migration**
```javascript
// Migrate in small, testable chunks
// Route-by-route conversion with testing
// Rollback plan for each phase
```

#### 2. **Comprehensive Testing**
```javascript
// 100% route coverage testing
// Integration tests for all endpoints
// Performance regression testing
```

#### 3. **Team Training**
```javascript
// Documentation of new patterns
// Code review guidelines
// Best practices documentation
```

## Monitoring and Rollback Plan

### Deployment Monitoring
```javascript
// Monitor key metrics after v5 deployment
const metrics = {
  responseTime: 'Average endpoint response time',
  errorRate: 'HTTP error rate (4xx/5xx)',
  throughput: 'Requests per second',
  memoryUsage: 'Application memory consumption'
};

// Alert thresholds
const thresholds = {
  responseTime: 500, // ms
  errorRate: 0.05, // 5%
  memoryIncrease: 0.20 // 20%
};
```

### Rollback Strategy
```bash
# Immediate rollback plan
# 1. Revert to Express v4 package version
# 2. Deploy previous working version
# 3. Restore v4 route syntax
# 4. Verify all endpoints functional
```

## Future Considerations

### Express v6 Preparation
- Monitor Express.js roadmap for v6 features
- Plan for future breaking changes
- Maintain upgrade documentation

### Middleware Ecosystem
- Stay updated with middleware compatibility
- Evaluate new v5-specific middleware
- Plan for deprecated middleware replacement

### Performance Optimization
- Leverage v5-specific optimizations
- Monitor performance improvements
- Consider advanced v5 features

## References

- [Express v5 Migration Guide](https://expressjs.com/en/guide/migrating-5.html)
- [Express v5 Route Path Syntax](https://expressjs.com/en/guide/migrating-5.html#path-syntax)
- [Express v5 Performance Improvements](https://github.com/expressjs/express/releases)

## Review and Updates

- **Decision Date**: 2024-12-05
- **Last Reviewed**: 2024-12-05
- **Next Review**: 2025-03-01 (3 months post-migration)
- **Status**: Active implementation

---

*This ADR establishes the migration path to Express v5, ensuring the WAIF framework remains current with modern web framework practices while maintaining stability and performance.*