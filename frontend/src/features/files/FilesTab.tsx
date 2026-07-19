"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, File, Folder, FolderOpen } from "lucide-react";
import { clsx } from "clsx";
import { useStore } from "@/store";
import { FileViewer } from "@/features/files/FileViewer";
import { sendCreateFile } from "@/lib/websocket";
import type { FileNode } from "@/types";

function FileTreeNode({
  node,
  depth,
  selectedFile,
  onSelect,
}: {
  node: FileNode;
  depth: number;
  selectedFile: string | null;
  onSelect: (path: string) => void;
}) {
  const isDir = node.type === "directory";
  const [expanded, setExpanded] = useState(depth === 0);
  const pad = { paddingLeft: 8 + depth * 12 };

  if (!isDir) {
    const active = selectedFile === node.path;
    return (
      <button
        onClick={() => onSelect(node.path)}
        style={pad}
        className={clsx(
          "flex w-full items-center gap-1.5 py-1 pr-2 text-left text-xs",
          active ? "bg-dark-800 text-white" : "text-dark-300 hover:bg-dark-800/50 hover:text-white"
        )}
      >
        <File className="h-3.5 w-3.5 shrink-0" />
        <span className="truncate">{node.name}</span>
      </button>
    );
  }

  const children = node.children ?? [];
  return (
    <div>
      <button
        onClick={() => setExpanded((v) => !v)}
        style={pad}
        className="flex w-full items-center gap-1 py-1 pr-2 text-left text-xs text-dark-300 hover:text-white"
      >
        {expanded ? <ChevronDown className="h-3 w-3 shrink-0" /> : <ChevronRight className="h-3 w-3 shrink-0" />}
        {expanded ? <FolderOpen className="h-3.5 w-3.5 shrink-0" /> : <Folder className="h-3.5 w-3.5 shrink-0" />}
        <span className="truncate">{node.name}</span>
      </button>
      {expanded &&
        children.map((child) => (
          <FileTreeNode
            key={child.path}
            node={child}
            depth={depth + 1}
            selectedFile={selectedFile}
            onSelect={onSelect}
          />
        ))}
    </div>
  );
}

export function FilesTab() {
  const files = useStore((s) => s.files);
  const selectedFile = useStore((s) => s.selectedFile);
  const setSelectedFile = useStore((s) => s.setSelectedFile);
  const [newFileName, setNewFileName] = useState("");
  const [showNewFile, setShowNewFile] = useState(false);

  function handleCreateFile() {
    const name = newFileName.trim();
    if (!name) return;
    sendCreateFile(name);
    setNewFileName("");
    setShowNewFile(false);
  }

  return (
    <div className="flex h-full bg-dark-950">
      <div className="flex w-64 min-w-[16rem] flex-col border-r border-dark-700 bg-dark-900">
        <div className="flex items-center justify-between border-b border-dark-700 px-3 py-2">
          <span className="text-xs font-semibold text-white">Files</span>
          <button onClick={() => setShowNewFile(true)} className="text-dark-400 hover:text-white text-xs" title="New file">+</button>
        </div>
        <div className="flex-1 overflow-y-auto py-1">
          {showNewFile && (
            <div className="px-3 py-1">
              <input autoFocus value={newFileName} onChange={e => setNewFileName(e.target.value)} onKeyDown={e => { if (e.key === "Enter") handleCreateFile(); if (e.key === "Escape") setShowNewFile(false); }} placeholder="filename.md" className="w-full bg-dark-800 border border-dark-600 rounded px-2 py-1 text-xs text-white placeholder-dark-500 outline-none" />
            </div>
          )}
          {files.length === 0 ? (
            <p className="p-4 text-xs text-dark-500">
              No files yet. Agents will create files here as they work.
            </p>
          ) : (
            files.map((node) => (
              <FileTreeNode
                key={node.path}
                node={node}
                depth={0}
                selectedFile={selectedFile}
                onSelect={setSelectedFile}
              />
            ))
          )}
        </div>
      </div>
      <div className="flex-1 overflow-hidden">
        <FileViewer />
      </div>
    </div>
  );
}
