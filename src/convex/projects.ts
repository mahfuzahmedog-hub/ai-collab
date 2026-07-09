import { v } from "convex/values";
import { mutation, query } from "./_generated/server";
import { getCurrentUser } from "./users";
import { ROLES } from "./schema";

// ─── Queries ─────────────────────────────────────────────────────────────────

export const list = query({
  args: {},
  handler: async (ctx) => {
    const user = await getCurrentUser(ctx);
    if (!user) return [];

    const memberships = await ctx.db
      .query("projectMembers")
      .withIndex("user", (q) => q.eq("userId", user._id))
      .collect();

    const projectIds = memberships.map((m) => m.projectId);
    const projects = await Promise.all(
      projectIds.map((id) => ctx.db.get(id)),
    );
    return projects.filter((p) => p !== null);
  },
});

export const get = query({
  args: { projectId: v.id("projects") },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) return null;

    const membership = await ctx.db
      .query("projectMembers")
      .withIndex("project_user", (q) =>
        q.eq("projectId", args.projectId).eq("userId", user._id),
      )
      .first();

    if (!membership) return null;

    return await ctx.db.get(args.projectId);
  },
});

// ─── Mutations ───────────────────────────────────────────────────────────────

export const create = mutation({
  args: {
    name: v.string(),
    description: v.optional(v.string()),
    goal: v.optional(v.string()),
    tags: v.optional(v.array(v.string())),
  },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const projectId = await ctx.db.insert("projects", {
      name: args.name,
      description: args.description,
      goal: args.goal,
      ownerId: user._id,
      status: "active",
      tags: args.tags,
    });

    // Add creator as admin member
    await ctx.db.insert("projectMembers", {
      projectId,
      userId: user._id,
      role: ROLES.ADMIN,
      joinedAt: Date.now(),
    });

    return projectId;
  },
});

export const update = mutation({
  args: {
    projectId: v.id("projects"),
    name: v.optional(v.string()),
    description: v.optional(v.string()),
    goal: v.optional(v.string()),
    status: v.optional(v.union(v.literal("active"), v.literal("archived"), v.literal("completed"))),
    tags: v.optional(v.array(v.string())),
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

    if (!membership || membership.role !== ROLES.ADMIN) {
      throw new Error("Not authorized");
    }

    const patch: Record<string, unknown> = {};
    if (args.name !== undefined) patch.name = args.name;
    if (args.description !== undefined) patch.description = args.description;
    if (args.goal !== undefined) patch.goal = args.goal;
    if (args.status !== undefined) patch.status = args.status;
    if (args.tags !== undefined) patch.tags = args.tags;

    await ctx.db.patch(args.projectId, patch);
  },
});

export const remove = mutation({
  args: { projectId: v.id("projects") },
  handler: async (ctx, args) => {
    const user = await getCurrentUser(ctx);
    if (!user) throw new Error("Not authenticated");

    const membership = await ctx.db
      .query("projectMembers")
      .withIndex("project_user", (q) =>
        q.eq("projectId", args.projectId).eq("userId", user._id),
      )
      .first();

    if (!membership || membership.role !== ROLES.ADMIN) {
      throw new Error("Not authorized");
    }

    await ctx.db.delete(args.projectId);
  },
});

// ─── Members ─────────────────────────────────────────────────────────────────

export const addMember = mutation({
  args: {
    projectId: v.id("projects"),
    userId: v.id("users"),
    role: v.union(v.literal("admin"), v.literal("user"), v.literal("member")),
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

    if (!membership || membership.role !== ROLES.ADMIN) {
      throw new Error("Not authorized");
    }

    await ctx.db.insert("projectMembers", {
      projectId: args.projectId,
      userId: args.userId,
      role: args.role,
      joinedAt: Date.now(),
    });
  },
});

export const listMembers = query({
  args: { projectId: v.id("projects") },
  handler: async (ctx, args) => {
    const memberships = await ctx.db
      .query("projectMembers")
      .withIndex("project", (q) => q.eq("projectId", args.projectId))
      .collect();

    const users = await Promise.all(
      memberships.map((m) => ctx.db.get(m.userId)),
    );

    return memberships.map((m, i) => ({
      ...m,
      user: users[i],
    }));
  },
});
