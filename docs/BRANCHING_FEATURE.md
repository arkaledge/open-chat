# Conversation Branching & Threading Feature

## Overview

The Conversation Branching feature allows users to create alternative conversation paths, explore "what if" scenarios, and compare different AI responses - similar to how Slack handles message threads, but applied to AI conversations.

## Key Features

### 1. **Conversation Branching**
Create a complete copy of a conversation to explore alternative paths without affecting the original.

**Use Cases:**
- Try different approaches to a problem
- Compare responses from different models
- Keep main conversation focused while exploring tangents
- Team collaboration on different aspects

**How to Use:**
1. Open any conversation
2. Click the "Branch" icon in the conversation menu
3. New conversation created with all history copied
4. Make changes without affecting original

### 2. **Message-Level Branching**
Branch from any specific message in a conversation.

**Use Cases:**
- Explore alternative responses from a specific point
- Compare "what if" scenarios
- A/B test different prompts
- Recover from conversation drift

**How to Use:**
1. Hover over any message
2. Click the three-dot menu (⋮)
3. Select "Branch from here"
4. New conversation starts from that message

### 3. **Message Regeneration**
Generate alternative responses for any assistant message.

**Use Cases:**
- Get multiple perspectives on same question
- Improve response quality
- Try different models on same prompt
- Compare response styles

**How to Use:**
1. Hover over assistant message
2. Click three-dot menu (⋮)
3. Select "Regenerate"
4. Choose to keep original or replace

### 4. **Message Editing**
Edit user messages and optionally regenerate the response.

**Use Cases:**
- Fix typos in prompts
- Refine questions for better answers
- Experiment with prompt variations
- Improve context

**How to Use:**
1. Hover over your message
2. Click three-dot menu (⋮)
3. Select "Edit message"
4. Modify content
5. Choose to create branch or edit in-place

### 5. **Branch Tree Visualization**
View and navigate the entire conversation tree.

**Use Cases:**
- Understand conversation evolution
- Find specific branches quickly
- Navigate complex conversation histories
- Track exploration paths

**How to Use:**
1. Click "Branch Tree" icon in header
2. See visual tree of all branches
3. Click any branch to navigate
4. Current conversation highlighted

## Technical Implementation

### Database Schema

```sql
-- Conversations with branching support
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    parent_conversation_id UUID REFERENCES conversations(id),
    branched_at_message_id UUID REFERENCES messages(id),
    branch_count INTEGER DEFAULT 0,
    ...
);

-- Messages with threading support
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    parent_message_id UUID REFERENCES messages(id),
    thread_id UUID,
    is_thread_root BOOLEAN DEFAULT FALSE,
    branch_depth INTEGER DEFAULT 0,
    ...
);
```

### API Endpoints

#### Create Conversation Branch
```http
POST /api/v1/branches/conversations/{conversation_id}/branch
Content-Type: application/json

{
  "title": "Alternative approach",
  "include_future_messages": false
}

Response: 201 Created
{
  "id": "...",
  "parent_conversation_id": "...",
  "title": "Alternative approach",
  ...
}
```

#### Branch from Message
```http
POST /api/v1/branches/conversations/{conversation_id}/messages/{message_id}/branch
Content-Type: application/json

{
  "new_content": "Optional replacement content",
  "model": "gpt-4o",
  "temperature": 0.7
}

Response: 201 Created
{
  "id": "...",
  "branched_at_message_id": "...",
  ...
}
```

#### Regenerate Message
```http
POST /api/v1/branches/messages/{message_id}/regenerate
Content-Type: application/json

{
  "model": "claude-3-5-sonnet-20241022",
  "temperature": 0.9,
  "keep_original": true
}

Response: 200 OK
{
  "conversation_id": "...",
  "message": {...}
}
```

#### Edit Message
```http
POST /api/v1/branches/messages/{message_id}/edit
Content-Type: application/json

{
  "content": "Updated message content",
  "regenerate_response": true,
  "create_branch": true
}

Response: 200 OK
{
  "conversation_id": "...",
  ...
}
```

#### Get Branch Tree
```http
GET /api/v1/branches/conversations/{conversation_id}/tree

Response: 200 OK
{
  "conversation_id": "...",
  "title": "Root conversation",
  "message_count": 15,
  "branches": [
    {
      "conversation_id": "...",
      "title": "Branch 1",
      "message_count": 12,
      "branches": [...]
    }
  ]
}
```

#### List Branches
```http
GET /api/v1/branches/conversations/{conversation_id}/branches

Response: 200 OK
[
  {
    "conversation_id": "...",
    "parent_conversation_id": "...",
    "branch_depth": 1,
    "title": "...",
    "created_at": "..."
  }
]
```

### Frontend Components

#### MessageActions Component
Provides context menu for messages with branching options.

```tsx
import MessageActions from '@/components/chat/MessageActions';

<MessageActions
  message={message}
  conversationId={conversationId}
  onEdit={() => handleEdit()}
  onRegenerate={() => handleRegenerate()}
/>
```

#### BranchIndicator Component
Shows branch relationship information.

```tsx
import BranchIndicator from '@/components/chat/BranchIndicator';

<BranchIndicator
  conversationId={conversationId}
  metadata={conversation.metadata}
/>
```

#### BranchTree Component
Visual tree navigation for branches.

```tsx
import BranchTree from '@/components/chat/BranchTree';

<BranchTree
  conversationId={conversationId}
  onClose={() => setShowTree(false)}
/>
```

## User Experience Guidelines

### Visual Indicators

1. **Branch Badge**: Conversations show branch count badge
2. **Parent Link**: Branched conversations show "Branched from..." indicator
3. **Tree Icon**: Click to see full branch tree
4. **Message Menu**: Hover to reveal branching options

### Best Practices

#### When to Branch
- ✅ Exploring alternative approaches
- ✅ Comparing model responses
- ✅ Testing different prompts
- ✅ Team collaboration scenarios

#### When NOT to Branch
- ❌ Simple typo corrections (use edit instead)
- ❌ Linear conversation flow
- ❌ One-off questions

### Performance Considerations

**Storage**: Each branch duplicates message history
- Average message: ~1KB
- 50-message conversation branch: ~50KB
- 1000 users, 10 branches each: ~500MB

**Database Queries**:
- Branch creation: O(n) where n = messages copied
- Tree traversal: O(b^d) where b = branches, d = depth
- Optimized with indexes on parent_conversation_id

**Recommendations**:
- Limit branch depth to 10 levels
- Archive old branches automatically
- Implement branch pruning for unused branches

## Example Workflows

### Workflow 1: Model Comparison

```
1. User: "Explain quantum computing"
   Assistant (GPT-4o): [Response A]

2. User clicks "Regenerate" → selects Claude 3.5
   Creates Branch → Shows Claude response

3. User compares both responses side-by-side
   Chooses preferred branch
```

### Workflow 2: Prompt Refinement

```
1. User: "Write a function"
   Assistant: [Generic response]

2. User clicks "Edit message"
   Updates to: "Write a Python function to sort arrays"
   Creates Branch → Better response

3. User continues in improved branch
```

### Workflow 3: Team Collaboration

```
1. User A: Creates conversation about architecture
2. User A: Branches at design discussion
   Branch 1: Explores microservices
   Branch 2: Explores monolith

3. User B: Reviews both branches
4. Team: Discusses and merges insights
```

## Advanced Features

### Branch Merging (Future)
Combine insights from multiple branches.

```
Branch 1: Technical approach
Branch 2: Business approach
  ↓
Merged: Combined perspective
```

### Branch Annotations (Future)
Add notes to branches explaining purpose.

```
Branch: "Performance optimization attempt"
Note: "Testing caching strategies"
Result: "20% improvement achieved"
```

### Branch Templates (Future)
Pre-configured branching patterns.

```
Template: "Model Comparison"
- Auto-create 3 branches
- Use different models
- Compare results
```

## Troubleshooting

### Issue: Branch creation fails
**Solution**: Check database connection and constraints

### Issue: Branch tree too large
**Solution**: Implement pagination or depth limiting

### Issue: Slow branch operations
**Solution**: Add indexes, optimize queries, use caching

## Migration Guide

### Upgrading from v1.x

1. Run migration:
```bash
alembic upgrade 002_message_threading
```

2. Update frontend packages:
```bash
npm install
```

3. Restart services:
```bash
docker-compose restart backend frontend
```

### Data Migration

Existing conversations will work without changes. New branching features become available immediately.

## Security Considerations

1. **Access Control**: Users can only branch their own conversations
2. **Quotas**: Implement branch limits per user/organization
3. **Audit**: All branch operations logged
4. **Privacy**: Branch metadata respects original permissions

## Performance Metrics

**Target KPIs:**
- Branch creation: < 500ms
- Tree traversal: < 200ms
- Message regeneration: < 2s
- Branch navigation: < 100ms

**Monitoring:**
```sql
-- Track branch usage
SELECT COUNT(*) as total_branches,
       AVG(branch_count) as avg_branches_per_conversation
FROM conversations
WHERE parent_conversation_id IS NOT NULL;

-- Find deep branch trees
SELECT id, title, branch_count
FROM conversations
ORDER BY branch_count DESC
LIMIT 10;
```

## FAQ

**Q: How many branches can I create?**
A: No hard limit currently. Best practice: < 10 branches per conversation.

**Q: Do branches affect the original conversation?**
A: No. Branches are completely independent once created.

**Q: Can I merge branches?**
A: Not yet. This is a planned feature.

**Q: Are branches shared with my team?**
A: Branches follow the same sharing rules as conversations.

**Q: Does branching cost extra tokens?**
A: No. Branching copies existing messages without regenerating them.

**Q: Can I delete a branch?**
A: Yes. Deleting a branch doesn't affect the parent conversation.

---

**Version**: 2.0
**Last Updated**: 2024-01-15
**Feature Status**: ✅ Production Ready
