# ADR-002: Singleton Service Pattern for Database Connections

## Status
**Accepted** - 2024-12-05

## Context

Database and external service connections in Node.js applications require careful management to avoid resource leaks, connection pool exhaustion, and performance issues. We needed to establish a pattern for managing these connections across the WAIF framework.

### Problem Statement
- Multiple service instances creating redundant database connections
- Connection pool fragmentation across different service instances
- Difficulty in managing connection lifecycle and cleanup
- Inconsistent connection configuration across services
- Resource waste and potential connection limit exhaustion

### Service Types Requiring Connection Management
1. **MongoDB Service** - Document database operations
2. **Redis Service** - Caching and session storage
3. **External API Services** - Third-party integrations
4. **Email Service** - SMTP connections
5. **File Storage Service** - Cloud storage connections

### Current Architecture Constraints
- Node.js single-threaded event loop
- Limited database connection pools (MongoDB: ~100 connections)
- Redis connection limits
- Memory efficiency requirements
- Need for graceful connection cleanup on shutdown

## Decision

We will implement the **Singleton Pattern** for all database and external service connections, ensuring a single instance per service type manages all connections for the application.

### Implementation Strategy

#### Core Singleton Pattern
```javascript
// Base singleton implementation
class ServiceSingleton {
  constructor() {
    if (this.constructor.instance) {
      return this.constructor.instance;
    }
    this.constructor.instance = this;
  }

  static getInstance() {
    if (!this.instance) {
      this.instance = new this();
    }
    return this.instance;
  }
}
```

#### MongoDB Service Singleton
```javascript
export class MongoDBService extends ServiceSingleton {
  constructor() {
    super();
    this.client = null;
    this.db = null;
    this.isConnected = false;
    this.connectionPromise = null;
  }

  async connect() {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.connectionPromise = this._establishConnection();
    return this.connectionPromise;
  }

  async _establishConnection() {
    if (this.isConnected) return this.client;

    this.client = new MongoClient(config.mongodb.uri, {
      maxPoolSize: 100,
      minPoolSize: 5,
      maxIdleTimeMS: 30000,
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
    });

    await this.client.connect();
    this.db = this.client.db(config.mongodb.database);
    this.isConnected = true;
    
    return this.client;
  }
}
```

#### Redis Service Singleton
```javascript
export class RedisService extends ServiceSingleton {
  constructor() {
    super();
    this.client = null;
    this.isConnected = false;
    this.connectionPromise = null;
  }

  async connect() {
    if (this.connectionPromise) {
      return this.connectionPromise;
    }

    this.connectionPromise = this._establishConnection();
    return this.connectionPromise;
  }

  async _establishConnection() {
    if (this.isConnected) return this.client;

    this.client = redis.createClient({
      url: config.redis.url,
      retry_strategy: (options) => {
        if (options.error && options.error.code === 'ECONNREFUSED') {
          return new Error('Redis server connection refused');
        }
        if (options.total_retry_time > 1000 * 60 * 60) {
          return new Error('Redis retry time exhausted');
        }
        return Math.min(options.attempt * 100, 3000);
      }
    });

    await this.client.connect();
    this.isConnected = true;
    
    return this.client;
  }
}
```

## Rationale

### Why Singleton Pattern?

#### 1. **Resource Efficiency**
```javascript
// ❌ Without Singleton - Multiple instances, multiple connections
const userService = new UserService(); // Creates MongoDB connection
const orderService = new OrderService(); // Creates another MongoDB connection
const productService = new ProductService(); // Creates yet another connection

// ✅ With Singleton - Single connection shared
const mongoService = MongoDBService.getInstance(); // Single connection
// All services use the same connection pool
```

#### 2. **Connection Pool Management**
- **Optimal Pool Usage**: Single pool manages all connections efficiently
- **Prevents Pool Fragmentation**: Avoids splitting connections across instances
- **Resource Limits Compliance**: Stays within database connection limits
- **Performance Optimization**: Better connection reuse and caching

#### 3. **Configuration Consistency**
```javascript
// All services use same connection configuration
const mongoService = MongoDBService.getInstance();
// Connection settings applied once, used everywhere
```

#### 4. **Graceful Shutdown Management**
```javascript
// Single point to manage connection lifecycle
process.on('SIGTERM', async () => {
  const mongoService = MongoDBService.getInstance();
  const redisService = RedisService.getInstance();
  
  await mongoService.disconnect();
  await redisService.disconnect();
  process.exit(0);
});
```

### Why Not Other Patterns?

#### Dependency Injection Container
- **❌ Complexity**: Additional framework overhead
- **❌ Over-engineering**: Simple connection management doesn't need DI container
- **❌ Learning Curve**: Team familiarity with singleton pattern

#### Factory Pattern
- **❌ Instance Management**: Still need to manage single instance manually
- **❌ Connection Duplication**: Doesn't prevent multiple connections
- **❌ Resource Waste**: Can create unnecessary instances

#### Module Singleton (CommonJS)
- **❌ ESM Incompatibility**: We use ES modules throughout
- **❌ Testing Difficulty**: Harder to mock and reset for tests
- **❌ Import Complexity**: Less explicit than class-based singletons

## Implementation Details

### Connection Initialization
```javascript
// Lazy initialization - connect when first needed
export class MongoDBService extends ServiceSingleton {
  async create(collection, document) {
    if (!this.isConnected) {
      await this.connect();
    }
    return this.db.collection(collection).insertOne(document);
  }
}
```

### Error Handling and Reconnection
```javascript
export class MongoDBService extends ServiceSingleton {
  async executeWithRetry(operation, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        if (!this.isConnected) {
          await this.connect();
        }
        return await operation();
      } catch (error) {
        if (this.isConnectionError(error) && attempt < maxRetries) {
          this.isConnected = false;
          this.connectionPromise = null;
          await this.wait(1000 * attempt); // Exponential backoff
          continue;
        }
        throw error;
      }
    }
  }

  isConnectionError(error) {
    const connectionErrors = [
      'ECONNREFUSED', 'ENOTFOUND', 'ETIMEDOUT',
      'MongoNetworkError', 'MongoServerSelectionError'
    ];
    return connectionErrors.some(code => 
      error.code === code || error.name === code
    );
  }
}
```

### Testing Support
```javascript
// Test helper to reset singleton instances
export class TestHelpers {
  static resetSingletons() {
    MongoDBService.instance = null;
    RedisService.instance = null;
  }

  static async cleanupConnections() {
    const mongoService = MongoDBService.getInstance();
    const redisService = RedisService.getInstance();
    
    if (mongoService.isConnected) {
      await mongoService.disconnect();
    }
    if (redisService.isConnected) {
      await redisService.disconnect();
    }
  }
}
```

## Consequences

### Positive

#### 1. **Resource Optimization**
- Single connection pool per service type
- Optimal memory usage
- Reduced connection overhead
- Better performance under load

#### 2. **Simplified Management**
- Single point of configuration
- Centralized error handling
- Unified connection lifecycle
- Easier monitoring and debugging

#### 3. **Consistency**
- Same connection settings across all usage
- Predictable behavior
- Standardized error handling
- Unified logging and monitoring

#### 4. **Performance Benefits**
- Connection pool reuse
- Reduced connection establishment overhead
- Better caching at connection level
- Optimized resource utilization

### Negative

#### 1. **Testing Complexity**
- Need to reset singletons between tests
- Potential test isolation issues
- Mocking requires additional setup

#### 2. **Global State**
- Hidden dependencies (services depend on singleton state)
- Potential coupling between unrelated components
- Debugging can be more complex

#### 3. **Concurrent Access**
- Need to handle concurrent initialization properly
- Race conditions during startup
- Connection state management complexity

### Mitigation Strategies

#### 1. **Testing Support**
```javascript
// Clear test setup
beforeEach(() => {
  TestHelpers.resetSingletons();
});

afterEach(async () => {
  await TestHelpers.cleanupConnections();
});
```

#### 2. **Explicit Dependencies**
```javascript
// Make singleton dependency explicit in service constructors
export class UserService {
  constructor(mongoService = MongoDBService.getInstance()) {
    this.mongoService = mongoService;
  }
}
```

#### 3. **Health Monitoring**
```javascript
// Health check endpoint to monitor singleton connections
export const healthCheck = async () => {
  const mongoService = MongoDBService.getInstance();
  const redisService = RedisService.getInstance();
  
  return {
    mongodb: {
      connected: mongoService.isConnected,
      poolSize: mongoService.client?.topology?.s?.servers?.size || 0
    },
    redis: {
      connected: redisService.isConnected,
      status: redisService.client?.status || 'disconnected'
    }
  };
};
```

## Best Practices

### 1. **Initialization Pattern**
```javascript
// Always use lazy initialization
class ServiceSingleton {
  async ensureConnected() {
    if (!this.isConnected) {
      await this.connect();
    }
  }
}
```

### 2. **Error Handling**
```javascript
// Implement connection recovery
async operation() {
  try {
    await this.ensureConnected();
    return await this.performOperation();
  } catch (error) {
    if (this.isConnectionError(error)) {
      this.resetConnection();
    }
    throw error;
  }
}
```

### 3. **Graceful Shutdown**
```javascript
// Implement proper cleanup
async disconnect() {
  if (this.client) {
    await this.client.close();
    this.client = null;
    this.isConnected = false;
    this.connectionPromise = null;
  }
}
```

## Monitoring and Observability

### Connection Metrics
```javascript
export class MongoDBService extends ServiceSingleton {
  getConnectionMetrics() {
    return {
      totalConnections: this.client?.topology?.s?.servers?.size || 0,
      activeConnections: this.client?.topology?.s?.pool?.totalConnectionCount || 0,
      availableConnections: this.client?.topology?.s?.pool?.availableConnectionCount || 0,
      connectionErrors: this.connectionErrorCount || 0,
      lastConnectionTime: this.lastConnectionTime
    };
  }
}
```

### Health Monitoring
```javascript
// Regular health checks in production
setInterval(async () => {
  try {
    const mongoService = MongoDBService.getInstance();
    await mongoService.ping();
  } catch (error) {
    logger.error('MongoDB health check failed', { error: error.message });
    // Trigger alerts/monitoring
  }
}, 30000); // Every 30 seconds
```

## Future Considerations

### 1. **Microservices Evolution**
- Each service might need its own database connections
- Consider service-specific connection configurations
- Plan for distributed singleton patterns

### 2. **Connection Pooling Evolution**
- Monitor connection pool usage patterns
- Adjust pool sizes based on metrics
- Consider dynamic pool sizing

### 3. **Multi-Database Support**
- Extend singleton pattern for multiple databases
- Database-specific singleton instances
- Cross-database transaction support

## References

- [MongoDB Connection Pool Best Practices](https://docs.mongodb.com/manual/administration/connection-pool-overview/)
- [Node.js Singleton Pattern](https://nodejs.org/en/docs/guides/nodejs-docker-webapp/)
- [Redis Connection Management](https://redis.io/docs/manual/clients/)

## Review and Updates

- **Decision Date**: 2024-12-05
- **Last Reviewed**: 2024-12-05  
- **Next Review**: 2025-03-01 (3 months)
- **Status**: Active implementation

---

*This ADR establishes the singleton pattern as the standard for all database and external service connections in the WAIF framework, ensuring efficient resource usage and consistent connection management.*