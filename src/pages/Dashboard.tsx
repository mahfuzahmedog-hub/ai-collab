import { useQuery } from "convex/react";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/convex/_generated/api";
import { Id } from "@/convex/_generated/dataModel";
import { motion } from "framer-motion";
import { LogoDropdown } from "@/components/LogoDropdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Bot,
  MessageCircle,
  CheckCircle2,
  Clock,
  AlertCircle,
  TrendingUp,
  Users,
  ListTodo,
  Plus,
  Loader2,
  ArrowRight,
  Activity,
  Zap,
  BarChart3,
} from "lucide-react";
import { useNavigate } from "react-router";

export default function DashboardPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const projects = useQuery(api.projects.list);
  const activeProject = projects?.[0];
  const agents = useQuery(
    api.agents.list,
    activeProject ? { projectId: activeProject._id as Id<"projects"> } : "skip",
  );
  const tasks = useQuery(
    api.tasks.list,
    activeProject ? { projectId: activeProject._id as Id<"projects"> } : "skip",
  );
  const channels = useQuery(
    api.channels.list,
    activeProject ? { projectId: activeProject._id as Id<"projects"> } : "skip",
  );

  const isLoading = authLoading || (projects === undefined);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const statusCounts = {
    idle: agents?.filter((a: any) => a.status === "idle").length ?? 0,
    working: agents?.filter((a: any) => a.status === "working").length ?? 0,
    reviewing: agents?.filter((a: any) => a.status === "reviewing").length ?? 0,
    error: agents?.filter((a: any) => a.status === "error").length ?? 0,
  };

  const taskCounts = {
    pending: tasks?.filter((t: any) => t.status === "pending").length ?? 0,
    inProgress: tasks?.filter((t: any) => t.status === "in_progress").length ?? 0,
    inReview: tasks?.filter((t: any) => t.status === "in_review").length ?? 0,
    completed: tasks?.filter((t: any) => t.status === "completed").length ?? 0,
  };

  const statCards = [
    {
      title: "Active Agents",
      value: agents?.length ?? 0,
      icon: Bot,
      color: "text-purple-500",
      bg: "bg-purple-500/10",
      detail: `${statusCounts.working} working`,
    },
    {
      title: "Tasks",
      value: tasks?.length ?? 0,
      icon: ListTodo,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
      detail: `${taskCounts.completed} completed`,
    },
    {
      title: "In Progress",
      value: taskCounts.inProgress,
      icon: Clock,
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
      detail: `${taskCounts.pending} pending`,
    },
    {
      title: "Completed",
      value: taskCounts.completed,
      icon: CheckCircle2,
      color: "text-green-500",
      bg: "bg-green-500/10",
      detail: `${taskCounts.inReview} in review`,
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Top Bar */}
      <header className="h-12 border-b flex items-center justify-between px-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex items-center gap-3">
          <Bot className="h-5 w-5 text-primary" />
          <span className="font-semibold text-sm">AIOS Dashboard</span>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="h-8 gap-1.5 text-xs"
            onClick={() => navigate("/chat")}
          >
            <MessageCircle className="h-3.5 w-3.5" />
            Open Chat
          </Button>
          <LogoDropdown />
        </div>
      </header>

      <ScrollArea className="h-[calc(100vh-48px)]">
        <div className="p-6 max-w-7xl mx-auto space-y-6">
          {/* Welcome */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">
                  Welcome{user?.name ? `, ${user.name}` : " to AIOS"}
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Your AI Agent Operating System — manage projects, agents, and tasks.
                </p>
              </div>
              {activeProject && (
                <Badge variant="secondary" className="h-6 text-xs gap-1">
                  <Zap className="h-3 w-3" />
                  {activeProject.name}
                </Badge>
              )}
            </div>
          </motion.div>

          {/* Stats Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            {statCards.map((stat, i) => (
              <Card key={i} className="border-0 shadow-sm bg-card">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground font-medium">{stat.title}</p>
                      <p className="text-2xl font-bold">{stat.value}</p>
                      <p className="text-[10px] text-muted-foreground/60">{stat.detail}</p>
                    </div>
                    <div className={`p-2 rounded-lg ${stat.bg}`}>
                      <stat.icon className={`h-4 w-4 ${stat.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Agent Status */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.2 }}
              className="lg:col-span-2"
            >
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 text-primary" />
                      <CardTitle className="text-sm font-semibold">Agent Team</CardTitle>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs gap-1"
                      onClick={() => navigate("/chat")}
                    >
                      View all <ArrowRight className="h-3 w-3" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {agents?.length === 0 && (
                      <p className="text-sm text-muted-foreground/60 py-4 text-center">
                        No agents yet. Create a project to get started.
                      </p>
                    )}
                    {(agents ?? []).slice(0, 6).map((agent: any, i: number) => (
                      <div
                        key={agent._id}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                        onClick={() => navigate("/chat")}
                      >
                        <div className="relative">
                          <span className="text-xl">{agent.emoji ?? "🤖"}</span>
                          <span
                            className={`absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-background ${
                              agent.status === "idle" ? "bg-green-500" :
                              agent.status === "working" ? "bg-blue-500" :
                              agent.status === "reviewing" ? "bg-yellow-500" :
                              agent.status === "error" ? "bg-red-500" :
                              "bg-gray-400"
                            }`}
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate flex items-center gap-2">
                            {agent.name}
                            <Badge variant="outline" className="h-4 text-[9px] px-1 font-normal capitalize">
                              {agent.type}
                            </Badge>
                          </p>
                          <p className="text-xs text-muted-foreground/60 truncate">
                            {agent.description ?? "No description"}
                          </p>
                        </div>
                        <span className={`text-[10px] capitalize ${
                          agent.status === "idle" ? "text-green-500" :
                          agent.status === "working" ? "text-blue-500" :
                          agent.status === "reviewing" ? "text-yellow-500" :
                          "text-muted-foreground"
                        }`}>
                          {agent.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Right Column */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.3 }}
              className="space-y-4"
            >
              {/* Recent Tasks */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">
                    <ListTodo className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm font-semibold">Recent Tasks</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  {tasks?.length === 0 ? (
                    <p className="text-sm text-muted-foreground/60 py-4 text-center">
                      No tasks yet
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {(tasks ?? []).slice(0, 5).map((task: any) => (
                        <div key={task._id} className="flex items-center gap-2 text-sm">
                          <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                            task.status === "completed" ? "bg-green-500" :
                            task.status === "in_progress" ? "bg-blue-500" :
                            task.status === "failed" ? "bg-red-500" :
                            "bg-yellow-500"
                          }`} />
                          <span className="truncate text-muted-foreground/80">{task.title}</span>
                          <Badge variant="outline" className="h-4 text-[9px] px-1 ml-auto shrink-0 capitalize">
                            {task.status.replace("_", " ")}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card className="border-0 shadow-sm">
                <CardHeader className="pb-3">
                  <div className="flex items-center gap-2">
                    <Zap className="h-4 w-4 text-primary" />
                    <CardTitle className="text-sm font-semibold">Quick Actions</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <Button
                    variant="outline"
                    className="w-full justify-start h-9 text-xs gap-2"
                    onClick={() => navigate("/chat")}
                  >
                    <MessageCircle className="h-3.5 w-3.5" />
                    Open Team Chat
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start h-9 text-xs gap-2"
                    onClick={() => navigate("/chat")}
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Create New Task
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start h-9 text-xs gap-2"
                    onClick={() => navigate("/chat")}
                  >
                    <Activity className="h-3.5 w-3.5" />
                    View Activity Log
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
