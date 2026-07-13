from __future__ import annotations
from app.tools.registry import ToolDefinition, tool_registry

_S = lambda d: {"type": "string", "description": d}
_N = lambda d: {"type": "number", "description": d}
_B = lambda d: {"type": "boolean", "description": d}
_A = lambda i: {"type": "array", "items": i}
_O = lambda p, r=None: {"type": "object", "properties": p, "required": r or list(p.keys())}

create_agent = ToolDefinition(
    name="create_agent",
    description="Create a new AI agent with a specific role, skills, and personality. The agent appears in the sidebar and can be messaged directly.",
    parameters=_O({
        "name": _S("Human-readable name for the agent"),
        "role": _S("Role: backend_engineer, frontend_engineer, researcher, designer, reviewer, qa_engineer, security, infra, manager, or custom"),
        "skills": _A(_S("Skill keyword")),
        "personality": _S("Personality description"),
        "display_name": _S("Display name (defaults to name)"),
        "mission": _S("One-sentence mission statement"),
        "channel": _S("Channel slug to post work in (default: general)"),
    }, ["name", "role"]),
)

evolve_agent = ToolDefinition(
    name="evolve_agent",
    description="Update an existing agent's skills, personality, mission, or channel.",
    parameters=_O({
        "agent_id": _S("ID of the agent to evolve"),
        "skills": _A(_S("New skill to add")),
        "personality": _S("Updated personality"),
        "mission": _S("Updated mission"),
        "channel": _S("Updated channel slug"),
    }, ["agent_id"]),
)

merge_agents = ToolDefinition(
    name="merge_agents",
    description="Merge two agents: the absorb agent's skills are absorbed into the keep agent, then absorb is retired.",
    parameters=_O({
        "keep_id": _S("ID of the agent to keep"),
        "absorb_id": _S("ID of the agent to absorb and retire"),
    }, ["keep_id", "absorb_id"]),
)

split_agent = ToolDefinition(
    name="split_agent",
    description="Create a new specialist agent from an existing agent's skills.",
    parameters=_O({
        "source_id": _S("ID of the source agent to split from"),
        "new_name": _S("Name for the new agent"),
        "new_role": _S("Role for the new agent"),
        "skills": _A(_S("Skills for the new agent")),
    }, ["source_id", "new_name"]),
)

retire_agent = ToolDefinition(
    name="retire_agent",
    description="Permanently retire an agent that is no longer needed.",
    parameters=_O({
        "agent_id": _S("ID of the agent to retire"),
    }, ["agent_id"]),
)

create_channel = ToolDefinition(
    name="create_channel",
    description="Create a new text channel or category in the workspace.",
    parameters=_O({
        "name": _S("Display name for the channel"),
        "channel_type": _S("Type: 'channel' for text, 'category' for a group header"),
        "sort_order": _N("Sort order (lower = first)"),
    }, ["name"]),
)

create_subchannel = ToolDefinition(
    name="create_subchannel",
    description="Create a sub-channel nested under a parent channel. parent_id is the parent's slug.",
    parameters=_O({
        "name": _S("Display name for the sub-channel"),
        "parent_id": _S("Slug of the parent channel (e.g. 'backend')"),
        "sort_order": _N("Sort order"),
    }, ["name", "parent_id"]),
)

rename_channel = ToolDefinition(
    name="rename_channel",
    description="Rename an existing channel by its slug.",
    parameters=_O({
        "id": _S("Channel slug to rename"),
        "name": _S("New display name"),
    }, ["id", "name"]),
)

move_channel = ToolDefinition(
    name="move_channel",
    description="Move a channel under a new parent. Omit parent_id to move to top level.",
    parameters=_O({
        "id": _S("Channel slug to move"),
        "parent_id": _S("New parent slug (omit to move to top level)"),
    }, ["id"]),
)

delete_channel = ToolDefinition(
    name="delete_channel",
    description="Delete a channel and all of its sub-channels.",
    parameters=_O({
        "channel": _S("Channel slug to delete"),
    }, ["channel"]),
)

create_thread = ToolDefinition(
    name="create_thread",
    description="Create a threaded discussion on a message.",
    parameters=_O({
        "channel": _S("Channel slug where the parent message is"),
        "parent_message_id": _S("ID of the parent message"),
        "title": _S("Thread title"),
    }, ["channel", "parent_message_id", "title"]),
)

register_tool = ToolDefinition(
    name="register_tool",
    description="Register an external tool that agents can discover and use.",
    parameters=_O({
        "name": _S("Tool name"),
        "description": _S("What the tool does"),
        "config": _O({"url": _S("API endpoint URL"), "auth": _S("Auth method")}),
    }, ["name", "description"]),
)

remove_tool = ToolDefinition(
    name="remove_tool",
    description="Remove a previously registered tool.",
    parameters=_O({
        "name": _S("Tool name to remove"),
    }, ["name"]),
)

create_knowledge_base = ToolDefinition(
    name="create_knowledge_base",
    description="Create a named knowledge base for storing documents and facts.",
    parameters=_O({
        "name": _S("Knowledge base name"),
    }, ["name"]),
)

remember_fact = ToolDefinition(
    name="remember_fact",
    description="Store a durable fact in the workspace memory.",
    parameters=_O({
        "key": _S("Fact key/name"),
        "value": _S("Fact value/description"),
    }, ["key", "value"]),
)

create_task = ToolDefinition(
    name="create_task",
    description="Create and optionally assign a task to an agent by role or name.",
    parameters=_O({
        "title": _S("Task title"),
        "description": _S("Detailed task description"),
        "priority": _S("Priority: low, medium, high, critical"),
        "assign_to": _S("Agent name or role to assign to"),
    }, ["title"]),
)

delegate_to_agent_tool = ToolDefinition(
    name="delegate_to_agent",
    description="Delegate a task to a specific agent by name or find the best match by skill.",
    parameters=_O({
        "name": _S("Agent name to delegate to (omit for auto-match)"),
        "task": _S("Task description"),
        "skills_needed": _A(_S("Skills the target agent should have")),
    }, ["task"]),
)

write_file = ToolDefinition(
    name="write_file",
    description="Write content to a file in the workspace.",
    parameters=_O({
        "path": _S("File path relative to workspace root"),
        "content": _S("File content"),
    }, ["path", "content"]),
)

read_file = ToolDefinition(
    name="read_file",
    description="Read the contents of a file from the workspace.",
    parameters=_O({
        "path": _S("File path relative to workspace root"),
    }, ["path"]),
)

list_files = ToolDefinition(
    name="list_files",
    description="List all files in the workspace.",
    parameters=_O({}),
)

http_get = ToolDefinition(
    name="http_get",
    description="Make an HTTP GET request to a URL.",
    parameters=_O({
        "url": _S("Target URL"),
    }, ["url"]),
)

http_post = ToolDefinition(
    name="http_post",
    description="Make an HTTP POST request to a URL.",
    parameters=_O({
        "url": _S("Target URL"),
    }, ["url"]),
)

http_put = ToolDefinition(
    name="http_put",
    description="Make an HTTP PUT request to a URL.",
    parameters=_O({
        "url": _S("Target URL"),
    }, ["url"]),
)

http_delete = ToolDefinition(
    name="http_delete",
    description="Make an HTTP DELETE request to a URL.",
    parameters=_O({
        "url": _S("Target URL"),
    }, ["url"]),
)

web_search = ToolDefinition(
    name="web_search",
    description="Search the web for information on a given query.",
    parameters=_O({
        "query": _S("Search query"),
        "num_results": _N("Number of results to return (default 5)"),
    }, ["query"]),
)

browse = ToolDefinition(
    name="browse",
    description="Navigate to a URL and retrieve its text content.",
    parameters=_O({
        "url": _S("URL to browse"),
    }, ["url"]),
)

screenshot = ToolDefinition(
    name="screenshot",
    description="Take a screenshot of a webpage at the given URL.",
    parameters=_O({
        "url": _S("URL to screenshot"),
    }, ["url"]),
)

run_python = ToolDefinition(
    name="run_python",
    description="Execute Python code and return the output.",
    parameters=_O({
        "code": _S("Python code to execute"),
    }, ["code"]),
)

run_shell = ToolDefinition(
    name="run_shell",
    description="Execute a shell command and return the output.",
    parameters=_O({
        "command": _S("Shell command to execute"),
    }, ["command"]),
)

get_repo = ToolDefinition(
    name="get_repo",
    description="Get information about a GitHub repository.",
    parameters=_O({
        "repo": _S("Repository name (e.g. 'owner/repo')"),
    }, ["repo"]),
)

search_repos = ToolDefinition(
    name="search_repos",
    description="Search GitHub repositories by query.",
    parameters=_O({
        "query": _S("Search query"),
    }, ["query"]),
)

get_file_content = ToolDefinition(
    name="get_file_content",
    description="Get the content of a file from a GitHub repository.",
    parameters=_O({
        "repo": _S("Repository name (e.g. 'owner/repo')"),
        "path": _S("File path in the repository"),
        "branch": _S("Branch name (default: main)"),
    }, ["repo", "path"]),
)

create_issue = ToolDefinition(
    name="create_issue",
    description="Create an issue on a GitHub repository.",
    parameters=_O({
        "repo": _S("Repository name (e.g. 'owner/repo')"),
        "title": _S("Issue title"),
        "body": _S("Issue body/description"),
    }, ["repo", "title"]),
)

forget_memory = ToolDefinition(
    name="forget_memory",
    description="Delete a specific memory by its ID.",
    parameters=_O({
        "mem_id": _S("Memory ID to delete"),
    }, ["mem_id"]),
)

search_memories_tool = ToolDefinition(
    name="search_memories",
    description="Search the memory store for relevant information.",
    parameters=_O({
        "query": _S("Search query"),
        "type_filter": _S("Optional memory type filter: fact, conversation, decision, code, user_preference, user_profile"),
    }, ["query"]),
)

create_skill = ToolDefinition(
    name="create_skill",
    description="Create a reusable skill from a completed workflow or task. The LLM will extract the pattern automatically.",
    parameters=_O({
        "name": _S("Short kebab-case name for the skill"),
        "description": _S("One-line summary of what the skill does"),
        "category": _S("Category: workflow, knowledge, template, or integration"),
        "prompt_template": _S("Instructions injected when this skill is triggered"),
        "trigger_phrases": _A(_S("Phrase that auto-activates this skill")),
    }, ["name", "description"]),
)

search_skills_tool = ToolDefinition(
    name="search_skills",
    description="Search available skills by keyword.",
    parameters=_O({
        "query": _S("Search query"),
        "category": _S("Optional category filter: workflow, knowledge, template, integration"),
    }, ["query"]),
)

list_skills_tool = ToolDefinition(
    name="list_skills",
    description="List all registered skills, optionally filtered by category.",
    parameters=_O({
        "category": _S("Optional category filter: workflow, knowledge, template, integration"),
    }),
)

delete_skill_tool = ToolDefinition(
    name="delete_skill",
    description="Delete a skill by its ID.",
    parameters=_O({
        "skill_id": _S("Skill ID to delete"),
    }, ["skill_id"]),
)

ALL_TOOLS = [
    create_agent, evolve_agent, merge_agents, split_agent, retire_agent,
    create_channel, create_subchannel, rename_channel, move_channel, delete_channel,
    create_thread,
    register_tool, remove_tool, create_knowledge_base, remember_fact, forget_memory, search_memories_tool,
    create_skill, search_skills_tool, list_skills_tool, delete_skill_tool,
    create_task, delegate_to_agent_tool,
    write_file, read_file, list_files,
    http_get, http_post, http_put, http_delete,
    web_search, browse, screenshot,
    run_python, run_shell,
    get_repo, search_repos, get_file_content, create_issue,
]


def register_all_schemas():
    for definition in ALL_TOOLS:
        tool_registry.register(definition)
