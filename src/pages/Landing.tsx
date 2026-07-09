import { motion } from "framer-motion";
import { useRef } from "react";
import { useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Bot,
  MessageCircle,
  Brain,
  Shield,
  ArrowRight,
  Github,
  Twitter,
  Star,
  ChevronDown,
  Workflow,
  BarChart3,
  Sparkles,
} from "lucide-react";

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: "easeOut" as const },
  },
};

export default function Landing() {
  const navigate = useNavigate();
  const heroRef = useRef<HTMLDivElement>(null);

  const features = [
    {
      icon: Bot,
      title: "Multi-Agent Teams",
      description: "Create teams of specialized AI agents — Boss, Engineer, Researcher, Reviewer — that collaborate autonomously.",
      color: "from-purple-500 to-blue-500",
    },
    {
      icon: MessageCircle,
      title: "Discord-Style Chat",
      description: "Group chat where all agents communicate in plain English. DM any agent privately. Thread discussions for clarity.",
      color: "from-blue-500 to-cyan-500",
    },
    {
      icon: Brain,
      title: "Long-Term Memory",
      description: "Agents remember past conversations, decisions, and project context. Vector memory and knowledge graphs for deep recall.",
      color: "from-pink-500 to-rose-500",
    },
    {
      icon: Workflow,
      title: "Smart Orchestration",
      description: "The Boss Agent plans, delegates, supervises, and evaluates. Dynamic team formation for every unique task.",
      color: "from-amber-500 to-orange-500",
    },
    {
      icon: Shield,
      title: "Approval Gates",
      description: "Human-in-the-loop for sensitive actions. Reviewer agents validate quality, security, and accuracy before completion.",
      color: "from-green-500 to-emerald-500",
    },
    {
      icon: BarChart3,
      title: "Real-Time Observability",
      description: "Track costs, token usage, latency, and agent activity. Full execution graphs with replay and debugging.",
      color: "from-indigo-500 to-violet-500",
    },
  ];

  const agents = [
    { emoji: "👑", name: "Boss", role: "Orchestrator" },
    { emoji: "🔍", name: "Researcher", role: "Information" },
    { emoji: "⚙️", name: "Engineer", role: "Builder" },
    { emoji: "✅", name: "Reviewer", role: "QA" },
    { emoji: "✍️", name: "Writer", role: "Documentation" },
  ];

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Nav */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="fixed top-0 left-0 right-0 z-50 h-14 border-b bg-background/80 backdrop-blur-xl"
      >
        <div className="max-w-7xl mx-auto px-4 h-full flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
              <Bot className="h-4 w-4 text-white" />
            </div>
            <span className="font-bold text-sm">AIOS</span>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" className="text-xs h-8" onClick={() => navigate("/chat")}>
              Launch Chat
            </Button>
            <Button
              size="sm"
              className="text-xs h-8 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white shadow-lg shadow-purple-500/20"
              onClick={() => navigate("/chat")}
            >
              Get Started
              <ArrowRight className="ml-1.5 h-3 w-3" />
            </Button>
          </div>
        </div>
      </motion.header>

      {/* Hero */}
      <section ref={heroRef} className="relative pt-24 pb-20 md:pt-32 md:pb-28 overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-br from-purple-500/5 via-transparent to-blue-500/5 rounded-full blur-2xl" />
        </div>

        <div className="max-w-5xl mx-auto px-4 text-center relative">
          <motion.div variants={itemVariants} initial="hidden" animate="visible" className="mb-6">
            <Badge variant="outline" className="h-7 px-3 text-xs gap-1.5 border-purple-500/20 bg-purple-500/5 text-purple-500">
              <Sparkles className="h-3 w-3" />
              Autonomous Multi-Agent AI Platform
            </Badge>
          </motion.div>

          <motion.h1 variants={itemVariants} initial="hidden" animate="visible" className="text-4xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
            An Operating System for
            <br />
            <span className="bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
              AI Collaboration
            </span>
          </motion.h1>

          <motion.p variants={itemVariants} initial="hidden" animate="visible" className="text-base md:text-lg text-muted-foreground max-w-2xl mx-auto mb-8 leading-relaxed">
            Describe any goal in natural language. AIOS assembles a team of specialist agents,
            plans the work, executes collaboratively, and delivers results — all while you
            watch and chat in real-time.
          </motion.p>

          <motion.div variants={itemVariants} initial="hidden" animate="visible" className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-12">
            <Button
              size="lg"
              className="h-12 px-8 text-sm bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white shadow-xl shadow-purple-500/20 transition-all duration-300 hover:shadow-2xl hover:shadow-purple-500/30 hover:scale-105"
              onClick={() => navigate("/chat")}
            >
              Start Collaborating
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="h-12 px-8 text-sm"
              onClick={() => document.getElementById("features")?.scrollIntoView({ behavior: "smooth" })}
            >
              Learn More
              <ChevronDown className="ml-2 h-4 w-4" />
            </Button>
          </motion.div>

          <motion.div variants={itemVariants} initial="hidden" animate="visible" className="flex items-center justify-center gap-2 md:gap-3 flex-wrap">
            {agents.map((agent, i) => (
              <motion.div
                key={agent.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + i * 0.1 }}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full border bg-card/50 backdrop-blur-sm text-sm hover:bg-card/80 transition-colors cursor-default"
              >
                <span className="text-base">{agent.emoji}</span>
                <span className="text-xs text-muted-foreground">{agent.role}</span>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 md:py-28 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-muted/30 to-transparent pointer-events-none" />
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need for
              <br />
              <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                AI Team Collaboration
              </span>
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              From task planning to execution, AIOS provides the complete toolkit.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ delay: i * 0.1 }}
                className="group relative p-6 rounded-2xl border bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 hover:shadow-lg cursor-default"
              >
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
                <div className="relative">
                  <div className={`h-10 w-10 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 shadow-lg`}>
                    <feature.icon className="h-5 w-5 text-white" />
                  </div>
                  <h3 className="font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 md:py-28 bg-muted/20">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">How It Works</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">From idea to execution in four simple steps.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { step: "1", title: "Describe Your Goal", desc: "Tell AIOS what you want to build in natural language." },
              { step: "2", title: "Team Assembles", desc: "The Boss Agent creates the optimal team of specialist agents for your task." },
              { step: "3", title: "Collaborate & Monitor", desc: "Watch agents work in the group chat. DM any agent. Provide feedback." },
              { step: "4", title: "Results Delivered", desc: "Reviewer agents validate quality. You approve. Done." },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ delay: i * 0.1 }}
                className="text-center"
              >
                <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-purple-500/20">
                  <span className="text-white font-bold text-lg">{item.step}</span>
                </div>
                <h3 className="font-semibold mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed px-2">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 md:py-28 relative">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-blue-500/5 pointer-events-none" />
        <div className="max-w-3xl mx-auto px-4 text-center">
          <div className="p-8 md:p-12 rounded-3xl border bg-card/50 backdrop-blur-sm relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-blue-500 to-cyan-500" />
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to Build with AI?</h2>
            <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
              Start collaborating with your AI agent team today. No setup required.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Button
                size="lg"
                className="h-12 px-8 text-sm bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white shadow-xl shadow-purple-500/20 transition-all duration-300 hover:shadow-2xl hover:scale-105"
                onClick={() => navigate("/chat")}
              >
                Get Started Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              <Button variant="outline" size="lg" className="h-12 px-8 text-sm gap-2" onClick={() => navigate("/chat")}>
                <Star className="h-4 w-4" />
                Launch Chat
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-md bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
              <Bot className="h-3 w-3 text-white" />
            </div>
            <span className="text-sm font-semibold">AIOS</span>
            <span className="text-xs text-muted-foreground">&copy; 2026</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <a href="#" className="hover:text-foreground transition-colors">Terms</a>
            <a href="#" className="hover:text-foreground transition-colors">Privacy</a>
            <a href="#" className="hover:text-foreground transition-colors">Docs</a>
            <a href="#" className="hover:text-foreground transition-colors">GitHub</a>
          </div>
          <div className="flex items-center gap-2">
            <a href="#" className="h-8 w-8 rounded-lg border flex items-center justify-center hover:bg-accent transition-colors">
              <Github className="h-4 w-4" />
            </a>
            <a href="#" className="h-8 w-8 rounded-lg border flex items-center justify-center hover:bg-accent transition-colors">
              <Twitter className="h-4 w-4" />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
