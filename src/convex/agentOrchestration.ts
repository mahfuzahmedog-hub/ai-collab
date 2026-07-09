import { v } from "convex/values";
import { action } from "./_generated/server";
import { api } from "./_generated/api";
import { Doc, Id } from "./_generated/dataModel";

// ─── Simulated Response Engine ──────────────────────────────────────────────
// Generates contextual responses based on agent persona + message content.
// Swap in a real LLM call later (e.g. api.llm.generateAgentResponse).

type AgentInfo = {
  _id: string;
  name: string;
  type: string;
  emoji?: string;
  description?: string;
  capabilities?: string[];
};

const BOSS_RESPONSES = [
  "Great question! Let me think about the best approach here. I'll have the team look into this.",
  "I've analyzed your request. Here's what I think we should do — let me break it down into tasks.",
  "Excellent! This is right up our alley. I'm assigning some specialist agents to work on this.",
  "Got it. Let me coordinate with the team and get everyone aligned on this goal.",
  "Perfect. I'll task the relevant agents and we'll get started right away.",
  "Good thinking. Let me delegate this to the right specialists — they'll chime in shortly.",
  "I see what you're after. Here's my plan of attack for tackling this efficiently.",
  "Interesting challenge! Let's break this into smaller pieces and tackle each one systematically.",
];

const RESEARCHER_RESPONSES = [
  "I've done some initial research on this topic. Here's what I found — there are some excellent resources and best practices we can follow.",
  "Great topic! Let me pull together some key insights and data points that will help guide our approach.",
  "I've been looking into this. The current landscape suggests a few different approaches we could take.",
  "Based on my research, I'd recommend we look at these key areas — there's strong precedent for this approach.",
  "Quick research summary: I found several high-quality references that will inform our strategy here.",
];

const ENGINEER_RESPONSES = [
  "I've thought about the technical architecture. Here's what I'd suggest for the implementation.",
  "Good call on the technical approach. Let me outline how we can build this efficiently.",
  "From an engineering standpoint, I recommend we follow these patterns — they'll keep the code clean and maintainable.",
  "I've done some preliminary design thinking. The architecture should be modular and scalable.",
  "Technically speaking, this is straightforward. Let me draft the implementation plan.",
  "Great engineering challenge! I'd suggest we use a component-based approach with clear separation of concerns.",
];

const REVIEWER_RESPONSES = [
  "I'll keep an eye on quality assurance for this. We should establish some validation criteria upfront.",
  "Good — I'll make sure we have proper quality gates in place before we mark anything complete.",
  "From a quality perspective, I recommend we set up some automated checks to validate the output.",
  "I'll review the work as it comes in and make sure we're meeting our standards.",
  "Let me think about what could go wrong... Here are some edge cases we should consider.",
];

const WRITER_RESPONSES = [
  "Once we have the details sorted, I can document everything clearly. We'll want good docs for this.",
  "I'll be ready to write up the documentation and any supporting content we need.",
  "Good — I'll make sure we have clear, well-structured documentation for whatever we build.",
  "I can help structure the output, create guides, and make sure everything's well documented.",
  "Let me start drafting an outline for the documentation structure we'll want.",
];

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function generateSimulatedResponse(
  agent: AgentInfo,
  userMessage: string,
  agentResponses: string[],
): string {
  const msg = userMessage.toLowerCase();
  const agentName = agent.name;
  let response = pick(agentResponses);

  // Add contextual flavor based on keywords
  if (msg.includes("hello") || msg.includes("hi ") || msg.includes("hey") || msg.includes("👋")) {
    response = `Hey there! 👋 Great to have you here. What would you like to build today?`;
  } else if (msg.includes("thank")) {
    response = `You're welcome! Happy to help. Let me know what else you need.`;
  } else if (msg.includes("help") || msg.includes("can you")) {
    response = `Of course! I'm here to help. Let me look into this and get back to you with a solid plan.`;
  } else if (msg.includes("bug") || msg.includes("fix") || msg.includes("issue")) {
    if (agent.type === "engineer" || agent.type === "specialist" && agentName === "Engineer") {
      response = `Let me investigate that bug. I'll trace through the code and find the root cause.`;
    } else if (agent.type === "reviewer") {
      response = `I'll help validate the fix and make sure we've covered all the edge cases.`;
    } else {
      response = `A bug? No problem. I'll assign our Engineer to investigate and fix it.`;
    }
  } else if (msg.includes("code") || msg.includes("build") || msg.includes("implement")) {
    if (agentName === "Engineer") {
      response = `Let me design the architecture and write the implementation. Here's my approach...`;
    } else {
      response = `Building something new — fantastic! I'll coordinate with the Engineer to get this implemented.`;
    }
  } else if (msg.includes("research") || msg.includes("search") || msg.includes("find") || msg.includes("look up")) {
    if (agentName === "Researcher") {
      response = `On it! Let me gather the latest information and insights on this topic.`;
    } else {
      response = `Good idea to research this first. ${agentName === "Boss" ? "Let me task our Researcher with this." : "I'll dig into this and report back."}`;
    }
  } else if (msg.includes("write") || msg.includes("doc") || msg.includes("document")) {
    if (agentName === "Writer") {
      response = `I'll start drafting the documentation. I'll make it clear and well-structured.`;
    } else {
      response = `Great — we'll need good documentation for this. Let's get the Writer involved.`;
    }
  } else if (msg.includes("review") || msg.includes("check") || msg.includes("validate")) {
    if (agentName === "Reviewer") {
      response = `I'll review everything carefully — checking for quality, accuracy, and completeness.`;
    } else {
      response = `Smart to get a review. Let's make sure our Reviewer looks this over.`;
    }
  } else if (msg.includes("plan") || msg.includes("strategy") || msg.includes("approach")) {
    if (agentName === "Boss") {
      response = `Let me put together a comprehensive strategy. I'll involve the right specialists.`;
    } else {
      response = `Good strategic thinking. I'll contribute my analysis to the planning process.`;
    }
  } else if (msg.includes("test") || msg.includes("deploy") || msg.includes("release")) {
    if (agentName === "Engineer") {
      response = `I'll prepare everything for deployment — testing, building, and making sure it's release-ready.`;
    } else if (agentName === "Reviewer") {
      response = `I'll do a final quality check before we deploy. Let's make sure everything is solid.`;
    } else {
      response = `Let's get this ready for release. I'll coordinate testing and the deployment pipeline.`;
    }
  } else if (msg.includes("idea") || msg.includes("suggest") || msg.includes("what if")) {
    response = `Interesting idea! Let me think about this... Here are my initial thoughts on how we could approach it.`;
  }

  // Add agent-specific personality
  if (agentName === "Boss") {
    response += `\n\nWhat do you think? I can adjust the plan if you have a different direction in mind.`;
  } else if (agentName === "Researcher") {
    response += `\n\nI can dive deeper into any specific area if you'd like more detail.`;
  } else if (agentName === "Engineer") {
    response += `\n\nLet me know if you want me to start coding this up.`;
  } else if (agentName === "Reviewer") {
    response += `\n\nI'll keep track of quality as we go — just let me know when there's something to review.`;
  } else if (agentName === "Writer") {
    response += `\n\nLet me know when the details are finalized and I'll get the docs written up.`;
  }

  return response;
}

function shouldAgentRespond(
  agent: AgentInfo,
  userMessage: string,
): boolean {
  const msg = userMessage.toLowerCase();
  const name = agent.name;

  // Boss always responds
  if (name === "Boss") return true;

  // Check for @mentions
  if (msg.includes(`@${name.toLowerCase()}`)) return true;

  // Check for keyword matches to the agent's specialty
  switch (name) {
    case "Researcher":
      return /research|search|find|look up|investigate|data|information|insight|learn|study|analyze/i.test(msg);
    case "Engineer":
      return /code|build|implement|develop|architect|fix|bug|technical|engineer|program|function|component|api|database|design pattern|refactor/i.test(msg);
    case "Reviewer":
      return /review|check|validate|quality|security|test|audit|verify|approve|ensure/i.test(msg);
    case "Writer":
      return /write|doc|document|readme|guide|manual|explain|describe|content|article|readme|tutorial|blog/i.test(msg);
    default:
      return false;
  }
}

// ─── Process User Message ───────────────────────────────────────────────────

export const processUserMessage = action({
  args: {
    channelId: v.id("channels"),
    projectId: v.id("projects"),
    content: v.string(),
    contentType: v.optional(
      v.union(v.literal("text"), v.literal("code")),
    ),
  },
  handler: async (ctx, args): Promise<string> => {
    // 1. Save the user's message
    const messageId = await ctx.runMutation(api.messages.send, {
      channelId: args.channelId,
      projectId: args.projectId,
      content: args.content,
      contentType: args.contentType ?? "text",
    });

    // 2. Get the channel and all agents
    const channel = await ctx.runQuery(api.channels.get, {
      channelId: args.channelId,
    });
    if (!channel) return messageId;

    const allAgents = await ctx.runQuery(api.agents.list, {
      projectId: args.projectId,
    });
    if (!allAgents || allAgents.length === 0) return messageId;

    const activeAgents = allAgents.filter((a: any) => a.status !== "retired") as AgentInfo[];

    // 3. Determine which agents should respond
    let respondingAgents: AgentInfo[] = [];

    if (channel.type === "direct") {
      // Direct message — only the specific agent responds
      const target = activeAgents.find((a) =>
        channel.agentIds.includes(a._id as Id<"agents">),
      );
      if (target) respondingAgents = [target];
    } else {
      // Group chat — Boss always responds, and specialists chime in based on keywords
      const boss = activeAgents.find((a) => a.type === "boss");
      if (boss) respondingAgents.push(boss);

      const specialistResponses = activeAgents.filter(
        (a) => a.type !== "boss" && shouldAgentRespond(a, args.content),
      );
      respondingAgents.push(...specialistResponses);

      // Limit to max 3 agents responding to avoid spam
      if (respondingAgents.length > 3) {
        respondingAgents = [respondingAgents[0], ...respondingAgents.slice(1, 3)];
      }
    }

    if (respondingAgents.length === 0) return messageId;

    // 4. Get response templates per agent
    const responseMap: Record<string, string[]> = {
      Boss: BOSS_RESPONSES,
      Researcher: RESEARCHER_RESPONSES,
      Engineer: ENGINEER_RESPONSES,
      Reviewer: REVIEWER_RESPONSES,
      Writer: WRITER_RESPONSES,
    };

    // 5. Send responses sequentially with realistic delays
    for (let i = 0; i < respondingAgents.length; i++) {
      const agent = respondingAgents[i];

      // Mark agent as working
      await ctx.runMutation(api.agents.setStatus, {
        agentId: agent._id as any,
        status: "working",
      });

      // Generate response
      const templates = responseMap[agent.name] ?? BOSS_RESPONSES;
      const response = generateSimulatedResponse(agent, args.content, templates);

      // Small delay so responses feel realistic (300ms between agents)
      await sleep(300);

      // Post the response
      await ctx.runMutation(api.messages.sendAgentMessage, {
        channelId: args.channelId,
        projectId: args.projectId,
        agentId: agent._id as any,
        content: response,
        contentType: "text",
      });

      // Mark agent as idle
      await ctx.runMutation(api.agents.setStatus, {
        agentId: agent._id as any,
        status: "idle",
      });
    }

    return messageId;
  },
});

// ─── Send Welcome Message ────────────────────────────────────────────────────

export const sendWelcomeMessage = action({
  args: {
    channelId: v.id("channels"),
    projectId: v.id("projects"),
  },
  handler: async (ctx, args) => {
    const bossAgent = await ctx.runQuery(api.agents.getBossAgent, {
      projectId: args.projectId,
    });
    if (!bossAgent) return;

    const welcomeMessage = `👋 **Hey there! I'm the Boss Agent.** I'm here to orchestrate your AI team.

I've assembled a few specialist agents to help you:
• 🔍 **Researcher** — Researches topics and gathers data
• ⚙️ **Engineer** — Writes code and builds things
• ✅ **Reviewer** — Checks quality and catches issues
• ✍️ **Writer** — Creates docs and written content

**Just tell me what you'd like to work on** and I'll coordinate the team. Or @mention any agent to chat with them directly.

What should we build today? 🚀`;

    await ctx.runMutation(api.messages.sendAgentMessage, {
      channelId: args.channelId,
      projectId: args.projectId,
      agentId: bossAgent._id,
      content: welcomeMessage,
      contentType: "text",
    });
  },
});
