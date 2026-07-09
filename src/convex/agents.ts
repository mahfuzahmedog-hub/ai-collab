import { v } from "convex/values";
import { mutation, query } from "./_generated/server";
import { getCurrentUser } from "./users";
import { AGENT_STATUS, AGENT_TYPE } from "./schema";

// ─── Queries ─────────────────────────────────────────────────────────────────

export const list = query({
  args: { projectId: v.id("projects") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("agents")
      .withIndex("project", (q) => q.eq("projectId", args.projectId))
      .order("desc")
      .collect();
  },
});

export const get = query({
  args: { agentId: v.id("agents") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.agentId);
  },
});

export const getBossAgent = query({
  args: { projectId: v.id("projects") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("agents")
      .withIndex("project", (q) => q.eq("projectId", args.projectId))
      .filter((q) => q.eq(q.field("type"), AGENT_TYPE.BOSS))
      .first();
  },
});

export const getByParent = query({
  args: { parentAgentId: v.id("agents") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("agents")
      .withIndex("parent", (q) => q.eq("parentAgentId", args.parentAgentId))
      .collect();
  },
});

// ─── Mutations ───────────────────────────────────────────────────────────────

export const create = mutation({
  args: {
    projectId: v.id("projects"),
    name: v.string(),
    type: v.union(v.literal("boss"), v.literal("worker"), v.literal("reviewer"), v.literal("specialist")),
    emoji: v.optional(v.string()),
    description: v.optional(v.string()),
    systemPrompt: v.optional(v.string()),
    capabilities: v.optional(v.array(v.string())),
    parentAgentId: v.optional(v.id("agents")),
    llmModel: v.optional(v.string()),
    temperature: v.optional(v.number()),
    maxTokens: v.optional(v.number()),
    color: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const membership = await ctx.db
      .query("projectMembers")
      .withIndex("project_user", (q) =>
        q.eq("projectId", args.projectId).eq("userId", user._id),
      )
      .first();
    if (!membership) throw new Error("Not a project member");

    const agentId = await ctx.db.insert("agents", {
      projectId: args.projectId,
      name: args.name,
      type: args.type,
      status: AGENT_STATUS.IDLE,
      emoji: args.emoji,
      description: args.description,
      systemPrompt: args.systemPrompt,
      capabilities: args.capabilities,
      parentAgentId: args.parentAgentId,
      llmModel: args.llmModel,
      temperature: args.temperature,
      maxTokens: args.maxTokens,
      color: args.color,
      createdAt: Date.now(),
    });

    return agentId;
  },
});

export const update = mutation({
  args: {
    agentId: v.id("agents"),
    name: v.optional(v.string()),
    status: v.optional(v.union(v.literal("idle"), v.literal("working"), v.literal("reviewing"), v.literal("blocked"), v.literal("error"), v.literal("retired"))),
    description: v.optional(v.string()),
    systemPrompt: v.optional(v.string()),
    capabilities: v.optional(v.array(v.string())),
    emoji: v.optional(v.string()),
    color: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const patch: Record<string, unknown> = {};
    if (args.name !== undefined) patch.name = args.name;
    if (args.status !== undefined) patch.status = args.status;
    if (args.description !== undefined) patch.description = args.description;
    if (args.systemPrompt !== undefined) patch.systemPrompt = args.systemPrompt;
    if (args.capabilities !== undefined) patch.capabilities = args.capabilities;
    if (args.emoji !== undefined) patch.emoji = args.emoji;
    if (args.color !== undefined) patch.color = args.color;

    await ctx.db.patch(args.agentId, patch);
  },
});

export const remove = mutation({
  args: { agentId: v.id("agents") },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const agent = await ctx.db.get(args.agentId);
    if (!agent) throw new Error("Agent not found");

    const membership = await ctx.db
      .query("projectMembers")
      .withIndex("project_user", (q) =>
        q.eq("projectId", agent.projectId).eq("userId", user._id),
      )
      .first();
    if (!membership || membership.role !== "admin") {
      throw new Error("Not authorized");
    }

    await ctx.db.patch(args.agentId, { status: AGENT_STATUS.RETIRED, retiredAt: Date.now() });
  },
});

export const setStatus = mutation({
  args: {
    agentId: v.id("agents"),
    status: v.union(v.literal("idle"), v.literal("working"), v.literal("reviewing"), v.literal("blocked"), v.literal("error"), v.literal("retired")),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.agentId, { status: args.status });
  },
});

// ─── Boss Agent: Setup default agents for a project ─────────────────────────

export const setupDefaultAgents = mutation({
  args: { projectId: v.id("projects") },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    // Define default specialist agents (using string literals for union types)
    type AgentDef = {
      name: string;
      type: string;
      emoji: string;
      color: string;
      description: string;
      systemPrompt: string;
      capabilities: string[];
      llmModel: string;
    };

    const defaultAgents: AgentDef[] = [
      {
        name: "Boss",
        type: "boss",
        emoji: "👑",
        color: "#8B5CF6",
        description: "Orchestrates the team, delegates tasks, and ensures project goals are met.",
        systemPrompt: "You are the Boss Agent. You plan work, create specialist agents, delegate tasks, supervise execution, evaluate quality, and deliver results. You communicate clearly with the user and your team.",
        capabilities: ["planning", "delegation", "supervision", "quality-control", "reporting"],
        llmModel: "gpt-4o",
      },
      {
        name: "Researcher",
        type: "specialist",
        emoji: "🔍",
        color: "#3B82F6",
        description: "Researches topics, gathers information, and provides insights from web searches and documents.",
        systemPrompt: "You are the Researcher Agent. You gather information, analyze data, and provide well-sourced insights to help the team make informed decisions.",
        capabilities: ["web-search", "data-analysis", "fact-checking", "summarization"],
        llmModel: "gpt-4o",
      },
      {
        name: "Engineer",
        type: "specialist",
        emoji: "⚙️",
        color: "#10B981",
        description: "Builds, codes, and implements technical solutions with precision and best practices.",
        systemPrompt: "You are the Engineer Agent. You write clean, maintainable code, implement features, fix bugs, and follow engineering best practices. You explain technical decisions clearly.",
        capabilities: ["coding", "architecture", "code-review", "debugging", "testing"],
        llmModel: "gpt-4o",
      },
      {
        name: "Reviewer",
        type: "reviewer",
        emoji: "✅",
        color: "#F59E0B",
        description: "Reviews work for quality, security, requirements compliance, and factual accuracy.",
        systemPrompt: "You are the Reviewer Agent. You validate factual accuracy, requirements compliance, security, and quality before work is marked complete. You provide constructive feedback.",
        capabilities: ["qa", "security-audit", "requirements-validation", "fact-checking"],
        llmModel: "gpt-4o",
      },
      {
        name: "Writer",
        type: "specialist",
        emoji: "✍️",
        color: "#EC4899",
        description: "Creates documentation, reports, and written content with clarity and style.",
        systemPrompt: "You are the Writer Agent. You create clear, engaging documentation, reports, and written content. You adapt your tone to the audience and ensure everything is well-structured.",
        capabilities: ["documentation", "content-creation", "editing", "formatting"],
        llmModel: "gpt-4o",
      },
    ];

    const createdIds: string[] = [];

    for (const agent of defaultAgents) {
      const id = await ctx.db.insert("agents", {
        projectId: args.projectId,
        name: agent.name,
        type: agent.type as "boss" | "worker" | "reviewer" | "specialist",
        status: AGENT_STATUS.IDLE,
        emoji: agent.emoji,
        description: agent.description,
        systemPrompt: agent.systemPrompt,
        capabilities: agent.capabilities,
        llmModel: agent.llmModel,
        color: agent.color,
        createdAt: Date.now(),
      });
      createdIds.push(id);
    }

    return createdIds;
  },
});
