"use client";

import { useState } from "react";
import { useStore } from "@/store";
import { FileText, Folder, Bot, Loader2, Code } from "lucide-react";
import type { FileNode } from "@/types";

interface FileTreeProps {
  files: FileNode[];
}

function FileNodeComponent({ node, depth = 0, onSelect }: { node: FileNode; depth?: number; onSelect?: (path: string) => void }) {
  const isDir = node.type === "directory";
  const [expanded, setExpanded] = useState(isDir);

  if (!isDir) {
    return (
      <div className={`pl-${depth * 4} flex items-center gap-1 text-dark-300 text-xs hover:text-white cursor-pointer py-0.5`} onClick={() => onSelect?.(node.path)}>
        <FileText className="w-3 h-3" />
        <span className="truncate">{node.name}</span>
        {node.size && <span className="text-dark-500 ml-auto text-[10px]">{(node.size / 1024).toFixed(1)}KB</span>}
      </div>
    );
  }

  if (!node.children || node.children.length === 0) {
    return (
      <div className={`pl-${depth * 4} flex items-center gap-1 text-dark-400 text-xs`}>
        <Folder className="w-3 h-3" />
        <span>{node.name}</span>
      </div>
    );
  }

  return (
    <div className="pl-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className={`w-full pl-${depth * 4} flex items-center gap-1 text-dark-300 text-xs hover:text-white py-0.5`}
      >
        {expanded ? <span className="w-3">▼</span> : <span className="w-3">▶</span>}
        <Folder className="w-3 h-3" />
        <span>{node.name}</span>
      </button>
      {expanded && (
        <div className="mt-0.5">
          {node.children.map((child) => (
            <FileNodeComponent key={child.path} node={child} depth={depth + 1} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  );
}

function FileTree() {
  const files = useStore((s) => s.files);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  if (files.length === 0) {
    return (
      <div className="flex flex-col h-full">
        <div className="p-4 border-b border-dark-700">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <Code className="w-5 h-5" />
            Workspace
          </h3>
        </div>
        <div className="flex-1 flex items-center justify-center text-dark-500 text-sm p-4">
          No files yet. Agents will create files here as they work.
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-dark-900">
      <div className="p-4 border-b border-dark-700 flex items-center justify-between">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Code className="w-5 h-5" />
          Workspace ({files.length})
        </h3>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {files.map((file) => (
          <FileNodeComponent key={file.path} node={file} onSelect={(path) => setSelectedFile(path)} />
        ))}
      </div>
      {selectedFile && (
        <div className="p-3 border-t border-dark-700 bg-dark-800 text-xs text-dark-300">
          Selected: <span className="text-white font-mono truncate block">{selectedFile}</span>
        </div>
      )}
    </div>
  );
}

function AgentList() {
  const agents = useStore((s) => s.agents);

  if (agents.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-dark-500 text-sm p-4 border-t border-dark-700">
        No agents yet. Create a project to start.
      </div>
    );
  }

  const boss = agents.find((a) => a.role === "boss" || a.role === "coworker");
  const workers = agents.filter((a) => a.role !== "boss");

  return (
    <div className="flex-1 flex flex-col border-t border-dark-700 overflow-hidden">
      <div className="p-3 bg-dark-800 border-b border-dark-700">
        <h3 className="font-semibold text-white flex items-center gap-2">
          <Bot className="w-4 h-4" />
          Team ({workers.length})
        </h3>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {boss && (
          <div className="bg-primary-600/10 border border-primary-600/20 rounded-lg p-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold text-lg">
                {boss.name.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-white">{boss.name}</div>
                <div className="text-xs text-primary-400">Engineering Manager</div>
              </div>
              <div className={`w-2 h-2 rounded-full ${boss.status === "thinking" ? "bg-yellow-400 animate-pulse" : boss.status === "working" ? "bg-blue-400" : "bg-green-500"}`} />
            </div>
            {boss.status === "thinking" && <div className="mt-2 text-xs text-yellow-400">Thinking...</div>}
          </div>
        )}
        {workers.map((worker) => (
          <div key={worker.id} className="bg-dark-800/50 border border-dark-600 rounded-lg p-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-dark-700 flex items-center justify-center text-white text-xs font-bold">
                {worker.name.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-white truncate">{worker.name}</div>
                <div className="text-xs text-dark-400 capitalize">{worker.role.replace("_", " ")}</div>
              </div>
              <div className={`w-2 h-2 rounded-full ${worker.status === "working" ? "bg-blue-400" : worker.status === "thinking" ? "bg-yellow-400 animate-pulse" : worker.status === "blocked" ? "bg-red-500" : "bg-green-500"}`} />
            </div>
            {worker.current_task_id && (
              <div className="mt-2 text-xs text-dark-400 bg-dark-700 px-2 py-1 rounded">
                Working on: {worker.current_task_id}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export function AgentSidebar() {
  return (
    <aside className="w-72 flex-shrink-0 bg-dark-900 border-l border-dark-700 flex flex-col h-full">
      <FileTree />
      <AgentList />
    </aside>
  );
}