import { v } from "convex/values";
import { mutation, query } from "./_generated/server";
import { getCurrentUser } from "./users";

// ─── Queries ─────────────────────────────────────────────────────────────────

export const list = query({
  args: {},
  handler: async (ctx) => {
    const user = await getCurrentUser(ctx);
    if (!user) return [];

    return await ctx.db
      .query("notifications")
      .withIndex("user_time", (q) => q.eq("userId", user._id))
      .order("desc")
      .take(50);
  },
});

export const unreadCount = query({
  args: {},
  handler: async (ctx) => {
    const user = await getCurrentUser(ctx);
    if (!user) return 0;

    const notifications = await ctx.db
      .query("notifications")
      .withIndex("read", (q) =>
        q.eq("userId", user._id).eq("read", false),
      )
      .collect();

    return notifications.length;
  },
});

// ─── Mutations ───────────────────────────────────────────────────────────────

export const create = mutation({
  args: {
    userId: v.id("users"),
    projectId: v.optional(v.id("projects")),
    type: v.union(v.literal("mention"), v.literal("task"), v.literal("approval"), v.literal("message"), v.literal("system")),
    title: v.string(),
    body: v.string(),
    link: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    await ctx.db.insert("notifications", {
      userId: args.userId,
      projectId: args.projectId,
      type: args.type,
      title: args.title,
      body: args.body,
      read: false,
      link: args.link,
      createdAt: Date.now(),
    });
  },
});

export const markRead = mutation({
  args: { notificationId: v.id("notifications") },
  handler: async (ctx, args) => {
    const notif = await ctx.db.get(args.notificationId);
    if (notif) {
      await ctx.db.patch(args.notificationId, { read: true });
    }
  },
});

export const markAllRead = mutation({
  args: {},
  handler: async (ctx) => {
    const user = await getCurrentUser(ctx);
    if (!user) return;

    const unread = await ctx.db
      .query("notifications")
      .withIndex("read", (q) =>
        q.eq("userId", user._id).eq("read", false),
      )
      .collect();

    await Promise.all(
      unread.map((n) => ctx.db.patch(n._id, { read: true })),
    );
  },
});
