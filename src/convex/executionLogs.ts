import { v } from "convex/values";
import { mutation } from "./_generated/server";

export const log = mutation({
  args: {
    projectId: v.id("projects"),
    agentId: v.id("agents"),
    action: v.string(),
    status: v.union(v.literal("started"), v.literal("completed"), v.literal("failed")),
    taskId: v.optional(v.id("tasks")),
    input: v.optional(v.any()),
    output: v.optional(v.any()),
    tokensUsed: v.optional(v.number()),
    costUsd: v.optional(v.number()),
    latencyMs: v.optional(v.number()),
    model: v.optional(v.string()),
    error: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    await ctx.db.insert("executionLogs", {
      projectId: args.projectId,
      agentId: args.agentId,
      action: args.action,
      status: args.status,
      taskId: args.taskId,
      input: args.input,
      output: args.output,
      tokensUsed: args.tokensUsed,
      costUsd: args.costUsd,
      latencyMs: args.latencyMs,
      model: args.model,
      error: args.error,
      createdAt: args.status === "started" ? now : now,
      completedAt: args.status !== "started" ? now : undefined,
    });
  },
});
