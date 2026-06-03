# TypeScript Configuration - WAIF Framework

## Overview

This guide covers TypeScript configuration and best practices for the WAIF (Web Application Integration Framework) codebase. The framework uses:

- **Node.js 24+** with native ESM support
- **Express v5** with async route handlers
- **Strict type checking** for maximum type safety
- **Single project architecture** (not a monorepo)

## Migration Scope

When migrating to TypeScript:

- **Include**: All code in `src/`, `tests/`, and root configuration files
- **Exclude**: The `autocoder` directory and any code within it
- **Future**: After merging `pipeline/autocoder-updates` branch, convert that code separately

## Configuration

### Root Configuration (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "target": "ES2024",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2024"],
    "outDir": "./dist",
    "rootDir": "./src",
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "useUnknownInCatchVariables": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "allowJs": true,
    "checkJs": false,
    "skipLibCheck": true,
    "incremental": true
  },
  "include": ["src/**/*"],
  "exclude": [
    "node_modules",
    "dist",
    "tests",
    "coverage",
    "docker",
    "migrations",
    "src/api/v1.0/pipelines/autocoder/**/*"
  ]
}
```

### Test Configuration (`tsconfig.test.json`)

```json
{
  "extends": "./tsconfig.json",
  "compilerOptions": {
    "rootDir": ".",
    "outDir": "./dist-tests",
    "noEmit": true,
    "declaration": false,
    "declarationMap": false
  },
  "include": ["src/**/*", "tests/**/*"],
  "exclude": [
    "node_modules",
    "dist",
    "dist-tests",
    "coverage",
    "src/api/v1.0/pipelines/autocoder/**/*"
  ]
}
```

### Key Compiler Options Explained

| Option | Value | Purpose |
|--------|-------|---------|
| `target` | ES2024 | Latest stable ES features for Node.js 24 |
| `module` | NodeNext | Native ESM with `.js` extension support |
| `moduleResolution` | NodeNext | Follows Node.js ESM resolution algorithm |
| `strict` | true | Enables all strict type-checking options |
| `allowJs` | true | Allows gradual migration from JavaScript |
| `checkJs` | false | Don't type-check JS files during migration |
| `noUncheckedIndexedAccess` | true | Adds `undefined` to indexed access types |
| `exactOptionalPropertyTypes` | true | Distinguishes `undefined` from optional |
| `isolatedModules` | true | Ensures each file can be transpiled independently |
| `incremental` | true | Enables incremental compilation for faster builds |
| `skipLibCheck` | true | Faster builds, skip `.d.ts` checking |

## Required Dependencies

### Production Dependencies

```bash
npm install typescript tsx --save-dev
```

### Type Definitions

```bash
npm install --save-dev \
  @types/node \
  @types/express \
  @types/cors \
  @types/compression \
  @types/multer \
  @types/mime
```

### Test Type Definitions

```bash
npm install --save-dev @types/sinon
```

### Packages with Built-in Types (No @types needed)

- `mongodb` (v6.x) - Native TypeScript support
- `redis` (v5.x client for Redis 7.x servers) - Native TypeScript support
- `pino` (v9.x) - Native TypeScript support
- `openai` (v6.x) - Native TypeScript support
- `helmet` - Native TypeScript support

## Build Scripts

The project uses these TypeScript-related scripts in `package.json`:

```json
{
  "scripts": {
    "format": "prettier --write \"src/**/*.{js,ts}\" \"tests/**/*.{js,ts}\"",
    "lint": "eslint \"src/**/*.{js,ts}\" \"tests/**/*.{js,ts}\" --ignore-pattern \"**/test-harness/**/*\"",
    "quality": "npm run format && npm run lint -- --fix",
    "type-check": "tsc --noEmit",
    "type-check:watch": "tsc --noEmit --watch",
    "build:ts": "tsc",
    "build:ts:watch": "tsc --watch",
    "test:unit": "cross-env NODE_ENV=test npx c8 node --test --test-force-exit \"tests/unit/**/*.test.{js,ts}\"",
    "test:integration": "cross-env NODE_ENV=test node --test tests/integration/**/*.test.{js,ts}",
    "dev": "nodemon --watch src index.js",
    "start": "node index.js"
  }
}
```

**Note**: Use `build:ts` for TypeScript compilation (separate from Docker build). During hybrid JS/TS, `dev` runs against `index.js`; switch to `tsx watch src/index.ts` only after the entrypoint is converted.

## Type Definitions for WAIF Framework

### Express Request Augmentation

Create `src/types/express.d.ts`:

```typescript
import type { Logger } from 'pino';

declare global {
  namespace Express {
    interface Request {
      context: RequestContext;
      requestId: string;
      correlationId: string;
    }
  }
}

export interface RequestContext {
  requestId: string;
  correlationId: string;
  logger: Logger;
  success: <T>(data: T, message?: string, statusCode?: number) => void;
  error: (message: string, statusCode?: number, details?: unknown) => void;
  paginated: <T>(data: T[], pagination: PaginationMeta) => void;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}
```

### Error Classes

Create `src/types/errors.d.ts`:

```typescript
export interface AppErrorOptions {
  message: string;
  statusCode?: number;
  isOperational?: boolean;
  cause?: Error;
}

export class AppError extends Error {
  statusCode: number;
  isOperational: boolean;
  cause?: Error;

  constructor(options: AppErrorOptions);
}

export class ValidationError extends AppError {
  constructor(message: string, cause?: Error);
}

export class NotFoundError extends AppError {
  constructor(message: string, cause?: Error);
}

export class DatabaseError extends AppError {
  constructor(message: string, cause?: Error);
}

export class ExternalServiceError extends AppError {
  constructor(message: string, cause?: Error);
}
```

### Pipeline System Types

Create `src/types/pipeline.d.ts`:

```typescript
import type { EventEmitter } from 'events';

// Packet Types
export interface PacketDefinition {
  id: string;
  mediaTypes: Record<string, MediaTypeHandler>;
}

export interface MediaTypeHandler {
  parser: (buffer: Buffer) => Promise<unknown>;
  serializer: (data: unknown) => Promise<Buffer>;
}

export interface Packet {
  id: string;
  data: Buffer | unknown;
  metadata: PacketMetadata;
  mediaType: string;
}

export interface PacketMetadata {
  filename?: string;
  originalName?: string;
  size?: number;
  encoding?: string;
  [key: string]: unknown;
}

// Stage Types
export type StageHandler = (context: InvocationContext) => Promise<void>;

export interface StageDefinition {
  id: string;
  handler: StageHandler;
}

// Graph Types
export interface GraphDefinition {
  nodes: Record<string, GraphNode>;
}

export interface GraphNode {
  stages: StageReference[];
  edges: GraphEdge[];
}

export interface StageReference {
  stageId: string;
}

export interface GraphEdge {
  node: string;
  condition: (context: InvocationContext) => Promise<boolean>;
}

// Invocation Context
export interface InvocationContext extends EventEmitter {
  // Packet operations
  getPacket(id: string): Promise<unknown>;
  getPacketMetadata(id: string): PacketMetadata | undefined;
  getPacketBuffer(id: string): Promise<Buffer>;
  addPacket(id: string, data: unknown, metadata?: PacketMetadata): void;
  hasPacket(id: string): boolean;
  getAvailablePackets(): string[];

  // Metadata operations
  setMetadata(key: string, value: unknown): void;
  getMetadata(key: string): unknown;
  getAllMetadata(): Record<string, unknown>;

  // Execution tracking
  logStageStart(stageId: string): string;
  logStageEnd(invocationId: string, metadata?: Record<string, unknown>): void;
  getStats(): ExecutionStats;

  // Services
  services: ServiceProxy;

  // Cleanup
  cleanup(): Promise<void>;
}

export interface ExecutionStats {
  startTime: number;
  endTime?: number;
  duration?: number;
  stagesExecuted: number;
  packetsProcessed: number;
}

// Service Proxy
export interface ServiceProxy {
  chatCompletion(options: ChatCompletionOptions): Promise<ChatCompletionResponse>;
}

export interface ChatCompletionOptions {
  messages: ChatMessage[];
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  name?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
}

export interface ChatCompletionResponse {
  id: string;
  choices: ChatChoice[];
  usage: TokenUsage;
}

export interface ChatChoice {
  index: number;
  message: ChatMessage;
  finish_reason: string;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

// Pipeline Class
export interface PipelineOptions {
  name: string;
  description?: string;
}

export interface PipelineMetadata {
  name: string;
  description?: string;
  packets: PacketDefinition[];
  stages: string[];
  graphs: string[];
}
```

### Service Types

Create `src/types/services.d.ts`:

```typescript
import type { Db, Collection, Document, Filter, UpdateFilter, FindOptions } from 'mongodb';
import type { RedisClientType } from 'redis';

// MongoDB Service
export interface MongoDBService {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  getDb(): Db;
  getCollection<T extends Document>(name: string): Collection<T>;

  // CRUD operations
  findOne<T extends Document>(
    collection: string,
    filter: Filter<T>,
    options?: FindOptions
  ): Promise<T | null>;

  findMany<T extends Document>(
    collection: string,
    filter: Filter<T>,
    options?: FindOptions
  ): Promise<T[]>;

  insertOne<T extends Document>(
    collection: string,
    document: T
  ): Promise<string>;

  updateOne<T extends Document>(
    collection: string,
    filter: Filter<T>,
    update: UpdateFilter<T>
  ): Promise<boolean>;

  deleteOne<T extends Document>(
    collection: string,
    filter: Filter<T>
  ): Promise<boolean>;

  // Transaction support
  withTransaction<T>(
    callback: (session: unknown) => Promise<T>
  ): Promise<T>;
}

// Redis Service
export interface RedisService {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  getClient(): RedisClientType;

  // Key-value operations
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, ttl?: number): Promise<void>;
  del(key: string): Promise<void>;
  exists(key: string): Promise<boolean>;

  // Hash operations
  hGet<T>(key: string, field: string): Promise<T | null>;
  hSet<T>(key: string, field: string, value: T): Promise<void>;
  hGetAll<T>(key: string): Promise<Record<string, T>>;

  // Utility
  keys(pattern: string): Promise<string[]>;
  ttl(key: string): Promise<number>;
}

// LiteLLM Service
export interface LiteLLMService {
  chatCompletion(options: ChatCompletionOptions): Promise<ChatCompletionResponse>;
  getUsageStats(): UsageStats;
}

export interface UsageStats {
  totalCalls: number;
  totalTokens: number;
  promptTokens: number;
  completionTokens: number;
}
```

### Multipart Request/Response Types

Create `src/types/multipart.d.ts`:

```typescript
import type { Request } from 'express';

export interface MulterFile {
  fieldname: string;
  originalname: string;
  encoding: string;
  mimetype: string;
  size: number;
  buffer: Buffer;
  path?: string;
  destination?: string;
  filename?: string;
}

export interface MultipartRequest extends Request {
  files?: MulterFile[] | Record<string, MulterFile[]>;
  file?: MulterFile;
}

export interface MultipartPacket {
  id: string;
  buffer: Buffer;
  mediaType: string;
  metadata: Record<string, unknown>;
}

export interface MultipartResponseOptions {
  boundary?: string;
}
```

## Migration Patterns

### Converting JSDoc to TypeScript

**Before (JavaScript with JSDoc):**

```javascript
/**
 * Process a pipeline stage
 * @param {string} stageId - The stage identifier
 * @param {Object} context - The invocation context
 * @returns {Promise<void>}
 */
async function processStage(stageId, context) {
  // implementation
}
```

**After (TypeScript):**

```typescript
import type { InvocationContext } from '../types/pipeline.js';

async function processStage(
  stageId: string,
  context: InvocationContext
): Promise<void> {
  // implementation
}
```

### Converting Singleton Services

**Before (JavaScript):**

```javascript
let instance = null;

class MongoDBService {
  static getInstance() {
    if (!instance) {
      instance = new MongoDBService();
    }
    return instance;
  }
}

export default MongoDBService.getInstance();
```

**After (TypeScript):**

```typescript
let instance: MongoDBService | null = null;

class MongoDBService {
  private constructor() {}

  static getInstance(): MongoDBService {
    if (!instance) {
      instance = new MongoDBService();
    }
    return instance;
  }
}

export default MongoDBService.getInstance();
```

### Converting Express Middleware

**Before (JavaScript):**

```javascript
export function contextMiddleware(req, res, next) {
  req.context = {
    requestId: generateId(),
    logger: createLogger(),
  };
  next();
}
```

**After (TypeScript):**

```typescript
import type { Request, Response, NextFunction } from 'express';
import type { RequestContext } from '../types/express.js';

export function contextMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  req.context = {
    requestId: generateId(),
    logger: createLogger(),
  } as RequestContext;
  next();
}
```

### Converting Async Route Handlers

**Before (JavaScript):**

```javascript
export const getHealth = async (req, res) => {
  const health = await checkHealth();
  req.context.success(health);
};
```

**After (TypeScript):**

```typescript
import type { Request, Response } from 'express';

export const getHealth = async (
  req: Request,
  res: Response
): Promise<void> => {
  const health = await checkHealth();
  req.context.success(health);
};
```

### Converting Pipeline Definitions

**Before (JavaScript):**

```javascript
import { Pipeline } from '../../pipeline.js';

const pipeline = new Pipeline({
  name: 'My Pipeline',
  description: 'Description',
});

pipeline.definePacket('input', {
  'application/json': {
    parser: async (buffer) => JSON.parse(buffer.toString()),
    serializer: async (data) => Buffer.from(JSON.stringify(data)),
  },
});

export default pipeline;
```

**After (TypeScript):**

```typescript
import { Pipeline } from '../../pipeline.js';
import type { InvocationContext, MediaTypeHandler } from '../../../types/pipeline.js';

interface InputData {
  field1: string;
  field2: number;
}

const jsonHandler: MediaTypeHandler = {
  parser: async (buffer: Buffer): Promise<InputData> =>
    JSON.parse(buffer.toString()) as InputData,
  serializer: async (data: unknown): Promise<Buffer> =>
    Buffer.from(JSON.stringify(data)),
};

const pipeline = new Pipeline({
  name: 'My Pipeline',
  description: 'Description',
});

pipeline.definePacket('input', {
  'application/json': jsonHandler,
});

export default pipeline;
```

## Best Practices

### 1. Avoid `any`

```typescript
// Bad - Loses type safety
function process(data: any) {}

// Good - Use unknown for truly unknown types
function process(data: unknown) {
  if (typeof data === 'object' && data !== null) {
    // Now TypeScript knows data is an object
  }
}

// Better - Use generics for flexibility
function process<T>(data: T): T {}

// Best - Use specific interfaces
function process(data: ProcessableData): ProcessedResult {}
```

### 2. Unused Parameters

Prefix intentionally unused parameters with `_`:

```typescript
// Express error handler requires 4 params
export function errorHandler(
  err: AppError,
  _req: Request,
  res: Response,
  _next: NextFunction
): void {
  res.status(err.statusCode).json({ error: err.message });
}
```

### 3. Explicit Return Types for Public APIs

```typescript
// Internal function - inference is fine
function add(a: number, b: number) {
  return a + b;
}

// Exported function - explicit return type
export function calculateTotal(items: Item[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// Async functions - explicit Promise type
export async function fetchUser(id: string): Promise<User | null> {
  return await db.users.findOne({ id });
}
```

### 4. Type-Only Imports

Use `import type` for types to avoid runtime overhead:

```typescript
// Mixed import
import { Pipeline, type PipelineOptions } from './pipeline.js';

// Type-only import (preferred when only importing types)
import type { InvocationContext, Packet } from '../types/pipeline.js';
import { Pipeline } from './pipeline.js';
```

### 5. Const Assertions for Literal Types

```typescript
// Without const assertion - string[]
const stages = ['validate', 'transform', 'output'];

// With const assertion - readonly ['validate', 'transform', 'output']
const stages = ['validate', 'transform', 'output'] as const;

// Useful for configuration objects
const config = {
  timeout: 5000,
  maxRetries: 3,
} as const;
```

### 6. Discriminated Unions for State Management

```typescript
type PipelineState =
  | { status: 'idle' }
  | { status: 'running'; startTime: number }
  | { status: 'completed'; result: unknown; duration: number }
  | { status: 'failed'; error: Error };

function handleState(state: PipelineState) {
  switch (state.status) {
    case 'idle':
      // TypeScript knows no other properties
      break;
    case 'running':
      // TypeScript knows startTime exists
      console.log(state.startTime);
      break;
    case 'completed':
      // TypeScript knows result and duration exist
      console.log(state.result, state.duration);
      break;
    case 'failed':
      // TypeScript knows error exists
      console.error(state.error);
      break;
  }
}
```

## Common Issues & Solutions

### Issue: Module not found with `.js` extension

When using `NodeNext` module resolution, imports must use `.js` extensions:

```typescript
// Wrong - Will fail at runtime
import { foo } from './module';
import { bar } from './utils/helper';

// Correct - Use .js even for .ts files
import { foo } from './module.js';
import { bar } from './utils/helper.js';
```

### Issue: Express v5 async handler typing

Express v5 handles async errors automatically, but TypeScript needs proper typing:

```typescript
import type { Request, Response, NextFunction } from 'express';

// Define handler type that can be async
type AsyncHandler = (
  req: Request,
  res: Response,
  next: NextFunction
) => Promise<void> | void;

// Use in routes
const handler: AsyncHandler = async (req, res) => {
  const data = await fetchData();
  req.context.success(data);
};
```

### Issue: Multer file typing

```typescript
import type { Request } from 'express';
import type { MulterFile } from '../types/multipart.js';

interface FileRequest extends Request {
  file?: MulterFile;
  files?: MulterFile[] | Record<string, MulterFile[]>;
}

export function handleUpload(req: FileRequest, res: Response): void {
  if (req.file) {
    // Single file upload
    console.log(req.file.originalname);
  }
}
```

### Issue: Circular dependencies in type definitions

Use `import type` to break circular dependencies:

```typescript
// types/pipeline.d.ts
import type { InvocationContext } from './context.js';

// types/context.d.ts
import type { Pipeline } from './pipeline.js'; // Would cause circular

// Solution: Use type-only import
import type { PipelineMetadata } from './pipeline.js';
```

### Issue: JSON module imports

```typescript
// Enable in tsconfig.json: "resolveJsonModule": true

// Import JSON files
import config from './config.json' assert { type: 'json' };

// Or use dynamic import for conditional loading
const manifest = await import('./manifest.json', { assert: { type: 'json' } });
```

## Editor Configuration

### VS Code Settings

Add to `.vscode/settings.json`:

```json
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit",
    "source.organizeImports": "explicit"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### Recommended VS Code Extensions

- **ESLint** - Linting integration
- **Prettier** - Code formatting
- **TypeScript Importer** - Auto-import suggestions
- **Error Lens** - Inline error display
- **Pretty TypeScript Errors** - Readable error messages

## Testing with TypeScript

### Default (Phase 1) - Keep tests in JavaScript

- Tests stay in JavaScript while source migrates; commands already include `**/*.{js,ts}` globs.
- Run unit tests: `npm test` (or `npm run test:unit`)
- Run integration tests: `npm run test:integration`
- TypeScript test files should be introduced only after the loader/tooling is updated (see below).

### TypeScript tests (later phases)

When you start writing `.test.ts` files, run them with a TS-aware loader (e.g., `tsx`) or against compiled output:

```typescript
// tests/unit/utils/errors.test.ts
import { describe, it, before, after, mock } from 'node:test';
import assert from 'node:assert';
import { AppError, ValidationError } from '../../../src/utils/errors.js';

describe('AppError', () => {
  it('should create error with correct properties', () => {
    const error = new AppError({
      message: 'Test error',
      statusCode: 400,
    });

    assert.strictEqual(error.message, 'Test error');
    assert.strictEqual(error.statusCode, 400);
    assert.strictEqual(error.isOperational, true);
  });
});
```

```bash
# Type-check without emitting
npm run type-check

# Run TS tests with tsx loader
npx tsx --test tests/unit/**/*.test.ts

# Run with coverage
npx c8 tsx --test tests/unit/**/*.test.ts
```

## Migration Order

Recommended order for converting files:

1. **Foundation** (no dependencies)
   - `src/utils/errors.ts`
   - `src/utils/helpers.ts`
   - `src/utils/constants.ts`
   - `src/config/index.ts`

2. **Utilities** (depend on foundation)
   - `src/utils/response.handler.ts`
   - `src/utils/logger.ts`
   - `src/utils/media-type.helper.ts`
   - `src/utils/multipart.response.ts`
   - `src/utils/sse.response.ts`

3. **Services** (depend on utilities)
   - `src/api/v1.0/services/mongodb.service.ts`
   - `src/api/v1.0/services/redis.service.ts`
   - `src/api/v1.0/services/litellm.service.ts`
   - Other service files

4. **Middleware** (depend on services)
   - Core middleware
   - Security middleware
   - Multipart middleware

5. **Controllers & Routes** (depend on middleware)
   - Controller files
   - Route definition files

6. **Pipeline System** (most complex)
   - `src/api/v1.0/pipelines/pipeline.ts`
   - `src/api/v1.0/pipelines/invocation-context.ts`
   - `src/api/v1.0/pipelines/registry.ts`
   - Pipeline implementations (excluding autocoder)

7. **Entry Points**
   - `src/app.ts`
   - `src/index.ts`

8. **Tests** (optional, can remain JavaScript)
   - Unit tests
   - Integration tests

## Performance Tips

1. **Enable `skipLibCheck`** - Skip type checking of `.d.ts` files for faster builds
2. **Use incremental compilation** - Add `"incremental": true` to tsconfig
3. **Exclude unnecessary directories** - Don't type-check `node_modules`, `dist`, `coverage`
4. **Use `tsx` for development** - Faster than `ts-node` with native ESM support
5. **Run type-check separately** - Use `tsc --noEmit` in CI, don't block dev server

## Related Documentation

- [Code Standards](./STANDARDS.md) - Coding conventions and style guide
- [API Architecture](../architecture/README.md) - System architecture overview
- [Pipeline System](../../src/api/v1.0/pipelines/README.md) - Pipeline documentation
- [Migration Plan](../build/typescript-migration-plan.md) - Detailed migration checklist
