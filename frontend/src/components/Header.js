import React, { useCallback } from "react";
import { Sun, Moon, Search, BarChart3, Clock, Network, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

export default function Header({ theme, toggleTheme, activeView, setActiveView, seedDatabase, isSeeded }) {
  const handleSeed = useCallback(async () => {
    try {
      toast.info("Seeding database with sample data...");
      const result = await seedDatabase();
      toast.success(result.message);
    } catch {
      toast.error("Failed to seed database");
    }
  }, [seedDatabase]);

  const navItems = [
    { id: "analyze", label: "Analyze", icon: Search },
    { id: "history", label: "History", icon: Clock },
    { id: "stats", label: "Stats", icon: BarChart3 },
    { id: "graph", label: "Graph", icon: Network },
  ];

  return (
    <header
      className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50"
      data-testid="app-header"
    >
      <div className="max-w-[1600px] mx-auto px-4 h-14 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-foreground flex items-center justify-center">
            <span className="text-background text-xs font-mono font-bold">FN</span>
          </div>
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground hidden sm:block">
            Fake News Detector
          </span>
        </div>

        {/* Nav */}
        <nav className="flex items-center gap-1" data-testid="main-nav">
          {navItems.map(({ id, label, icon: Icon }) => (
            <Button
              key={id}
              variant={activeView === id ? "default" : "ghost"}
              size="sm"
              className="rounded-sm font-mono text-xs uppercase tracking-wider h-8 px-3"
              onClick={() => setActiveView(id)}
              data-testid={`nav-${id}`}
            >
              <Icon className="w-3.5 h-3.5 mr-1.5" />
              <span className="hidden sm:inline">{label}</span>
            </Button>
          ))}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="rounded-sm font-mono text-xs uppercase tracking-wider h-8"
            onClick={handleSeed}
            data-testid="seed-button"
          >
            <Database className="w-3.5 h-3.5 mr-1.5" />
            <span className="hidden sm:inline">Seed Data</span>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="rounded-sm h-8 w-8"
            onClick={toggleTheme}
            data-testid="theme-toggle"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </Button>
        </div>
      </div>
    </header>
  );
}
