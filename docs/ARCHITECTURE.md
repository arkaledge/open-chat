# OpenChat System Architecture

## Overview

OpenChat is a comprehensive Enterprise AI Assistant Platform built with a modern microservices architecture, supporting multiple LLM providers, RAG (Retrieval-Augmented Generation), web search, and conversation branching/threading.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Web App    │  │  Mobile App  │  │   API SDK    │             │
│  │  (Next.js)   │  │   (Future)   │  │   (Future)   │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                  │                      │
│         └─────────────────┴──────────────────┘                      │
│                           │                                         │
└───────────────────────────┼─────────────────────────────────────────┘
                            │ HTTPS/WSS
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              NGINX Ingress / Kong Gateway                   │   │
│  │  - TLS Termination        - Load Balancing                 │   │
│  │  - Rate Limiting          - Request Routing                │   │
│  │  - Authentication         - API Versioning                 │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│                │  │                │  │                │
│   FRONTEND     │  │   BACKEND      │  │   WEBSOCKET    │
│   SERVICE      │  │   API          │  │   SERVICE      │
│   (Next.js)    │  │   (FastAPI)    │  │   (Future)     │
│                │  │                │  │                │
└────────────────┘  └───────┬────────┘  └────────────────┘
                            │
        ┌───────────────────┼───────────────────────────────┐
        │                   │                               │
        ▼                   ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                               │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │    Auth      │  │    Chat      │  │   Branch     │             │
│  │   Service    │  │  Service     │  │  Service     │             │
│  │              │  │              │  │              │             │
│  │ - JWT Auth   │  │ - Streaming  │  │ - Threading  │             │
│  │ - RBAC       │  │ - Models     │  │ - Regenerate │             │
│  │ - Sessions   │  │ - Context    │  │ - Edit       │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │    RAG       │  │   Search     │  │    Cache     │             │
│  │   Service    │  │  Service     │  │   Service    │             │
│  │              │  │              │  │              │             │
│  │ - Documents  │  │ - Web Search │  │ - Semantic   │             │
│  │ - Embedding  │  │ - Tavily     │  │ - Redis      │             │
│  │ - Retrieval  │  │ - Brave      │  │ - TTL        │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────────────────┐
        │                   │                               │
        ▼                   ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              LLM Orchestration Service                      │   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │   LiteLLM    │  │  LangChain   │  │  LlamaIndex  │    │   │
│  │  │              │  │              │  │              │    │   │
│  │  │ - Routing    │  │ - Chains     │  │ - RAG        │    │   │
│  │  │ - Failover   │  │ - Memory     │  │ - Agents     │    │   │
│  │  │ - Cost Track │  │ - Tools      │  │ - Indices    │    │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
└───────────────────────────┼─────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────────────────┐
        │                   │                               │
        ▼                   ▼                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MODEL SERVING LAYER                             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   OpenAI     │  │  Anthropic   │  │    Azure     │             │
│  │     API      │  │     API      │  │   OpenAI     │             │
│  │              │  │              │  │              │             │
│  │ - GPT-4o     │  │ - Claude 3.5 │  │ - GPT-4      │             │
│  │ - GPT-4      │  │ - Claude 3   │  │ - Custom     │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Ollama     │  │     vLLM     │  │   AWS        │             │
│  │  (Local LLM) │  │  (Production)│  │   Bedrock    │             │
│  │              │  │              │  │              │             │
│  │ - Llama 3.1  │  │ - PagedAttn  │  │ - Claude     │             │
│  │ - Mistral    │  │ - Batching   │  │ - Titan      │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  PostgreSQL  │  │    Redis     │  │    Qdrant    │             │
│  │              │  │              │  │              │             │
│  │ - Users      │  │ - Cache      │  │ - Vectors    │             │
│  │ - Convos     │  │ - Sessions   │  │ - Embeddings │             │
│  │ - Messages   │  │ - Rate Limit │  │ - Search     │             │
│  │ - Branches   │  │ - Queue      │  │ - Metadata   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │    MinIO     │  │  TimescaleDB │                                │
│  │  (S3-compat) │  │  (Metrics)   │                                │
│  │              │  │              │                                │
│  │ - Documents  │  │ - Analytics  │                                │
│  │ - Models     │  │ - Audit Logs │                                │
│  └──────────────┘  └──────────────┘                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                               │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Prometheus  │  │   Grafana    │  │     Loki     │             │
│  │  (Metrics)   │  │ (Dashboards) │  │    (Logs)    │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐                                │
│  │    Jaeger    │  │  LangSmith   │                                │
│  │   (Traces)   │  │(LLM Observ.) │                                │
│  └──────────────┘  └──────────────┘                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Conversation Branching Architecture

### Branch Data Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Conversation Tree                         │
│                                                              │
│          ┌──────────────────┐                               │
│          │   Root Conv #1   │                               │
│          │  "How to code?"  │                               │
│          └────────┬─────────┘                               │
│                   │                                          │
│         ┌─────────┴─────────┬──────────────┐               │
│         │                   │              │               │
│         ▼                   ▼              ▼               │
│  ┌────────────┐      ┌────────────┐ ┌────────────┐        │
│  │ Branch #2  │      │ Branch #3  │ │ Branch #4  │        │
│  │ "Python"   │      │ "JS"       │ │ "Edit: Go" │        │
│  └─────┬──────┘      └────────────┘ └────────────┘        │
│        │                                                    │
│    ┌───┴───┐                                               │
│    │       │                                               │
│    ▼       ▼                                               │
│ ┌──────┐ ┌──────┐                                         │
│ │Branch│ │Branch│                                         │
│ │  #5  │ │  #6  │                                         │
│ └──────┘ └──────┘                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema for Branching

```sql
-- Conversations Table (Updated)
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    workspace_id UUID REFERENCES workspaces(id),
    title TEXT,
    model TEXT,
    metadata JSONB,

    -- Branching Fields
    parent_conversation_id UUID REFERENCES conversations(id),
    branched_at_message_id UUID REFERENCES messages(id),
    branch_count INTEGER DEFAULT 0,

    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    archived TIMESTAMP
);

-- Messages Table (Updated)
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role TEXT,
    content TEXT,
    model TEXT,

    -- Threading Fields
    parent_message_id UUID REFERENCES messages(id),
    thread_id UUID,
    is_thread_root BOOLEAN DEFAULT FALSE,
    branch_depth INTEGER DEFAULT 0,

    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    estimated_cost FLOAT,
    metadata JSONB,
    feedback_score INTEGER,

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_conv_parent ON conversations(parent_conversation_id);
CREATE INDEX idx_msg_thread ON messages(thread_id);
CREATE INDEX idx_msg_parent ON messages(parent_message_id);
```

## Request Flow with Branching

### 1. Normal Chat Request
```
User → Frontend → API Gateway → Backend
                                   ├─→ LLM Service → OpenAI/Anthropic
                                   ├─→ Cache Service → Redis (check)
                                   ├─→ RAG Service → Qdrant (if enabled)
                                   └─→ Search Service → Tavily (if enabled)

Backend → Save to PostgreSQL → Return Response → Stream to Frontend
```

### 2. Branch Creation Request
```
User clicks "Branch" on Message #5

Frontend → API /branches/conversations/{id}/messages/{msg_id}/branch

Backend:
  1. Fetch original conversation
  2. Fetch all messages up to branch point
  3. Create new conversation record
     - parent_conversation_id = original_id
     - branched_at_message_id = msg_id
  4. Copy messages to new conversation
  5. Update parent branch_count++
  6. Return new conversation

Frontend → Navigate to new conversation
```

### 3. Message Regeneration Request
```
User clicks "Regenerate" on Assistant Message

Frontend → API /branches/messages/{msg_id}/regenerate

Backend:
  1. Get message and conversation context
  2. Build context (all messages before this one)
  3. Call LLM with same prompt, different params
  4. If keep_original=true:
     - Create branch conversation
     - Copy history + add new response
  5. If keep_original=false:
     - Replace message content
  6. Return result

Frontend → Update UI or navigate to branch
```

### 4. Branch Tree Navigation
```
User opens "Branch Tree" view

Frontend → API /branches/conversations/{id}/tree

Backend:
  1. Start from conversation
  2. Find root (traverse parent_conversation_id)
  3. Recursively build tree:
     - Get conversation
     - Get message count
     - Get all children (where parent_id = current)
     - Repeat for each child
  4. Return nested tree structure

Frontend → Render interactive tree
           - Current conversation highlighted
           - Click to navigate
```

## Data Flow Diagram

```
┌──────────┐
│   User   │
└────┬─────┘
     │ 1. Send Message
     ▼
┌─────────────┐
│  Frontend   │
│  Store      │
└──────┬──────┘
       │ 2. API Call
       ▼
┌─────────────┐
│  Backend    │
│  API        │──────┐
└──────┬──────┘      │ 3. Check Cache
       │             ▼
       │        ┌─────────┐
       │        │  Redis  │
       │        └─────────┘
       │             │
       │ 4. If Cache Miss
       ▼             │
┌─────────────┐      │
│ LLM Service │◄─────┘
└──────┬──────┘
       │
       ├─────► 5a. RAG Enabled?
       │            │
       │            ▼
       │       ┌─────────┐
       │       │ Qdrant  │ (Vector Search)
       │       └─────────┘
       │
       ├─────► 5b. Web Search Enabled?
       │            │
       │            ▼
       │       ┌─────────┐
       │       │ Tavily  │ (Web Search)
       │       └─────────┘
       │
       └─────► 6. Build Context & Call LLM
                    │
                    ▼
               ┌──────────┐
               │ OpenAI/  │
               │Anthropic │
               └────┬─────┘
                    │ 7. Stream Response
                    ▼
               ┌──────────┐
               │ Backend  │
               └────┬─────┘
                    │ 8. Save to DB
                    ▼
               ┌──────────┐
               │PostgreSQL│
               └────┬─────┘
                    │ 9. Cache Response
                    ▼
               ┌──────────┐
               │  Redis   │
               └────┬─────┘
                    │ 10. Return to Frontend
                    ▼
               ┌──────────┐
               │ Frontend │
               │  Update  │
               └──────────┘
```

## Scalability Architecture

```
┌────────────────── Load Balancer ──────────────────┐
│                                                    │
├─► Backend Pod 1 ──┐                               │
├─► Backend Pod 2 ──┼──► Shared State ──────────────┤
├─► Backend Pod 3 ──┘                               │
│                                                    │
└────────────────────────────────────────────────────┘
                     │
     ┌───────────────┼────────────────┐
     │               │                │
     ▼               ▼                ▼
┌──────────┐   ┌──────────┐    ┌──────────┐
│PostgreSQL│   │  Redis   │    │  Qdrant  │
│ Cluster  │   │ Sentinel │    │ Cluster  │
│          │   │          │    │          │
│ Primary  │   │ Master   │    │  Nodes   │
│ Replicas │   │ Replicas │    │  1,2,3   │
└──────────┘   └──────────┘    └──────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────┐
│            Security Layers                   │
│                                             │
│  1. Network Level                           │
│     - TLS 1.3                               │
│     - WAF Rules                             │
│     - Rate Limiting                         │
│                                             │
│  2. Authentication                          │
│     - JWT Tokens                            │
│     - OAuth 2.0 / SAML                      │
│     - MFA                                   │
│                                             │
│  3. Authorization                           │
│     - RBAC (Roles)                          │
│     - Row-Level Security                    │
│     - API Key Management                    │
│                                             │
│  4. Data Protection                         │
│     - Encryption at Rest (AES-256)          │
│     - Encryption in Transit (TLS)           │
│     - PII Detection & Redaction             │
│     - Prompt Injection Detection            │
│                                             │
│  5. Audit & Compliance                      │
│     - Activity Logging                      │
│     - Audit Trails                          │
│     - Compliance Reports                    │
│                                             │
└─────────────────────────────────────────────┘
```

## Performance Optimization

### Caching Strategy
```
Request → Check L1 (Redis Semantic Cache)
          │
          ├─ Hit → Return Cached Response (15x faster)
          │
          └─ Miss → Check L2 (Model Provider Cache)
                    │
                    ├─ Hit → Return Response
                    │
                    └─ Miss → Generate Response
                              │
                              └─→ Cache in L1 & L2
```

### Cost Optimization
```
Query Classification
│
├─ Simple → Small Model (7B params, INT4)
│           Cost: $0.01/1K tokens
│
├─ Medium → Medium Model (13B params, FP8)
│           Cost: $0.05/1K tokens
│
├─ Complex → Large Model (70B params)
│            Cost: $0.20/1K tokens
│
└─ Expert → Frontier Model (GPT-4o, Claude)
            Cost: $1.00/1K tokens
```

## Monitoring & Observability

```
┌─────────────── Metrics Collection ───────────────┐
│                                                   │
│  Application Metrics                             │
│  ├─ Request Rate                                 │
│  ├─ Response Time (P50, P95, P99)                │
│  ├─ Error Rate                                   │
│  └─ Active Users                                 │
│                                                   │
│  LLM Metrics                                     │
│  ├─ Token Usage (Input/Output)                   │
│  ├─ Cost per Request                             │
│  ├─ Model Performance                            │
│  └─ Cache Hit Rate                               │
│                                                   │
│  Infrastructure Metrics                          │
│  ├─ CPU/Memory Usage                             │
│  ├─ GPU Utilization                              │
│  ├─ Database Connections                         │
│  └─ Queue Depth                                  │
│                                                   │
└───────────────────────────────────────────────────┘
         │
         ▼
    ┌──────────┐
    │Prometheus│
    └────┬─────┘
         │
         ▼
    ┌──────────┐
    │ Grafana  │──► Alerts ──► PagerDuty
    └──────────┘
```

## Deployment Architecture (Kubernetes)

```
┌──────────────────────────────────────────────────┐
│              Kubernetes Cluster                   │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │         openchat Namespace              │    │
│  │                                         │    │
│  │  ┌────────────┐   ┌────────────┐      │    │
│  │  │  Backend   │   │  Frontend  │      │    │
│  │  │Deployment  │   │ Deployment │      │    │
│  │  │  (3 pods)  │   │  (2 pods)  │      │    │
│  │  └────────────┘   └────────────┘      │    │
│  │                                         │    │
│  │  ┌────────────┐   ┌────────────┐      │    │
│  │  │PostgreSQL  │   │   Redis    │      │    │
│  │  │StatefulSet │   │ Deployment │      │    │
│  │  └────────────┘   └────────────┘      │    │
│  │                                         │    │
│  │  ┌────────────┐   ┌────────────┐      │    │
│  │  │   Qdrant   │   │   MinIO    │      │    │
│  │  │ StatefulSet│   │ Deployment │      │    │
│  │  └────────────┘   └────────────┘      │    │
│  │                                         │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │      monitoring Namespace               │    │
│  │                                         │    │
│  │  Prometheus, Grafana, Loki, Jaeger     │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
└──────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. **Multi-Model Provider Strategy**
- **Why**: Avoid vendor lock-in, optimize costs, enable comparison
- **How**: Abstraction layer (LiteLLM) + provider-specific adapters
- **Trade-offs**: Added complexity vs. flexibility

### 2. **Conversation Branching**
- **Why**: Explore alternatives, compare responses, team collaboration
- **How**: Parent-child relationships in database, recursive tree traversal
- **Trade-offs**: Storage overhead vs. UX improvement

### 3. **Semantic Caching**
- **Why**: Reduce costs (70-90%), improve latency (15x faster)
- **How**: Embedding-based similarity matching in Redis
- **Trade-offs**: Cache storage vs. API costs

### 4. **Microservices Architecture**
- **Why**: Independent scaling, technology flexibility, team autonomy
- **How**: Service-per-domain pattern, API gateway
- **Trade-offs**: Operational complexity vs. scalability

### 5. **Event Streaming (SSE) for Chat**
- **Why**: Real-time UX, lower perceived latency
- **How**: Server-Sent Events with chunked responses
- **Trade-offs**: Connection management vs. user experience

## Future Architecture Enhancements

1. **WebSocket Support** for real-time collaboration
2. **Message Queue** (RabbitMQ/Kafka) for async processing
3. **CDN Integration** for global content delivery
4. **Multi-Region Deployment** for high availability
5. **GraphQL API** for flexible data fetching
6. **gRPC** for inter-service communication
7. **Service Mesh** (Istio) for advanced networking
8. **Function-as-a-Service** for plugin execution

---

**Document Version**: 2.0
**Last Updated**: 2024-01-15
**Authors**: OpenChat Engineering Team
