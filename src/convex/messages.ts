import { v } from "convex/values";
import { mutation, query } from "./_generated/server";
import { getCurrentUser } from "./users";

// ─── Queries ─────────────────────────────────────────────────────────────────

export const list = query({
  args: { channelId: v.id("channels"), limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 50;
    return await ctx.db
      .query("messages")
      .withIndex("channel_time", (q) => q.eq("channelId", args.channelId))
      .order("desc")
      .take(limit);
  },
});

export const get = query({
  args: { messageId: v.id("messages") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.messageId);
  },
});

export const listBySender = query({
  args: { senderId: v.id("users") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("messages")
      .withIndex("sender", (q) => q.eq("senderId", args.senderId))
      .order("desc")
      .take(50);
  },
});

export const listByAgent = query({
  args: { agentId: v.id("agents"), limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 50;
    return await ctx.db
      .query("messages")
      .withIndex("agent", (q) => q.eq("agentId", args.agentId))
      .order("desc")
      .take(limit);
  },
});

// ─── Mutations ───────────────────────────────────────────────────────────────

export const send = mutation({
  args: {
    channelId: v.id("channels"),
    projectId: v.id("projects"),
    content: v.string(),
    contentType: v.optional(v.union(v.literal("text"), v.literal("code"), v.literal("image"), v.literal("file"), v.literal("system"))),
    mentions: v.optional(v.array(v.id("agents"))),
    parentMessageId: v.optional(v.id("messages")),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const now = Date.now();

    const messageId = await ctx.db.insert("messages", {
      channelId: args.channelId,
      projectId: args.projectId,
      senderId: user._id,
      senderName: user.name ?? "Anonymous",
      senderType: "user",
      content: args.content,
      contentType: args.contentType ?? "text",
      mentions: args.mentions,
      parentMessageId: args.parentMessageId,
      createdAt: now,
    });

    // Update channel's last activity
    await ctx.db.patch(args.channelId, { lastActivityAt: now });

    return messageId;
  },
});

export const sendAgentMessage = mutation({
  args: {
    channelId: v.id("channels"),
    projectId: v.id("projects"),
    agentId: v.id("agents"),
    content: v.string(),
    contentType: v.optional(v.union(v.literal("text"), v.literal("code"), v.literal("image"), v.literal("file"), v.literal("system"))),
    parentMessageId: v.optional(v.id("messages")),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    const agent = await ctx.db.get(args.agentId);
    if (!agent) throw new Error("Agent not found");

    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const now = Date.now();

    const messageId = await ctx.db.insert("messages", {
      channelId: args.channelId,
      projectId: args.projectId,
      senderId: user._id,
      senderName: agent.name,
      senderType: "agent",
      agentId: args.agentId,
      content: args.content,
      contentType: args.contentType ?? "text",
      parentMessageId: args.parentMessageId,
      createdAt: now,
    });

    // Update channel's last activity
    await ctx.db.patch(args.channelId, { lastActivityAt: now });

    return messageId;
  },
});

export const edit = mutation({
  args: {
    messageId: v.id("messages"),
    content: v.string(),
  },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const message = await ctx.db.get(args.messageId);
    if (!message || message.senderId !== user._id) {
      throw new Error("Not authorized");
    }

    await ctx.db.patch(args.messageId, {
      content: args.content,
      editedAt: Date.now(),
    });
  },
});

export const remove = mutation({
  args: { messageId: v.id("messages") },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const message = await ctx.db.get(args.messageId);
    if (!message || message.senderId !== user._id) {
      throw new Error("Not authorized");
    }

    await ctx.db.delete(args.messageId);
  },
});
