"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import clsx from "clsx";

export function Markdown({ children }: { children: React.ReactNode }) {
  const content = typeof children === "string" ? children : "";
  return (
    <div className="text-sm text-dark-100 leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ node, ...props }) => (
            <p className="whitespace-normal my-1" {...props} />
          ),
          h1: ({ node, ...props }) => (
            <h1 className="text-lg font-bold text-white mt-2 mb-1" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-base font-bold text-white mt-2 mb-1" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-sm font-semibold text-white mt-2 mb-1" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc ml-4 my-1" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal ml-4 my-1" {...props} />
          ),
          a: ({ node, ...props }) => (
            <a
              className="text-primary-400 underline"
              target="_blank"
              rel="noreferrer"
              {...props}
            />
          ),
          code: ({ node, className, children, ...props }) => {
            const isBlock = /language-/.test(className || "");
            if (isBlock) {
              return (
                <pre className="bg-dark-800 rounded p-2 overflow-x-auto text-xs font-mono my-1">
                  <code className={clsx("text-dark-100", className)} {...props}>
                    {children}
                  </code>
                </pre>
              );
            }
            return (
              <code
                className="bg-dark-800 px-1 rounded text-dark-100 font-mono text-xs"
                {...props}
              >
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
