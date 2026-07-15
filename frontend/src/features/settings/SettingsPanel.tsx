"use client";
import { AnimatePresence, motion } from "framer-motion";
import { useStore } from "@/store";
import { useState, useEffect } from "react";
import { X, Key, Check, AlertCircle } from "lucide-react";

const LS_KEY = "zen_api_key";

export function SettingsPanel() {
  const open = useStore((s) => s.settingsPanelOpen);
  const close = () => useStore.getState().setSettingsPanelOpen(false);
  const zenConnected = useStore((s) => s.zenConnected);
  const setZenConnected = useStore((s) => s.setZenConnected);
  const setZenApiKey = useStore((s) => s.setZenApiKey);
  const zenApiKey = useStore((s) => s.zenApiKey);
  const [input, setInput] = useState(zenApiKey || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem(LS_KEY);
    if (saved) {
      setInput(saved);
      connect(saved);
    }
  }, []);

  const connect = async (key: string) => {
    setError("");
    setSaving(true);
    try {
      const res = await fetch("/api/v1/settings/llm-key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: key }),
      });
      const data = await res.json();
      if (data.success) {
        setZenConnected(true);
        setZenApiKey(key);
        localStorage.setItem(LS_KEY, key);
      } else {
        setError("Connection failed");
        setZenConnected(false);
      }
    } catch {
      setError("Cannot reach backend");
      setZenConnected(false);
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = () => {
    if (!input.trim()) return;
    connect(input.trim());
  };

  const handleDisconnect = () => {
    setZenConnected(false);
    setZenApiKey(null);
    localStorage.removeItem(LS_KEY);
    setInput("");
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex justify-end"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute inset-0 bg-black/50" onClick={close} />
          <motion.aside
            className="relative w-full max-w-sm h-full bg-dark-900 border-l border-dark-700 shadow-2xl flex flex-col"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "tween", duration: 0.25 }}
          >
            <div className="flex items-center justify-between p-4 border-b border-dark-700">
              <div className="flex items-center gap-2">
                <Key size={18} className="text-primary-400" />
                <span className="text-white font-semibold">LLM Settings</span>
              </div>
              <button onClick={close} className="text-dark-400 hover:text-white transition-colors">
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              <div className="bg-dark-800 rounded-md p-3 flex items-center gap-2 text-sm">
                <span className={`w-2 h-2 rounded-full ${zenConnected ? "bg-green-500" : "bg-red-500"}`} />
                <span className="text-dark-300">{zenConnected ? "Connected to Zen API" : "Not connected"}</span>
              </div>

              <div>
                <label className="text-xs uppercase tracking-wide text-dark-500 mb-1 block">Zen API Key</label>
                <input
                  type="password"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                  placeholder="sk-zen-..."
                  className="w-full bg-dark-800 border border-dark-600 rounded px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-primary-500"
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 text-xs text-red-400 bg-red-900/20 rounded px-3 py-2">
                  <AlertCircle size={14} /> {error}
                </div>
              )}

              {zenConnected && (
                <div className="flex items-center gap-2 text-xs text-green-400 bg-green-900/20 rounded px-3 py-2">
                  <Check size={14} /> Connected &mdash; LLM requests use Zen API
                </div>
              )}

              <div className="text-xs text-dark-500 space-y-1">
                <p>Paste your Zen API key from any account. Comma-separate multiple keys for quota rotation.</p>
                <p>Key is saved in your browser and auto-connected on reload.</p>
              </div>
            </div>

            <div className="p-4 border-t border-dark-700 flex flex-col gap-2">
              {zenConnected ? (
                <button
                  onClick={handleDisconnect}
                  className="w-full flex items-center justify-center gap-2 bg-red-600 hover:bg-red-500 text-white rounded-md py-2 text-sm font-medium transition-colors"
                >
                  Disconnect
                </button>
              ) : (
                <button
                  onClick={handleSubmit}
                  disabled={saving || !input.trim()}
                  className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white rounded-md py-2 text-sm font-medium transition-colors"
                >
                  {saving ? "Connecting..." : "Connect"}
                </button>
              )}
            </div>
          </motion.aside>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
