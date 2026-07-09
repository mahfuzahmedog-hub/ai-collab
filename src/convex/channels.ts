import { v } from "convex/values";
import { mutation, query } from "./_generated/server";
import { getCurrentUser } from "./users";
import { CHANNEL_TYPE } from "./schema";

// ─── Queries ─────────────────────────────────────────────────────────────────

export const list = query({
  args: { projectId: v.id("projects") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("channels")
      .withIndex("project", (q) => q.eq("projectId", args.projectId))
      .order("desc")
      .collect();
  },
});

export const get = query({
  args: { channelId: v.id("channels") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.channelId);
  },
});

export const getGroupChannel = query({
  args: { projectId: v.id("projects") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("channels")
      .withIndex("project", (q) => q.eq("projectId", args.projectId))
      .filter((q) =>
        q.and(
          q.eq(q.field("type"), CHANNEL_TYPE.GROUP),
          q.eq(q.field("isDefault"), true),
        ),
      )
      .first();
  },
});

export const getDirectChannel = query({
  args: { projectId: v.id("projects"), agentId: v.id("agents") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("channels")
      .withIndex("project", (q) => q.eq("projectId", args.projectId))
      .filter((q) =>
        q.and(
          q.eq(q.field("type"), CHANNEL_TYPE.DIRECT),
          q.eq(q.field("agentIds"), [args.agentId]),
        ),
      )
      .first();
  },
});

// ─── Mutations ───────────────────────────────────────────────────────────────

export const create = mutation({
  args: {
    projectId: v.id("projects"),
    name: v.string(),
    type: v.union(v.literal("group"), v.literal("direct"), v.literal("thread")),
    agentIds: v.array(v.id("agents")),
    participantUserIds: v.optional(v.array(v.id("users"))),
    parentChannelId: v.optional(v.id("channels")),
    isDefault: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const now = Date.now();

    const channelId = await ctx.db.insert("channels", {
      projectId: args.projectId,
      name: args.name,
      type: args.type,
      agentIds: args.agentIds,
      participantUserIds: args.participantUserIds ?? [user._id],
      parentChannelId: args.parentChannelId,
      isDefault: args.isDefault ?? false,
      createdAt: now,
      lastActivityAt: now,
    });

    return channelId;
  },
});

export const setupDefaultChannels = mutation({
  args: { projectId: v.id("projects"), agentIds: v.array(v.id("agents")) },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const now = Date.now();

    // Create the main group chat channel
    const groupChannelId = await ctx.db.insert("channels", {
      projectId: args.projectId,
      name: "general",
      type: CHANNEL_TYPE.GROUP,
      agentIds: args.agentIds,
      participantUserIds: [user._id],
      isDefault: true,
      createdAt: now,
      lastActivityAt: now,
    });

    // Create direct message channels for each agent
    const directChannelIds: Record<string, string> = {};
    for (const agentId of args.agentIds) {
      const directId = await ctx.db.insert("channels", {
        projectId: args.projectId,
        name: "direct",
        type: CHANNEL_TYPE.DIRECT,
        agentIds: [agentId],
        participantUserIds: [user._id],
        parentChannelId: groupChannelId,
        createdAt: now,
        lastActivityAt: now,
      });
      directChannelIds[agentId] = directId;
    }

    return { groupChannelId, directChannelIds };
  },
});

export const updateLastActivity = mutation({
  args: { channelId: v.id("channels") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.channelId, { lastActivityAt: Date.now() });
  },
});
