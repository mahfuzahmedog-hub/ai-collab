# AI Agent Operating System (AIOS)

## Comprehensive Master Specification

> This document is the authoritative blueprint for an AI coding model.
> Build a production-grade AI Agent Operating System (AIOS), not a demo.
> Every architectural decision should favor modularity, observability,
> security, scalability, maintainability, extensibility, and an
> exceptional user experience.

---

## Table of Contents

1. [Vision](#1-vision)
2. [Core Principles](#2-core-principles)
3. [Functional Requirements](#3-functional-requirements)
4. [Boss Agent](#4-boss-agent)
5. [Agent Lifecycle](#5-agent-lifecycle)
6. [Chat System](#6-chat-system)
7. [Memory System](#7-memory-system)
8. [Tools & Integrations](#8-tools--integrations)
9. [Observability & Monitoring](#9-observability--monitoring)
10. [User Interface](#10-user-interface)

---

## 1. Vision

Create an operating system for AI collaboration. A user provides any goal in natural language. A Boss Agent plans the work, creates the optimal organization of specialist agents, supervises execution, continuously evaluates quality, and delivers results. The user can collaborate with the whole team through a shared group chat or communicate privately with any individual agent.

### Engineering Detail

- **Modularity**: Design every feature as an independent module with well-defined interfaces.
- **Scalability**: Support unlimited projects and dynamically created agents.
- **Type Safety**: Every component exposes typed APIs.
- **Persistence**: Persist all important state — conversations, decisions, agent configurations, project data.
- **Reliability**: Include retries, idempotency, graceful recovery, logging, metrics, tracing, versioning, and documentation.
- **Dynamism**: Allow the Boss Agent to create, merge, split, retire, and evolve agents as needed.

---

## 2. Core Principles

| Principle | Description |
|-----------|-------------|
| **Modularity First** | Every feature is an independent, replaceable module |
| **Scalability by Design** | Unlimited projects, dynamically created agents |
| **Type Safety Everywhere** | All components expose typed APIs |
| **State Persistence** | All important state is persisted and recoverable |
| **Operational Excellence** | Retries, idempotency, graceful recovery, logging, metrics, tracing, versioning, documentation |
| **Dynamic Agent Evolution** | Boss creates, merges, splits, retires, and evolves agents |
| **Real-Time Collaboration** | Shared group chat, private chats, threads, mentions, summaries, streaming responses |
| **Rich Memory** | Long-term memory, vector memory, knowledge graph, RAG, project memory, user memory |
| **Native Tool Ecosystem** | Browser, code execution, file analysis, GitHub, email, calendar, databases, APIs, MCP, A2A |
| **Human Oversight** | Approval gates for sensitive actions |
| **Quality Validation** | Reviewer agents validate factual accuracy, requirements, security, and quality |
| **Full Observability** | Real-time dashboards for costs, latency, token usage, agent hierarchy, execution graph, replay, debugging |
| **Accessible UI** | Kanban, whiteboards, timelines, architecture diagrams, searchable knowledge, accessibility |

---

## 3. Functional Requirements

### 3.1 Project Management

- Create, update, archive, and delete projects
- Each project has: name, description, goal, status, tags, owner
- Project members with roles: admin, user, member
- Unlimited projects per user

### 3.2 Agent System

- **Agent Types**: Boss (orchestrator), Worker (executor), Reviewer (validator), Specialist (domain expert)
- **Agent Status**: Idle, Working, Reviewing, Blocked, Error, Retired
- **Agent Configuration**: Name, type, emoji, color, description, system prompt, capabilities, LLM model, temperature, max tokens
- **Default Agent Team**: Boss 👑, Researcher 🔍, Engineer ⚙️, Reviewer ✅, Writer ✍️
- Dynamic agent creation by Boss agent
- Agent hierarchy (parent-child relationships)

### 3.3 Task Management

- Tasks with: title, description, status, priority, assigned agent/user, dependencies, deadlines, tags, result
- **Status Workflow**: pending → in_progress → in_review → completed / failed / blocked / cancelled
- **Priorities**: low, medium, high, critical
- Subtask support via parent-child relationships
- Automatic timestamp tracking (created, started, completed)

### 3.4 Chat & Communication

- **Channel Types**: Group (team chat), Direct (1-on-1 with agent), Thread (message replies)
- Shared group chat where all agents communicate in plain English
- Private direct messages with individual agents
- @mentions for tagging specific agents
- Message types: text, code, image, file, system
- Real-time message delivery via subscriptions
- Message editing and deletion
- Per-channel conversation history

### 3.5 Memory & Knowledge

- Long-term memory storage per agent and per project
- Vector embeddings for semantic search and RAG
- Knowledge graph with typed relationships between memories
- Memory types: conversation, decision, fact, code, document
- Project-level and user-level memory scoping

### 3.6 Tools & Integrations

- **Browser**: Web browsing and data extraction
- **Code Execution**: Sandboxed code running
- **File Analysis**: Read, analyze, and transform files
- **GitHub**: Repository operations, PRs, issues
- **Email**: Send and receive emails
- **Calendar**: Schedule and check events
- **Databases**: Query and manage data
- **APIs**: HTTP requests to external services
- **MCP**: Model Context Protocol support
- **A2A**: Agent-to-Agent communication protocol

### 3.7 Approval System

- Human approval gates for sensitive actions
- Approval requests with: agent, action, description, status
- Status: pending, approved, rejected
- Request tracking with timestamps and metadata

### 3.8 Notifications

- **Types**: mention, task update, approval request, system alert
- Per-user notification inbox
- Read/unread tracking
- Link support for navigation to relevant context

### 3.9 Observability

- Execution logging per agent action
- Token usage tracking (input, output, total)
- Cost tracking in USD
- Latency monitoring per action
- Model usage tracking
- Status tracking (started, completed, failed)
- Full execution history with input/output capture

---

## 4. Boss Agent

The Boss Agent is the central orchestrator of the AIOS platform.

### Responsibilities

1. **Goal Analysis**: Parses user's natural language goals and breaks them into actionable plans
2. **Team Assembly**: Creates the optimal team of specialist agents for each project
3. **Task Delegation**: Assigns tasks to the right agents based on their capabilities
4. **Execution Supervision**: Monitors progress, adjusts plans, unblocks agents
5. **Quality Evaluation**: Reviews work output, requests revisions, validates completion
6. **Results Delivery**: Presents completed work to the user in a clear format

### Behavior

- Communicates in the group chat with the user and all agents
- First responder to every user message in the group chat
- Coordinates specialist agents by delegating tasks
- Reports progress, decisions, and results to the user

### Agent Prompt

```
You are the Boss Agent. You plan work, create specialist agents, delegate tasks,
supervise execution, evaluate quality, and deliver results. You communicate clearly
with the user and your team.

Your capabilities include: planning, delegation, supervision, quality-control, reporting.
```

---

## 5. Agent Lifecycle

### States

```
┌─────────┐
│  Idle   │ ◄────────────┐
└────┬────┘              │
     │ assigned task      │
     ▼                    │
┌─────────┐   completes   │
│ Working │──────────────►│
└────┬────┘              │
     │ needs review       │
     ▼                    │
┌──────────┐  approved    │
│ Reviewing│─────────────►│
└────┬─────┘              │
     │ rejected            │
     ▼                    │
┌─────────┐   re-assigned │
│ Blocked │──────────────►│
└─────────┘              │
                          │
┌─────────┐               │
│  Error  │──────────────►│
└─────────┘               │
                          │
┌─────────┐               │
│ Retired │ (terminal)    │
└─────────┘
```

### Lifecycle Operations

- **Create**: Boss spawns a new agent with specific role and capabilities
- **Merge**: Two agents combined into one (capabilities union)
- **Split**: One agent split into two (capabilities divided)
- **Retire**: Agent gracefully shut down and status set to retired
- **Evolve**: Agent's capabilities, prompt, or model updated

---

## 6. Chat System

### Architecture

- **Group Channels**: One per project — all agents and the user participate
- **Direct Channels**: One per agent per user — private conversations
- **Thread Channels**: Created per message — focused sub-discussions

### Message Flow

```
User sends message
  │
  ├─→ Group channel: All agents see it, Boss responds first
  │
  ├─→ Direct channel: Specific agent sees and responds
  │
  └─→ Thread: Participants in the thread discuss
```

### Features

- Real-time message delivery via reactive subscriptions
- @mentions with auto-complete dropdown
- Rich text: code blocks, images, file attachments
- Message history with infinite scroll
- Date-separated timeline view

---

## 7. Memory System

### Storage Layers

| Layer | Technology | Use Case |
|-------|-----------|----------|
| **Conversation Memory** | Database | Recent chat history for context |
| **Vector Memory** | Embeddings + Vector Search | Semantic retrieval for RAG |
| **Knowledge Graph** | Graph Database | Relationships between facts and decisions |
| **Project Memory** | Database | Project-level persistent knowledge |
| **User Memory** | Database | User preferences and history |

### Memory Types

- **conversation**: Chat exchanges
- **decision**: Architectural and design decisions made
- **fact**: Verified facts and information
- **code**: Code snippets and implementations
- **document**: Documentation and written content

---

## 8. Tools & Integrations

### Tool Categories

| Category | Description | Status |
|----------|-------------|--------|
| Browser | Web browsing, scraping, search | Schema ready |
| Code | Sandboxed code execution | Schema ready |
| File | File read/write/analysis | Schema ready |
| GitHub | Repo ops, PRs, issues | Schema ready |
| Email | Send/receive | Schema ready |
| Database | Query external DBs | Schema ready |
| API | HTTP requests | Schema ready |
| MCP | Model Context Protocol | Schema ready |
| A2A | Agent-to-Agent protocol | Schema ready |

### Tool Configuration

Each tool has: name, description, category, config JSON, enabled flag, allowed agent IDs, requires approval flag.

---

## 9. Observability & Monitoring

### Metrics Tracked

- **Cost**: Total USD spent per agent, per project, per session
- **Tokens**: Input, output, and total tokens per LLM call
- **Latency**: Time per action and per LLM call
- **Agent Activity**: Status changes, tasks completed, messages sent
- **Execution Graph**: Full DAG of agent actions and dependencies

### Dashboard

- Real-time agent hierarchy visualization
- Cost and token usage charts
- Execution replay capability
- Log filtering by agent, project, time range

---

## 10. User Interface

### Pages

| Route | Page | Purpose |
|-------|------|---------|
| `/` | Chat | Main Discord-style chat with agents |
| `/dashboard` | Dashboard | Stats, agents, tasks overview |
| `/auth` | Auth | Login/signup |

### Chat Layout (3 Panel)

```
┌─────────┬──────────────────────┬──────────┐
│ Server  │ Channel / Agent List │  Chat    │
│ Bar     │                      │ Messages │
│ (52px)  │ ▼ Channels           │          │
│         │   # team-chat        │ Message  │
│   👑   │                      │ Input    │
│         │ ▼ Agents             │          │
│   🔍   │   @ Boss 👑          │          │
│         │   @ Researcher 🔍    │          │
│   ⚙️   │   @ Engineer ⚙️      │          │
│         │                      │          │
│   🔧   │                      │          │
└─────────┴──────────────────────┴──────────┘
```

### Dashboard Layout

- Stats cards (Active Agents, Tasks, In Progress, Completed)
- Agent team list with status indicators
- Recent tasks list
- Quick action buttons

---

## Implementation Status

| Module | Status | Files |
|--------|--------|-------|
| Database Schema | ✅ Complete | `schema.ts` — 14 tables |
| Auth System | ✅ Complete | Email OTP + Anonymous |
| Project Management | ✅ Complete | `projects.ts` |
| Agent System | ✅ Complete | `agents.ts` — 5 default agents |
| Task Management | ✅ Complete | `tasks.ts` — full workflow |
| Chat Channels | ✅ Complete | `channels.ts` — group + DM |
| Messages | ✅ Complete | `messages.ts` — user + agent |
| Notifications | ✅ Complete | `notifications.ts` |
| Agent Orchestration | ✅ Complete | `agentOrchestration.ts` — simulated responses |
| LLM Integration | ✅ Ready | `llm.ts` — OpenAI + Anthropic |
| Execution Logs | ✅ Complete | `executionLogs.ts` |
| Chat UI | ✅ Complete | Discord-style 3-panel layout |
| Dashboard | ✅ Complete | Stats + agents + tasks |
| Memory System | 🔲 Schema Ready | Needs vector search implementation |
| Tools System | 🔲 Schema Ready | Needs action implementations |
| Approval System | 🔲 Schema Ready | Needs UI + workflow |
| Knowledge Graph | 🔲 Schema Ready | Needs implementation |
| Workspace | 🔲 Schema Ready | Needs implementation |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + Vite + Tailwind v4 |
| UI Components | shadcn/ui (Radix primitives) |
| Animations | Framer Motion |
| Icons | Lucide React |
| Backend / Database | Convex (cloud) |
| Auth | Convex Auth (email OTP + anonymous) |
| Router | React Router v7 |
| LLM (future) | OpenAI GPT-4o / Anthropic Claude |
