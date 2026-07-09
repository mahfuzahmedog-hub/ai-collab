import { v } from "convex/values";
import { action } from "./_generated/server";
import { getCurrentUser } from "./users";
import { api } from "./_generated/api";

// ─── LLM Provider Configuration ──────────────────────────────────────────────

const PROVIDERS: Record<string, { baseUrl: string; defaultModel: string }> = {
  openai: {
    baseUrl: "https://api.openai.com/v1",
    defaultModel: "gpt-4o",
  },
  anthropic: {
    baseUrl: "https://api.anthropic.com/v1",
    defaultModel: "claude-3-5-sonnet-20241022",
  },
  omniroute: {
    baseUrl: "http://localhost:20128/v1",
    defaultModel: "auto",
  },
};

interface LLMMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

// ─── Send a message to an LLM and get a response ─────────────────────────────

export const chat = action({
  args: {
    messages: v.array(
      v.object({
        role: v.union(v.literal("system"), v.literal("user"), v.literal("assistant")),
        content: v.string(),
      }),
    ),
    model: v.optional(v.string()),
    provider: v.optional(v.union(v.literal("openai"), v.literal("anthropic"), v.literal("omniroute"))),
    temperature: v.optional(v.number()),
    maxTokens: v.optional(v.number()),
  },
  handler: async (ctx, args): Promise<string> => {
    const providerName = args.provider ?? "openai";
    const provider = PROVIDERS[providerName];
    if (!provider) {
      return `Unknown provider: ${providerName}`;
    }

    const apiKey = providerName === "omniroute" 
      ? process.env.OMNIROUTE_API_KEY 
      : providerName === "anthropic"
        ? process.env.ANTHROPIC_API_KEY
        : process.env.OPENAI_API_KEY;

    if (!apiKey) {
      return `I'm sorry, I don't have an API key configured for ${providerName}. Please add the API key to use this feature.`;
    }

    const model = args.model ?? provider.defaultModel;

    try {
      const response = await fetch(`${provider.baseUrl}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({
          model,
          messages: args.messages,
          temperature: args.temperature ?? 0.7,
          max_tokens: args.maxTokens ?? 2048,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("LLM API error:", response.status, errorText);
        return `I encountered an error: ${response.status}. Please check your API key and try again.`;
      }

      const data = await response.json();
      return data.choices?.[0]?.message?.content ?? "No response generated.";
    } catch (error) {
      console.error("LLM action error:", error);
      return "I'm sorry, I encountered an error while processing your request. Please try again.";
    }
  },
});

// ─── Generate an agent's response in a chat context ──────────────────────────

export const generateAgentResponse = action({
  args: {
    agentId: v.id("agents"),
    projectId: v.id("projects"),
    channelId: v.id("channels"),
    userMessage: v.string(),
    conversationHistory: v.array(
      v.object({
        role: v.union(v.literal("user"), v.literal("assistant"), v.literal("system")),
        content: v.string(),
        name: v.optional(v.string()),
      }),
    ),
    provider: v.optional(v.union(v.literal("openai"), v.literal("anthropic"), v.literal("omniroute"))),
  },
  handler: async (ctx, args): Promise<string> => {
    const agent = await ctx.runQuery(api.agents.get, { agentId: args.agentId });
    if (!agent) return "Agent not found.";

    // Build the system prompt
    const systemPrompt = agent.systemPrompt ?? "You are a helpful AI agent.";
    const agentContext = `You are ${agent.name}, a ${agent.type} agent in a multi-agent collaboration platform. 
Your capabilities include: ${(agent.capabilities ?? []).join(", ")}.
Respond naturally in English to the user's message in the group chat.
Keep your responses clear and conversational.`;

    const messages: LLMMessage[] = [
      { role: "system", content: `${systemPrompt}\n\n${agentContext}` },
      ...args.conversationHistory.map((m) => ({
        role: m.role as "user" | "assistant" | "system",
        content: `${m.name ? `${m.name}: ` : ""}${m.content}`,
      })),
      { role: "user", content: args.userMessage },
    ];

    const response = await ctx.runAction(api.llm.chat, {
      messages,
      model: agent.llmModel ?? "gpt-4o",
      provider: args.provider,
      temperature: agent.temperature ?? 0.7,
      maxTokens: agent.maxTokens ?? 1024,
    });

    // Log the execution
    await ctx.runMutation(api.executionLogs.log, {
      projectId: args.projectId,
      agentId: args.agentId,
      action: "chat_response",
      status: "completed",
      input: { userMessage: args.userMessage },
      output: { response },
      model: agent.llmModel ?? "gpt-4o",
    });

    return response;
  },
});
