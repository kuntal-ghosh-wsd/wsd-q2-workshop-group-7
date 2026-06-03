# WAIF Framework - Manual Testing Guide

A comprehensive guide for manually testing the WAIF (WSD AI Inference Facade) application.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Step 1: Verify Server Status](#step-1-verify-server-status)
- [Step 2: Access the Test Harness UI](#step-2-access-the-test-harness-ui)
- [Step 3: Explore Available Pipelines](#step-3-explore-available-pipelines)
- [Step 4: Test Echo Pipeline (No LLM Required)](#step-4-test-echo-pipeline-no-llm-required)
- [Step 5: Test Pipeline API Endpoints](#step-5-test-pipeline-api-endpoints)
- [Step 6: Test with JSON Input](#step-6-test-with-json-input)
- [Step 7: Test SSE Streaming](#step-7-test-sse-streaming)
- [Step 8: Test Error Handling](#step-8-test-error-handling)
- [Step 9: Test Main Graph (Requires LLM)](#step-9-test-main-graph-requires-llm)
- [Step 10: Test cURL Generator](#step-10-test-curl-generator)
- [Quick Test Checklist](#quick-test-checklist)
- [Troubleshooting](#troubleshooting)

---

## Overview

**WAIF** (WSD AI Inference Facade) is a REST API framework for building and executing **pipelines** - workflows that process data through stages, often with LLM (AI) integration. The Test Harness is a web UI for testing these pipelines.

### Key Concepts

- **Pipeline**: A workflow definition containing packets, stages, and graphs
- **Packet**: A named data container with media type support (input/output)
- **Stage**: A discrete processing unit within a pipeline
- **Graph**: An execution flow that connects stages with conditional branching
- **Test Harness**: Web-based UI for interactive pipeline testing

---

## Prerequisites

Before testing, ensure:

1. **Server is running**: `npm run dev` or `npm start`
2. **Default port**: Application runs on `http://localhost:4444`
3. **Environment**: Development mode (test harness is disabled in production)

Optional services:
- **MongoDB**: Required for database operations (some pipelines)
- **Redis**: Required for caching and rate limiting
- **LiteLLM**: Required for AI/LLM-powered pipelines

---

## Step 1: Verify Server Status

### Basic Ping Test

**Browser or curl:**
```bash
curl http://localhost:4444/api/test/ping
```

**Expected response:**
```json
{
  "status": "success",
  "message": "Pong! API is running",
  "data": {
    "timestamp": "2024-01-15T10:30:00.000Z",
    "version": "1.0.0",
    "environment": "development"
  }
}
```

### Full Health Check

Includes MongoDB and Redis connectivity status:

```bash
curl http://localhost:4444/api/test/health
```

**Expected response (healthy):**
```json
{
  "status": "success",
  "message": "System health check passed",
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "services": {
      "mongodb": { "status": "connected", "responseTime": 15 },
      "redis": { "status": "connected", "responseTime": 8 }
    },
    "system": {
      "uptime": 3600,
      "memory": { "used": 157286400, "total": 8589934592 }
    }
  }
}
```

### MongoDB Diagnostics

For detailed MongoDB connection info:

```bash
curl http://localhost:4444/api/test/mongo
```

---

## Step 2: Access the Test Harness UI

Open in your browser:
```
http://localhost:4444/test-harness/index.html
```

### UI Components

| Component | Description |
|-----------|-------------|
| **Header** | "WAIF Test Harness" with connection status indicator |
| **Left Panel** | List of available pipelines with versions |
| **Right Panel** | Pipeline details or graph execution view |
| **Auth Button** | Configure bearer token for authenticated requests |

### Initial State

- Connection status should show "Connected" (green)
- Pipeline list should load automatically
- Welcome message displayed in main panel

---

## Step 3: Explore Available Pipelines

### Available Pipelines

| Pipeline | Default Version | Description | Requires LLM? |
|----------|-----------------|-------------|---------------|
| `test-pipeline` | 1.0.0 | Simple test with echo mode | Echo: No, Main: Yes |
| `doc-2-ibt` | 1.4.0 | Document to IBT conversion | Yes |
| `translation` | Latest | Translation pipeline | Yes |
| `autocoder` | 1.0.0 | Code generation sandbox | Yes |

### Pipeline Information

Click on any pipeline to view:
- **Metadata**: Name, description, version info
- **Packets**: Input/output data containers with supported media types
- **Stages**: Processing steps available
- **Graphs**: Execution workflows

---

## Step 4: Test Echo Pipeline (No LLM Required)

The echo pipeline is ideal for testing without LLM dependencies.

### Using the Test Harness UI

1. **Select Pipeline**
   - Click **"test-pipeline"** in the left panel
   - Review pipeline details

2. **Select Graph**
   - Click on the **"echo"** graph
   - This opens the graph execution view

3. **Provide Input**
   - In "Input Packets" section, enter text:
     ```
     Hello, this is a test!
     ```
   - Ensure content type is `text/plain`

4. **Execute**
   - Click **"🚀 Execute Graph"**
   - Watch the graph visualization (nodes turn green)
   - Monitor the Event Log for execution events

5. **Check Output**
   - Output packet should show: `Echo: Hello, this is a test!`
   - Download button available for output

### Using curl

```bash
curl -X POST "http://localhost:4444/api/pipelines/test-pipeline/default/graphs/echo/actions/execute" \
  -H "Content-Type: multipart/form-data" \
  -F "input=Hello World;type=text/plain"
```

**Expected response (multipart):**
The response contains the output packet with:
- Content-Disposition header with packet ID
- Content-Type: text/plain
- Body: `Echo: Hello World`

---

## Step 5: Test Pipeline API Endpoints

### List All Pipelines

```bash
curl http://localhost:4444/api/pipelines
```

**Response structure:**
```json
{
  "status": "success",
  "message": "Available pipelines",
  "data": [
    {
      "pipelineId": "test-pipeline",
      "manifest": { "defaultVersion": "1.0.0" },
      "versions": [
        {
          "pipelineId": "test-pipeline",
          "name": "Test Pipeline",
          "version": "1.0.0",
          "packets": ["input", "output", "prompt"],
          "stages": ["validateInput", "buildPrompt", "callLLM", "processOutput", "echo"],
          "graphs": ["main", "echo"]
        }
      ]
    }
  ]
}
```

### Get Specific Pipeline Info

```bash
curl http://localhost:4444/api/pipelines/test-pipeline
```

### Get Pipeline Version Details

```bash
# Default version
curl http://localhost:4444/api/pipelines/test-pipeline/default

# Specific version
curl http://localhost:4444/api/pipelines/test-pipeline/versions/1.0.0
```

### Get Usage Statistics

```bash
curl http://localhost:4444/api/pipelines/usage
```

**Response:**
```json
{
  "status": "success",
  "message": "Usage statistics",
  "data": {
    "totalTokens": 50000,
    "promptTokens": 20000,
    "completionTokens": 30000,
    "totalCalls": 100,
    "toolCalls": 25,
    "averageTokensPerCall": 500
  }
}
```

---

## Step 6: Test with JSON Input

The test-pipeline accepts both `text/plain` and `application/json` input.

### JSON Input Format

```json
{
  "content": "Your message here",
  "maxLength": 100,
  "style": "casual"
}
```

**Style options:** `casual`, `formal`, `technical`

### Using Test Harness

1. Select `test-pipeline` → `echo` graph
2. Change content type dropdown to `application/json`
3. Enter JSON:
   ```json
   {"content": "Test message", "maxLength": 100, "style": "casual"}
   ```
4. Click Execute

### Using curl

```bash
curl -X POST "http://localhost:4444/api/pipelines/test-pipeline/default/graphs/echo/actions/execute" \
  -F 'input={"content":"Hello JSON","maxLength":100,"style":"casual"};type=application/json'
```

---

## Step 7: Test SSE Streaming

Server-Sent Events provide real-time execution monitoring.

### Using Test Harness

The UI automatically uses SSE streaming:
- Execute any graph
- Watch the Event Log panel for live events
- Events are color-coded by type

### Using curl

```bash
curl -X POST "http://localhost:4444/api/pipelines/test-pipeline/default/graphs/echo/actions/execute/stream" \
  -H "Accept: text/event-stream" \
  -F "input=Test streaming;type=text/plain"
```

### Event Types

| Event | Description |
|-------|-------------|
| `connected` | SSE connection established |
| `graph:start` | Graph execution begins |
| `graph:end` | Graph execution completes |
| `graph:error` | Execution failure |
| `node:start` | Node execution begins |
| `node:end` | Node execution ends |
| `stage:start` | Stage execution begins |
| `stage:end` | Stage execution ends |
| `packet:added` | New packet created |
| `edge:decision` | Edge condition evaluated |

### Example SSE Output

```
event: connected
data: {"message":"SSE connection established"}

event: graph:start
data: {"graphId":"echo","timestamp":"2024-01-15T10:30:00.000Z"}

event: node:start
data: {"nodeId":"validate","timestamp":"..."}

event: stage:start
data: {"stageId":"validateInput","timestamp":"..."}

event: stage:end
data: {"stageId":"validateInput","duration":5,"timestamp":"..."}

event: node:end
data: {"nodeId":"validate","timestamp":"..."}

event: node:start
data: {"nodeId":"echoBack","timestamp":"..."}

event: packet:added
data: {"packetId":"output","timestamp":"..."}

event: node:end
data: {"nodeId":"echoBack","timestamp":"..."}

event: graph:end
data: {"graphId":"echo","duration":15,"timestamp":"..."}
```

---

## Step 8: Test Error Handling

### Validation Errors

**Empty input:**
```bash
curl -X POST "http://localhost:4444/api/pipelines/test-pipeline/default/graphs/echo/actions/execute" \
  -F "input=   ;type=text/plain"
```

**Expected:** 400 Bad Request with validation error message

### Not Found Errors

**Non-existent pipeline:**
```bash
curl http://localhost:4444/api/pipelines/non-existent
```

**Expected:** 404 Not Found

**Non-existent graph:**
```bash
curl -X POST "http://localhost:4444/api/pipelines/test-pipeline/default/graphs/invalid/actions/execute" \
  -F "input=test;type=text/plain"
```

**Expected:** 404 Not Found

### Missing Required Header

```bash
curl http://localhost:4444/api/pipelines
```

**Expected:** Response with default API version handling

---

## Step 9: Test Main Graph (Requires LLM)

The main graph demonstrates full LLM integration.

### Prerequisites

- LiteLLM service configured and running
- Valid API credentials in environment

### Execution Flow

1. **validateInput** - Validates input is non-empty string
2. **buildPrompt** - Creates LLM prompt with style instructions
3. **callLLM** - Sends request to LiteLLM
4. **processOutput** - Truncates and validates response

### Using Test Harness

1. Select `test-pipeline` → `main` graph
2. Enter a question: `What is the capital of France?`
3. Click Execute
4. Watch the graph progress through all stages
5. Output contains LLM response

### Using curl

```bash
curl -X POST "http://localhost:4444/api/pipelines/test-pipeline/default/graphs/main/actions/execute" \
  -F "input=What is the capital of France?;type=text/plain"
```

---

## Step 10: Test cURL Generator

The Test Harness includes a built-in cURL command generator.

### Steps

1. Select a pipeline and graph
2. Fill in input data
3. Click the **"cURL"** button (next to Execute)
4. Configure options:
   - **Platform**: Unix/macOS/Linux or Windows PowerShell
   - **Response Type**: SSE Streaming, Multipart, or Single Packet
5. Copy the generated command

### Response Type Options

| Type | Endpoint Suffix | Returns |
|------|-----------------|---------|
| SSE Streaming | `/stream` | Real-time events |
| Multipart | (none) | All output packets |
| Single Packet | `/packets/{id}` | Specific packet only |

---

## Quick Test Checklist

| # | Test | Endpoint/Action | Expected Result |
|---|------|-----------------|-----------------|
| 1 | Server ping | `GET /api/test/ping` | "Pong! API is running" |
| 2 | Health check | `GET /api/test/health` | Status: healthy/degraded |
| 3 | MongoDB diagnostics | `GET /api/test/mongo` | Connection details |
| 4 | List pipelines | `GET /api/pipelines` | Array of pipelines |
| 5 | Pipeline info | `GET /api/pipelines/test-pipeline` | Pipeline metadata |
| 6 | Usage stats | `GET /api/pipelines/usage` | Token/call statistics |
| 7 | Test Harness UI | Browser `/test-harness/` | UI loads correctly |
| 8 | Echo (text) | Execute echo graph | Returns "Echo: {input}" |
| 9 | Echo (JSON) | Execute with JSON | Processes JSON correctly |
| 10 | SSE streaming | Execute with /stream | Real-time events |
| 11 | Empty input | Send empty string | Validation error |
| 12 | Invalid pipeline | Request non-existent | 404 Not Found |

---

## Troubleshooting

### Common Issues

#### "Disconnected" in Test Harness Header

**Possible causes:**
- Server not running
- Wrong port
- Network issues

**Solutions:**
1. Check terminal for server errors
2. Verify `npm run dev` is running
3. Confirm port 4444 is accessible

#### Pipeline Not Loading

**Possible causes:**
- Import errors in pipeline code
- Missing dependencies

**Solutions:**
1. Check terminal for pipeline loading errors
2. Look for specific error messages
3. Verify all imports use correct syntax

#### MongoDB/Redis Errors in Health Check

**Note:** These services are optional for basic testing.

**For full functionality:**
1. Start MongoDB: `docker-compose up mongodb`
2. Start Redis: `docker-compose up redis`
3. Or use Docker Compose for all services

#### SSE Connection Fails

**Possible causes:**
- Proxy interference
- CORS configuration
- Browser limitations

**Solutions:**
1. Test directly without proxy
2. Check browser console for errors
3. Try a different browser

#### Graph Visualization Not Displaying

**Possible causes:**
- Cytoscape.js not loaded
- Container sizing issues

**Solutions:**
1. Check browser console for JavaScript errors
2. Ensure CDN resources are accessible
3. Try refreshing the page

### Debug Commands

**Check server logs:**
```bash
# If running with npm run dev, logs appear in terminal
# For structured logs, check stdout/stderr
```

**Test specific version:**
```bash
curl http://localhost:4444/api/pipelines/test-pipeline/versions/1.0.0
```

**Verbose curl output:**
```bash
curl -v http://localhost:4444/api/test/ping
```

---

## Additional Resources

- [Pipeline Test Harness README](../../src/api/v1.0/test-harness/README.md)
- [API Documentation](../api/README.md)
- [Architecture Overview](../architecture/README.md)
- [Code Standards](../patterns/STANDARDS.md)
