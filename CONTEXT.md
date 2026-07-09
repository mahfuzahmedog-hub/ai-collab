# AIOS Platform — Complete Build Context

> **Repository**: [mahfuzahmedog-hub/ai-collab](https://github.com/mahfuzahmedog-hub/ai-collab)
> **Stack**: React 19 + Vite + Convex + Tailwind v4 + shadcn/ui + Framer Motion
> **Deployment**: Convex cloud (`https://lovely-lion-156.convex.cloud`)
> **Date**: July 9, 2026

---

## Table of Contents

1. [Project Origin](#1-project-origin)
2. [Tech Stack](#2-tech-stack)
3. [What Was Built](#3-what-was-built)
4. [Backend — Convex Functions](#4-backend--convex-functions)
5. [Frontend — Pages & Components](#5-frontend--pages--components)
6. [Agent Orchestration Engine](#6-agent-orchestration-engine)
7. [Database Schema](#7-database-schema)
8. [Fixes Applied](#8-fixes-applied)
9. [Architecture Flow](#9-architecture-flow)
10. [File Inventory](#10-file-inventory)
11. [To Do / Future Work](#11-to-do--future-work)

---

## 1. Project Origin

This project started as a **fresh vite-template** (React 19 + Convex + Tailwind v4 + shadcn/ui) with only auth scaffolding and a basic landing page. The goal was to build an **AI Agent Operating System (AIOS)** — a Discord-style chat interface where users collaborate with a team of AI agents.

The vision was inspired by:
- **mahfuzahmedog-hub/ai-collab** — An Autonomous Multi-Agent AI Collaboration Platform (original Python FastAPI + Next.js)
- **AIOS Comprehensive Master Specification** — A 30+ module spec covering agent lifecycle, chat, memory, tools, observability, and more

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Convex instead of FastAPI | Already configured in template, provides realtime subscriptions, serverless, built-in auth |
| React instead of Next.js | Vite template already set up, faster iteration for SPA |
| Anonymous auth | Skip sign-in wall, let users jump straight to the experience |
| Simulated agent responses | No API key required to demo; swap for real LLM later |
| Discord-style UI | Familiar chat layout — server bar, channel list, message area, member panel |

---

## 2. Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| **UI Library** | React | 19 |
| **Bundler** | Vite | Latest |
| **Styling** | Tailwind CSS | v4 |
| **Animation** | Framer Motion | Latest |
| **Icons** | Lucide React | Latest |
| **UI Components** | shadcn/ui (Radix primitives) | 50+ components |
| **Backend/Database** | Convex | Cloud deployment |
| **Auth** | Convex Auth | Email OTP + Anonymous |
| **Routing** | React Router | v7 |
| **State** | Convex reactive queries + hooks | |

**Environment**: Freebuff WebContainer (in-browser Linux, Node.js v22, npm 10)

---

## 3. What Was Built

### From Scratch (Did Not Exist Before)

| Category | Files | Lines of Code |
|----------|-------|--------------|
| Database Schema | `src/convex/schema.ts` | ~200 lines, 14 tables |
| Backend Functions | 9 modules (`projects.ts`, `agents.ts`, `tasks.ts`, `channels.ts`, `messages.ts`, `notifications.ts`, `llm.ts`, `agentOrchestration.ts`, `executionLogs.ts`) | ~1,200 lines |
| Discord Chat UI | `Chat.tsx`, `ChannelSidebar.tsx`, `MessageList.tsx`, `MessageInput.tsx` | ~600 lines |
| Dashboard | `Dashboard.tsx` | ~250 lines |
| Landing Page | `Landing.tsx` (replaced) | ~300 lines |
| Agent Response Engine | `agentOrchestration.ts` | ~250 lines |

### Pre-Existing (Preserved)

| File | Purpose |
|------|---------|
| `src/convex/auth.ts` | Auth helpers |
| `src/convex/auth.config.ts` | Auth provider config |
| `src/convex/http.ts` | HTTP endpoint actions |
| `src/convex/users.ts` | Current user query |
| `src/hooks/use-auth.ts` | Auth React hook |
| `src/hooks/use-mobile.ts` | Mobile detection |
| `src/pages/Auth.tsx` | Auth page (email OTP + anonymous) |
| `src/pages/NotFound.tsx` | 404 page |
| 50+ shadcn/ui components | `src/components/ui/` |
| `src/main.tsx` | Entry point (modified) |
| `src/index.css` | Theme variables (modified) |

---

## 4. Backend — Convex Functions

### `src/convex/projects.ts` — Project Management
- **Queries**: `list` (user's projects via membership), `get` (single project)
- **Mutations**: `create` (auto-adds creator as admin), `update` (patch), `remove` (admin-only), `addMember`, `listMembers`

### `src/convex/agents.ts` — Agent System
- **Queries**: `list`, `get`, `getBossAgent`, `getByParent`
- **Mutations**: `create`, `update`, `remove` (soft-delete → retired), `setStatus`
- **Setup**: `setupDefaultAgents` — Creates 5 agents:

| Agent | Emoji | Role | Color | Capabilities |
|-------|-------|------|-------|-------------|
| Boss | 👑 | Orchestrator | `#8B5CF6` | planning, delegation, supervision, quality-control, reporting |
| Researcher | 🔍 | Information | `#3B82F6` | web-search, data-analysis, fact-checking, summarization |
| Engineer | ⚙️ | Builder | `#10B981` | coding, architecture, code-review, debugging, testing |
| Reviewer | ✅ | QA | `#F59E0B` | qa, security-audit, requirements-validation, fact-checking |
| Writer | ✍️ | Documentation | `#EC4899` | documentation, content-creation, editing, formatting |

### `src/convex/tasks.ts` — Task Management
- **Queries**: `list`, `get`, `listByStatus`, `listByAgent`, `listByUser`
- **Mutations**: `create`, `update` (full status workflow with auto-timestamps), `remove`
- **Status workflow**: pending → in_progress → in_review → completed / failed / blocked / cancelled
- **Priorities**: low, medium, high, critical
- **Features**: Dependencies, parent tasks, deadlines, tags, result tracking

### `src/convex/channels.ts` — Chat Channels
- **Types**: `group` (team chat), `direct` (1-on-1 with agent), `thread` (message replies)
- **Queries**: `list`, `get`, `getGroupChannel`, `getDirectChannel`
- **Mutations**: `create`, `setupDefaultChannels` (group chat + per-agent DMs), `updateLastActivity`

### `src/convex/messages.ts` — Chat Messages
- **Sender types**: `user` (human) and `agent` (AI)
- **Content types**: text, code, image, file, system
- **Queries**: `list` (by channel, paginated), `get`, `listBySender`, `listByAgent`
- **Mutations**: `send`, `sendAgentMessage`, `edit`, `remove`

### `src/convex/notifications.ts` — Notifications
- **Types**: mention, task, approval, message, system
- **Queries**: `list`, `unreadCount`
- **Mutations**: `create`, `markRead`, `markAllRead`

### `src/convex/llm.ts` — LLM Integration (Future Use)
- **Providers**: OpenAI (default), Anthropic (configured)
- **Actions**: `chat` (direct API call), `generateAgentResponse` (with agent context)
- Reads `OPENAI_API_KEY` from environment
- Logs all executions to `executionLogs`

### `src/convex/executionLogs.ts` — Observability
- Records: agentId, action, status, tokensUsed, costUsd, latencyMs, model, error

---

## 5. Frontend — Pages & Components

### `src/pages/Chat.tsx` — Discord-Style Chat (Main Screen)
```
┌─────────────────────────────────────────────────────┐
│ Server │ Channels      │ Chat Messages    │ Team    │
│ Bar     │ & Agents      │                  │ Panel   │
│ (52px)  │               │                  │         │
│   👑   │ ▼ Channels   │ 👑 Boss Agent    │ Online  │
│         │  # Team Chat  │ Hey! What should │ — 5    │
│  👥    │               │ we build today?  │         │
│         │ ▼ Agents     │ ──── Today ──── │ 👑 Boss │
│  🔍    │  @ Boss 👑   │ You: Build a     │ 🔍 Res  │
│         │  @ Researcher│ todo app         │ ⚙️ Eng  │
│  ⚙️    │  @ Engineer  │                  │ ✅ Rev  │
│         │               │                  │ ✍️ Wri  │
│  🔧    │               │ [Message input]  │         │
└─────────────────────────────────────────────────────┘
```

**Features:**
- Auto-login as anonymous guest
- Auto-creates project + 5 agents + group chat + DMs on first visit
- Boss agent sends welcome message
- Messages sent via `processUserMessage` action (triggers agent responses)
- Three-panel Discord layout: sidebar | messages | team panel (responsive — sidebar hidden on mobile, team panel hidden on tablet)

### `src/components/chat/ChannelSidebar.tsx`
- **Server Bar**: Narrow 52px strip — AIOS home, Team, Search, Settings icons with tooltips
- **Channel List**: Group chat channels with `#` prefix, active state highlighting
- **Agent List**: DM entries with emoji avatar + colored status dot (green=idle, blue=working, yellow=reviewing, red=error/blocked, gray=retired)
- **Unread Badge**: Shows on server name header

### `src/components/chat/MessageList.tsx`
- Agent avatars with gradient backgrounds (purple→blue for agents, green→emerald for users)
- Badge labels: "Agent" / "You"
- **Date separators**: Today / Yesterday / formatted date
- **Hover timestamps**: Only visible on hover
- **Code blocks**: Rendered in styled `<pre>` with code header
- **Auto-scroll**: Scrolls to bottom on new messages
- **Sender grouping**: Same-sender consecutive messages hide the avatar

### `src/components/chat/MessageInput.tsx`
- **Auto-resizing textarea**: Grows up to 200px
- **@mentions**: Type `@` to open agent dropdown, filter by typing, arrow keys + Enter to select, Escape to close
- **Send button**: Shows spinner while sending, disables when empty
- **Keyboard shortcuts**: Enter=send, Shift+Enter=newline
- **Footer hint**: Shows available shortcuts
- **Attachment button**: Stub for future file uploads

### `src/pages/Dashboard.tsx`
- **Stats cards**: Active Agents, Tasks, In Progress, Completed — with icons and detail text
- **Agent team list**: Avatars with status indicators, type badges, descriptions
- **Recent tasks**: Status dots + title + status badge
- **Quick actions**: Open Chat, Create Task, View Activity Log

### `src/pages/Landing.tsx` (Replaced, Kept for Reference)
Was replaced as the root route. Still exists but `/` now loads `ChatPage` directly. Contains:
- Hero section with gradient text "AI Collaboration"
- 6 feature cards
- How-it-works steps
- CTA section
- Footer

---

## 6. Agent Orchestration Engine

### `src/convex/agentOrchestration.ts` — `processUserMessage` Action

This is the core loop that makes agents respond when the user sends a message.

```
User sends "Build me a todo app"
  │
  ├─ 1. Save user message to channel (api.messages.send)
  │
  ├─ 2. Get channel + all agents
  │
  ├─ 3. Determine responding agents:
  │     ├─ Group chat: Boss always + specialists by keywords
  │     │   "build" → Engineer chimes in
  │     │   "research" → Researcher chimes in
  │     └─ DM: Only the specific agent
  │
  ├─ 4. For each agent (max 3, 300ms apart):
  │     ├─ Mark agent as "working"
  │     ├─ Generate contextual response
  │     │   - Keyword matching (hello, bug, code, research, ...)
  │     │   - Agent-specific templates (8 Boss, 5 per specialist)
  │     │   - Personality endings per agent
  │     ├─ Post response via sendAgentMessage
  │     └─ Mark agent as "idle"
  │
  └─ Return messageId
```

**Simulated Response Keywords:**

| Keyword | Agent(s) | Behavior |
|---------|----------|----------|
| hello / hi / hey | Boss | Greeting + "what should we build?" |
| thanks / thank you | Responding agent | "You're welcome!" |
| help / can you | Boss | "Let me look into this" |
| bug / fix / issue | Engineer / Reviewer | Investigate + QA |
| code / build / implement | Engineer | Architecture + implementation |
| research / search / find | Researcher | Gather information |
| write / doc / document | Writer | Draft documentation |
| review / check / validate | Reviewer | Quality check |
| plan / strategy / approach | Boss | Strategic planning |
| test / deploy / release | Engineer + Reviewer | Prep + QA |
| idea / suggest / what if | Boss | Brainstorming |

---

## 7. Database Schema

### 14 Tables (defined in `src/convex/schema.ts`)

| Table | Key Fields | Indexes |
|-------|------------|---------|
| `users` | name, image, email, emailVerificationTime, isAnonymous, role | email |
| `projects` | name, description, goal, ownerId, status, tags | owner, status |
| `projectMembers` | projectId, userId, role, joinedAt | project, user, project_user |
| `agents` | projectId, name, type, status, emoji, description, systemPrompt, capabilities, parentAgentId, llmModel, temperature, maxTokens, color, createdAt, retiredAt | project, parent, status, type |
| `tasks` | projectId, title, description, status, priority, assignedAgentId, assignedUserId, parentTaskId, dependencies, createdBy, createdAt, startedAt, completedAt, deadline, tags, result, metadata | project, status, agent, parent, assignee |
| `channels` | projectId, name, type, agentIds, participantUserIds, parentChannelId, isDefault, createdAt, lastActivityAt | project, type, parent |
| `messages` | channelId, projectId, senderId, senderName, senderType, agentId, content, contentType, mentions, parentMessageId, threadChannelId, metadata, createdAt, editedAt | channel, project, sender, agent, parent, channel_time |
| `tools` | projectId, name, description, category, config, enabled, allowedAgentIds, requiresApproval, createdAt | project, category, enabled |
| `approvals` | projectId, agentId, taskId, action, description, status, requestedBy, approvedBy, requestedAt, resolvedAt, metadata | project, agent, task, status |
| `memories` | projectId, agentId, type, title, content, embedding, sourceIds, tags, createdAt | project, agent, type |
| `knowledgeEdges` | sourceMemoryId, targetMemoryId, relationship, weight, createdAt | source, target |
| `executionLogs` | projectId, agentId, taskId, action, status, input, output, tokensUsed, costUsd, latencyMs, model, error, createdAt, completedAt | project, agent, task, status, created |
| `workspaces` | projectId, agentId, name, type, parentId, content, mimeType, size, metadata, createdAt, updatedAt | project, agent, parent |
| `notifications` | userId, projectId, type, title, body, read, link, createdAt | user, read, user_time |

**Enums**: ROLES (admin/user/member), AGENT_STATUS (idle/working/reviewing/blocked/error/retired), AGENT_TYPE (boss/worker/reviewer/specialist), TASK_STATUS (7 states), CHANNEL_TYPE (group/direct/thread), TOOL_CATEGORY (browser/code/file/github/email/database/api/mcp/a2a/custom)

---

## 8. Fixes Applied

### Fix 1: Missing Routes
**Problem**: Landing page CTAs navigated to `/chat` and dashboard to `/dashboard`, but neither route existed in `main.tsx`. Clicking would hit the 404 page.

**Fix**: Added lazy imports + routes for `ChatPage` and `DashboardPage`.

### Fix 2: Missing Optional Prop
**Problem**: `ChannelSidebar` required `selectedDirectAgentId: string | null` as mandatory, but `Chat.tsx` didn't pass it.

**Fix**: Changed to optional: `selectedDirectAgentId?: string | null`.

### Fix 3: Skip Landing Page
**Problem**: App loaded the marketing landing page first; user had to click through to reach the chat.

**Fix**: Swapped root route from `<Landing />` to `<ChatPage />`. Auth redirect now goes to `/chat`.

### Fix 4: No Agent Responses
**Problem**: User messages went nowhere — the `send` mutation just saved the message with no agent trigger.

**Fix**: Created `agentOrchestration.ts` with `processUserMessage` action. Chat.tsx now calls this action instead of the raw mutation. Actions can call mutations → saves user message, triggers agent response, posts reply.

### Fix 5: LLM Dependency for Demo
**Problem**: Agents couldn't respond without an OpenAI API key.

**Fix**: Replaced LLM call with simulated response engine — keyword-mapped, agent-specific templates. No API key needed. Real LLM path preserved for later swap.

---

## 9. Architecture Flow

```
┌──────────────────────────────────────────────────────────────┐
│                     BROWSER (React App)                       │
│                                                              │
│  ┌─────────┐  ┌──────────────────┐  ┌────────────────────┐  │
│  │ Landing  │  │    Auth Page     │  │  Discord Chat UI   │  │
│  │ (unused) │  │  (email OTP /    │  │  ┌──────────────┐  │  │
│  └──────────┘  │   anonymous)     │  │  │ Sidebar      │  │  │
│                └──────────────────┘  │  │ MessageList  │  │  │
│                                      │  │ MessageInput │  │  │
│                                      │  └──────────────┘  │  │
│                                      └────────────────────┘  │
│                                            │                  │
│                                      useQuery / useMutation  │
│                                      useAction                │
└──────────────────────────────────────┬───────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    CONVEX CLOUD DEPLOYMENT                    │
│              (https://lovely-lion-156.convex.cloud)          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    QUERIES                            │   │
│  │  projects.list  agents.list  channels.list            │   │
│  │  messages.list  tasks.list    notifications.unread   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   MUTATIONS                          │   │
│  │  projects.create  agents.create  tasks.create        │   │
│  │  channels.setup  messages.send   sendAgentMessage    │   │
│  │  agents.setStatus                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    ACTIONS                            │   │
│  │  processUserMessage → send user msg → trigger agent  │   │
│  │  sendWelcomeMessage → Boss intro message             │   │
│  │  generateAgentResponse → LLM call (future use)       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  DATABASE (14 tables)                 │   │
│  │  users  projects  projectMembers  agents  tasks      │   │
│  │  channels  messages  tools  approvals  memories      │   │
│  │  knowledgeEdges  executionLogs  workspaces           │   │
│  │  notifications                                       │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Message Send Flow (Detailed)

```
User types "Build a todo app" → hits Enter
  │
  ├─ Frontend: Chat.tsx handleSendMessage
  │   └─ Calls api.agentOrchestration.processUserMessage (ACTION)
  │
  ├─ Convex Action begins
  │   ├─ ctx.runMutation(api.messages.send)
  │   │   └─ Saves user message to DB → Frontend reactively shows it
  │   │
  │   ├─ ctx.runQuery(api.channels.get) → verify channel
  │   ├─ ctx.runQuery(api.agents.list) → get all agents
  │   │
  │   ├─ Determine responding agents:
  │   │   ├─ Boss always (group chat keyword match)
  │   │   └─ Engineer matches "build" keyword → included
  │   │
  │   ├─ For Boss:
  │   │   ├─ ctx.runMutation(api.agents.setStatus, "working")
  │   │   ├─ Generate simulated response: "Building something new..."
  │   │   ├─ Sleep 300ms (realism)
  │   │   ├─ ctx.runMutation(api.messages.sendAgentMessage)
  │   │   │   └─ Boss's message saved → Frontend reactively shows it
  │   │   └─ ctx.runMutation(api.agents.setStatus, "idle")
  │   │
  │   └─ For Engineer:
  │       ├─ ctx.runMutation(api.agents.setStatus, "working")
  │       ├─ Generate: "Let me design the architecture..."
  │       ├─ Sleep 300ms
  │       ├─ ctx.runMutation(api.messages.sendAgentMessage)
  │       └─ ctx.runMutation(api.agents.setStatus, "idle")
  │
  └─ Action returns → Frontend receives acknowledgment
```

---

## 10. File Inventory

### Backend — Convex (10 files)
```
src/convex/
├── schema.ts              # 14 tables, enums, indexes
├── projects.ts            # Project CRUD + members
├── agents.ts              # Agent CRUD + default 5 agents setup
├── tasks.ts               # Task CRUD + status workflow
├── channels.ts            # Channel CRUD + default setup
├── messages.ts            # Message CRUD + agent messages
├── notifications.ts       # Notification CRUD
├── llm.ts                 # OpenAI/Anthropic integration
├── agentOrchestration.ts  # Agent response pipeline (simulated)
├── executionLogs.ts       # Observability logging
├── auth.ts                # Auth helpers (pre-existing)
├── auth.config.ts         # Auth config (pre-existing)
├── http.ts                # HTTP actions (pre-existing)
├── users.ts               # User queries (pre-existing)
├── auth/                  # Auth providers
│   └── emailOtp.ts        # Email OTP provider
└── _generated/            # Auto-generated types
```

### Frontend — Pages (4 files)
```
src/pages/
├── Chat.tsx           # Discord-style chat interface
├── Dashboard.tsx       # Project dashboard
├── Auth.tsx            # Auth page (pre-existing)
├── Landing.tsx         # Marketing page (replaced as root, kept for reference)
└── NotFound.tsx        # 404 page (pre-existing)
```

### Frontend — Components (3 files)
```
src/components/chat/
├── ChannelSidebar.tsx   # Discord sidebar with server bar + channels + agents
├── MessageList.tsx      # Message display with avatars + date separators
└── MessageInput.tsx     # Message input with @mentions
```

### Frontend — Hooks & Lib
```
src/hooks/
├── use-auth.ts          # Auth hook (pre-existing)
└── use-mobile.ts        # Mobile detection (pre-existing)

src/lib/
├── utils.ts             # Utility functions (pre-existing)
└── vly-integrations.ts  # Vly integrations (pre-existing)
```

### Config Files
```
/ (root)
├── package.json           # Dependencies & scripts
├── .env                   # VITE_CONVEX_URL + Vly config
├── tsconfig.json          # TypeScript config
├── vite.config.ts         # Vite config
├── index.html             # Entry HTML
├── src/index.css          # Theme variables + Tailwind directives
├── src/main.tsx           # App entry + routing
└── CONTEXT.md             # This file
```

---

## 11. To Do / Future Work

### Short Term
- [x] **OmniRoute LLM Integration**: Added OmniRoute as a provider in `src/convex/llm.ts` with `OMNIROUTE_API_KEY`, `OMNIROUTE_BASE_URL`, `OMNIROUTE_DEFAULT_MODEL` env vars. `agentOrchestration.ts` now uses real LLM when `OMNIROUTE_API_KEY` is set, falling back to simulated responses otherwise.
- [ ] **Convex Env Setup**: Run `npx convex env set OMNIROUTE_API_KEY "your-key"` to enable real LLM responses in the deployed Convex backend.
- [ ] **Preview Fix**: App may not render in Freebuff preview due to Convex auth initialization — may need to check browser console errors
- [ ] **Typing Indicators**: Show which agent is currently "working" (animated dots in message area)

### Medium Term
- [ ] **All Agents Respond**: Make each agent respond independently based on @mentions, not just the Boss routing
- [ ] **Mobile Responsive**: ChannelSidebar should be a slide-over drawer with hamburger toggle
- [ ] **Message Threads**: Reply threads for focused discussions
- [ ] **Code Syntax Highlighting**: Proper syntax highlighting for code blocks in messages

### Longer Term (AIOS Spec)
- [ ] **Project Management UI**: Full project CRUD from the dashboard
- [ ] **Task Board**: Kanban-style task management
- [ ] **Memory System**: Vector embeddings + RAG for long-term agent memory
- [ ] **Knowledge Graph**: Visual graph of project knowledge
- [ ] **Tool System**: Browser, code execution, file analysis, GitHub integrations
- [ ] **Human Approval Gates**: UI for approving/rejecting agent actions
- [ ] **Observability Dashboard**: Real-time cost, token, latency tracking
- [ ] **Multi-Project Support**: Switch between projects
- [ ] **Agent Evolution**: Boss creates/merges/splits agents dynamically
