"use client";

import { useEffect } from "react";
import { FileText, Loader2 } from "lucide-react";
import { useStore } from "@/store";
import { sendReadFile } from "@/lib/websocket";

export function FileViewer() {
  const selectedFile = useStore((s) => s.selectedFile);
  const fileContents = useStore((s) => s.fileContents);

  const cached = selectedFile ? fileContents[selectedFile] : undefined;
  const hasContent = selectedFile != null && cached !== undefined;

  useEffect(() => {
    if (selectedFile && fileContents[selectedFile] === undefined) {
      sendReadFile(selectedFile);
    }
  }, [selectedFile, fileContents]);

  if (!selectedFile) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-dark-500 bg-dark-950">
        <FileText className="mb-2 h-8 w-8" />
        <p className="text-sm">Select a file to view</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-dark-950">
      <div className="flex items-center gap-2 border-b border-dark-700 px-3 py-2">
        <FileText className="h-4 w-4 text-dark-400" />
        <span className="truncate font-mono text-xs text-white">{selectedFile}</span>
      </div>
      {hasContent ? (
        <pre className="flex-1 overflow-auto whitespace-pre bg-dark-900 p-3 font-mono text-xs text-dark-300">
          {cached}
        </pre>
      ) : (
        <div className="flex flex-1 items-center justify-center text-dark-500">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          <span className="text-sm">Loading…</span>
        </div>
      )}
    </div>
  );
}
