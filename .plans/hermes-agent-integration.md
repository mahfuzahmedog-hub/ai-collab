# Hermes Agent Integration Plan

## Objective
Transform AI Collab's agent system to behave like Hermes Agent — tool-calling loop, memory system, skills system, learning loop, and rich context assembly.

## Current State
- Regex `[ACTION]` blocks for tool use (fragile, non-standard)
- No memory system (short-term only in agent model)
- No skills system
- Simple think→send loop (single-turn)
- Flat system prompt
- No learning/curation

## Architecture Overview (Target)

```
User Message
    │
    ▼
System Prompt Assembly
  ├── Personality/Identity
  ├── Workspace Context (project, files)
  ├── Skills (loaded from library)
  ├── Memories (relevant facts recalled)
  ├── Conversation History
  ├── Tool Definitions (JSON schemas)
  └── Current Task/Mission
    │
    ▼
LLM Call (with function calling)
    │
    ├──► Text Response
    │     └──► Stream to user
    │
    └──► Tool Call
          │
          ▼
    Tool Dispatch & Execution
          │
          ▼
    Observation Collection
          │
          ▼
    LLM Call (with observation)
          │
          └──► (repeat until done)
    │
    ▼
Background Curation (async)
  ├── Review conversation
  ├── Create skills from experience
  ├── Save important memories
  └── Update user profile
```

---

## Phase 1: Tool Calling System (Replace [ACTION])

### 1.1 Tool Registry (`backend/app/tools/registry.py`) — NEW
- `ToolRegistry` singleton
- `ToolDef` Pydantic model: `name`, `description`, `parameters` (JSON Schema), `handler` (async callable)
- `register(tool)` / `get(name)` / `list()` / `to_openai_schemas()` methods
- `to_openai_schemas()` returns list of OpenAI function-calling format dicts

### 1.2 Convert Hermes Tool Schema (`backend/app/tools/schema.py`) — NEW
- Hermes-compatible JSON Schema for each tool
- Tool types to port:
  - `read_file` / `write_file` / `list_files` — workspace fs
  - `browse` / `screenshot` — web
  - `run_python` / `run_shell` — code exec
  - `web_search` — search
  - `http_get` / `http_post` / `http_put` / `http_delete` — API
  - `create_agent` / `evolve_agent` / `merge_agents` / `split_agent` / `retire_agent`
  - `create_channel` / `rename_channel` / `delete_channel`
  - `create_task` / `update_task`
  - `send_message` — to channel/dm
  - `create_thread`
  - `remember` — save to memory
  - `create_skill` — procedural memory creation

### 1.3 Refactor Agent Loop (`backend/app/agents/base_agent.py`) — REWRITE
Replace current `think_stream` with Hermes-style loop:

```
async def run_turn(messages):
    # 1. Call LLM with tool definitions
    response = await llm.chat(messages + [tool_defs])
    
    # 2. Process response
    while response.has_tool_calls:
        for call in response.tool_calls:
            # Execute tool
            result = await tool_registry.dispatch(call.name, call.args)
            # Add observation to messages
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
        
        # 3. Call LLM again with observations
        response = await llm.chat(messages)
    
    # 4. Return final text
    return response.text
```

### 1.4 Provider Tool-Calling Support (`backend/app/llm/providers.py`) — MODIFY
- Add `tool_choice` param to `chat()` and `chat_stream()`
- Pass `tools` array to OpenAI-compatible providers
- Parse `tool_calls` from response choices
- Add `chat_with_tools()` method to `LLMProvider` base

### 1.5 Streaming with Tool Calls (`backend/app/websocket/handlers.py`) — MODIFY
- Relay tool_call_start / tool_call_result events to frontend
- Stream text content interleaved with tool call notifications

**Files affected:** NEW `tools/registry.py`, `tools/schema.py`; MODIFY `agents/base_agent.py`, `llm/providers.py`, `llm/base.py`, `websocket/handlers.py`

---

## Phase 2: Memory System

### 2.1 Memory Manager (`backend/app/memory/manager.py`) — NEW
- SQLite-backed with FTS5 full-text search (like Hermes `hermes_state.py`)
- Memory types: `fact`, `conversation`, `decision`, `code`, `user_preference`, `user_profile`
- CRUD operations: `save(memory)`, `search(query)`, `recall(context)`, `forget(id)`
- `recall(context)` — FTS5 search + recent + relevance ranking
- `consolidate()` — merge duplicate/related memories
- Embedding support via OmniRoute `_get_embedding_via_omniroute()` for vector search

### 2.2 Memory Models (`backend/app/models/memory.py`) — MODIFY
Extend existing `Memory` model:
```python
class Memory(BaseModel):
    id: str
    type: MemoryType  # enum
    content: str
    scope: str  # "agent" | "project" | "user" | "global"
    source: str  # "conversation" | "curation" | "manual"
    tags: list[str]
    embedding: list[float] | None
    created_at: datetime
    last_accessed: datetime
    access_count: int
    importance: float  # 0.0-1.0
    metadata: dict
```

### 2.3 Memory Injection (`backend/app/agents/memory_injector.py`) — NEW
- Before each LLM call, recall relevant memories
- Format as "Memories:" section in system prompt
- Trim to token budget (~2000 tokens)
- Track what was injected for dedup

### 2.4 Memory During Conversation (`backend/app/agents/base_agent.py`) — MODIFY
- After each assistant response, analyze for savable memories
- Save important facts, user preferences, decisions
- Update user profile memory

**Files affected:** NEW `memory/manager.py`, `memory/injector.py`; MODIFY `models/memory.py`, `agents/base_agent.py`, `db/models.py`, `db/repository.py`

---

## Phase 3: Skills System

### 3.1 Skill Models (`backend/app/skills/models.py`) — NEW
```python
class Skill(BaseModel):
    id: str
    name: str
    description: str
    category: str  # "workflow" | "knowledge" | "template" | "integration"
    prompt_template: str  # Instructions injected into system prompt
    trigger_phrases: list[str]  # Auto-activate on these keywords
    parameters: dict  # JSON Schema for skill parameters
    usage_count: int
    success_rate: float
    created_at: datetime
    last_used: datetime
    version: int
```

### 3.2 Skill Library (`backend/app/skills/library.py`) — NEW
- Load skills from filesystem (`~/.ridoy/skills/`)
- Skills Hub compatible format (YAML frontmatter + markdown body)
- `load_skill(name)` / `list_skills(category)` / `save_skill(skill)` / `delete_skill(name)`
- FTS5 search across skill descriptions and content

### 3.3 Skill Loader (`backend/app/skills/loader.py`) — NEW
- Before LLM call, analyze user message for trigger phrases
- Load matching skills into system prompt
- Format as "Relevant Skills:" section
- Budget-limited (summarize if too many skills match)

### 3.4 Skill Creation (`backend/app/skills/creator.py`) — NEW
- After complex task completion, prompt LLM to create skill
- Extract reusable procedure from conversation history
- Save as skill with description, template, trigger phrases
- Compatible with agentskills.io open standard

### 3.5 Skill Improvement (`backend/app/skills/improver.py`) — NEW
- Track skill usage and outcomes
- After each use, prompt LLM to suggest improvements
- Version skills with changelog
- Auto-apply improvements if success rate drops below threshold

**Files affected:** NEW `skills/models.py`, `skills/library.py`, `skills/loader.py`, `skills/creator.py`, `skills/improver.py`

---

## Phase 4: Enhanced Agent Loop

### 4.1 Rich System Prompt (`backend/app/agents/prompt_builder.py`) — NEW
Build system prompt from modular sections:

```
# Identity & Personality
You are {name}, a {role} with...

# Mission & Context
Current project: {project.title}
Team members: {team_members}

# Workspace
{files, git branch, recent changes}

# Memories
{relevant memories from recall}

# Skills
{active skills loaded from library}

# Available Tools
{tool definitions in OpenAI format}

# Instructions
{core behavioral rules, output format, safety rules}
```

### 4.2 Context Compression (`backend/app/agents/context_compressor.py`) — NEW
- Token counting (tiktoken)
- Budget allocation: system 25%, history 50%, new context 25%
- Summarize old conversation turns when over budget
- Prioritize recent turns, tool results, user messages
- Compression trigger: `compress --background` or auto when >80% budget

### 4.3 Subagent Delegation (`backend/app/agents/delegator.py`) — NEW
- Tool: `delegate_to_agent(name, task, skills_needed)`
- Spawns isolated agent with own context, tools, mission
- Hermes-style: `[DELEGATE]` or structured tool call
- Parallel workstreams via `asyncio.gather`
- Result collection and synthesis

### 4.4 Agent State Machine (`backend/app/agents/state_machine.py`) — MODIFY
Currently 24 states in LifecycleEngine. Simplify to Hermes-like:
- `idle` → `thinking` (LLM call in progress)
- `thinking` → `awaiting_tool` (waiting for tool result)
- `awaiting_tool` → `thinking` (tool returned, continue)
- `thinking` → `idle` (response sent to user)
- `thinking` → `delegated` (subagent spawned)
- `delegated` → `thinking` (subagent result received)

### 4.5 Token & Cost Tracking (`backend/app/agents/cost_tracker.py`) — MODIFY
- Real token counting from LLM responses
- Per-model cost calculation
- Session-level accumulation
- `/usage` command display

**Files affected:** NEW `agents/prompt_builder.py`, `agents/context_compressor.py`, `agents/delegator.py`; MODIFY `agents/base_agent.py`, `services/lifecycle.py`

---

## Phase 5: Learning Loop

### 5.1 Curator Agent (`backend/app/curator/curator.py`) — NEW
- Background agent that reviews conversations asynchronously
- Triggered after message exchanges, periodic, or manual `/curate`
- Runs with limited tool access (read-only: read memory, read skill library)
- Produces:
  - New memory entries (facts, preferences, decisions)
  - New skills (reusable procedures)
  - User profile updates
  - Skill improvement suggestions

### 5.2 Curation Triggers (`backend/app/curator/triggers.py`) — NEW
- After every 5 messages in a conversation
- On explicit `/curate` command
- Periodic (every 30 min of inactivity)
- After task completion

### 5.3 User Profiling (`backend/app/curator/profile.py`) — NEW
- Build and maintain "who the user is" profile
- Preferences, communication style, domain expertise
- Updates from conversation analysis
- Injected into system prompt

### 5.4 Curator Scheduling (`backend/cron/curator.py`) — NEW (standalone script)
- Can run as separate process or background task
- Non-blocking (fire-and-forget from main agent loop)
- Results saved to DB for next system prompt construction

**Files affected:** NEW `curator/curator.py`, `curator/triggers.py`, `curator/profile.py`, `cron/curator.py`

---

## Phase 6: Frontend Changes

### 6.1 Tool Call Visualization (`frontend/src/components/chat/ToolCallCard.tsx`) — NEW
- Display tool calls as collapsible cards in chat stream
- Show: tool name, arguments (formatted), result (truncated)
- Status: pending → running → completed / failed

### 6.2 Streaming Tool Calls in Timeline (`frontend/src/components/timeline/Timeline.tsx`) — MODIFY
- Interleave text chunks with tool call cards
- Maintain read order: text → tool → observation → text

### 6.3 Memory & Skills UI (`frontend/src/features/knowledge/`) — NEW
- Memory browser: search, filter by type, view detail
- Skill library: browse, create, edit, test
- User profile viewer

### 6.4 Store Updates (`frontend/src/store/index.ts`) — MODIFY
- Add `memories`, `skills`, `userProfile` slices
- Add `toolCalls` slice for tracking in-progress tools

**Files affected:** NEW `components/chat/ToolCallCard.tsx`, `features/knowledge/MemoryPanel.tsx`, `features/knowledge/SkillPanel.tsx`; MODIFY `components/timeline/Timeline.tsx`, `store/index.ts`, `types/index.ts`

---

## Phase 7: Testing & Verification

### 7.1 Tool Calling E2E (`tests/test_tool_calling.py`) — NEW
- Mock LLM returning tool call
- Verify dispatch, execution, observation loop
- Verify error handling (tool fails → retry/fix)

### 7.2 Memory Integration (`tests/test_memory.py`) — NEW
- Save memory, search, recall
- FTS5 search quality
- Memory injection into system prompt

### 7.3 Skills System (`tests/test_skills.py`) — NEW
- Create, load, list skills
- Skill trigger matching
- Skill improvement flow

### 7.4 Full Agent Loop (`tests/test_agent_loop.py`) — NEW
- Multi-turn tool calling
- Context compression
- Learning loop

---

## Implementation Order

```
Week 1: Phase 1 (Tool System) + Phase 4.1 (Prompt Builder)
  - This is the foundation everything else builds on
  - Changes how LLM calls work at the core
  
Week 2: Phase 2 (Memory System)
  - FTS5-backed persistent memory
  - Memory injection into context
  - Makes the agent remember across sessions

Week 3: Phase 3 (Skills System)
  - Skill library and loading
  - Skill creation from experience
  - Makes the agent learn reusable procedures

Week 4: Phase 4 (Enhanced Loop) + Phase 5 (Learning Loop)
  - Context compression
  - Subagent delegation
  - Background curator
  - Makes the agent autonomous and self-improving

Week 5: Phase 6 (Frontend) + Phase 7 (Tests)
  - Tool call visualization
  - Memory/skills UI
  - Integration tests
```

## Key Hermes Patterns to Adopt

| Pattern | Hermes Approach | Our Replacement |
|---|---|---|
| Tool calling | OpenAI function calling | Same format (OpenAI compatible via OmniRoute) |
| Memory | SQLite FTS5 + Honcho | SQLite FTS5 + OmniRoute embeddings |
| Skills | Filesystem YAML + markdown | Same format |
| System prompt | Modular assembly | PromptBuilder modular sections |
| Context compression | Token-count based summarization | tiktoken + summarization |
| Curator | Forked subagent with limited tools | Same pattern |
| Delegation | [DELEGATE] tool call | Tool-based delegation |
| Provider chain | Ordered fallback + retry | Already have this in OmniRouteProvider |
| Streaming | Yield chunks + tool call interleaving | Enhanced stream_chunk events |
| Gateway | Telegram/Discord/Slack/CLI | Same platform support + Web UI |
