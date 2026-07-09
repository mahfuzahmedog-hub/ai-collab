import { v } from "convex/values";
import { mutation, query } from "./_generated/server";
import { getCurrentUser } from "./users";
import { TASK_STATUS } from "./schema";

// ─── Queries ─────────────────────────────────────────────────────────────────

export const list = query({
  args: { projectId: v.id("projects") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("tasks")
      .withIndex("project", (q) => q.eq("projectId", args.projectId))
      .order("desc")
      .collect();
  },
});

export const get = query({
  args: { taskId: v.id("tasks") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.taskId);
  },
});

export const listByStatus = query({
  args: { projectId: v.id("projects"), status: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("tasks")
      .withIndex("project", (q) => q.eq("projectId", args.projectId))
      .filter((q) => q.eq(q.field("status"), args.status))
      .collect();
  },
});

export const listByAgent = query({
  args: { agentId: v.id("agents") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("tasks")
      .withIndex("agent", (q) => q.eq("assignedAgentId", args.agentId))
      .order("desc")
      .collect();
  },
});

export const listByUser = query({
  args: {},
  handler: async (ctx) => {
    const user = await getCurrentUser(ctx);
    if (!user) return [];
    return await ctx.db
      .query("tasks")
      .withIndex("assignee", (q) => q.eq("assignedUserId", user._id))
      .order("desc")
      .collect();
  },
});

// ─── Mutations ───────────────────────────────────────────────────────────────

export const create = mutation({
  args: {
    projectId: v.id("projects"),
    title: v.string(),
    description: v.optional(v.string()),
    priority: v.union(v.literal("low"), v.literal("medium"), v.literal("high"), v.literal("critical")),
    assignedAgentId: v.optional(v.id("agents")),
    assignedUserId: v.optional(v.id("users")),
    parentTaskId: v.optional(v.id("tasks")),
    dependencies: v.optional(v.array(v.id("tasks"))),
    deadline: v.optional(v.number()),
    tags: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const taskId = await ctx.db.insert("tasks", {
      projectId: args.projectId,
      title: args.title,
      description: args.description,
      status: TASK_STATUS.PENDING,
      priority: args.priority,
      assignedAgentId: args.assignedAgentId,
      assignedUserId: args.assignedUserId,
      parentTaskId: args.parentTaskId,
      dependencies: args.dependencies,
      createdBy: user._id,
      createdAt: Date.now(),
      deadline: args.deadline,
      tags: args.tags,
    });

    return taskId;
  },
});

export const update = mutation({
  args: {
    taskId: v.id("tasks"),
    title: v.optional(v.string()),
    description: v.optional(v.string()),
    status: v.optional(v.union(
      v.literal("pending"),
      v.literal("in_progress"),
      v.literal("in_review"),
      v.literal("completed"),
      v.literal("failed"),
      v.literal("blocked"),
      v.literal("cancelled"),
    )),
    priority: v.optional(v.union(v.literal("low"), v.literal("medium"), v.literal("high"), v.literal("critical"))),
    assignedAgentId: v.optional(v.id("agents")),
    result: v.optional(v.string()),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const patch: Record<string, unknown> = {};
    if (args.title !== undefined) patch.title = args.title;
    if (args.description !== undefined) patch.description = args.description;
    if (args.status !== undefined) {
      patch.status = args.status;
      if (args.status === TASK_STATUS.IN_PROGRESS) patch.startedAt = Date.now();
      if (args.status === TASK_STATUS.COMPLETED || args.status === TASK_STATUS.FAILED || args.status === TASK_STATUS.CANCELLED) {
        patch.completedAt = Date.now();
      }
    }
    if (args.priority !== undefined) patch.priority = args.priority;
    if (args.assignedAgentId !== undefined) patch.assignedAgentId = args.assignedAgentId;
    if (args.result !== undefined) patch.result = args.result;
    if (args.metadata !== undefined) patch.metadata = args.metadata;

    await ctx.db.patch(args.taskId, patch);
  },
});

export const remove = mutation({
  args: { taskId: v.id("tasks") },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");
    await ctx.db.delete(args.taskId);
  },
});
