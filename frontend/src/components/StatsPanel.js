import React from "react";
import { BarChart3, Shield, AlertTriangle, Globe, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

function StatCard({ icon: Icon, label, value, sub }) {
  return (
    <div className="border border-border bg-card p-4 rounded-sm">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4 text-muted-foreground" />
        <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground">{label}</span>
      </div>
      <div className="font-mono text-3xl font-bold">{value}</div>
      {sub && <div className="font-mono text-[10px] text-muted-foreground mt-1">{sub}</div>}
    </div>
  );
}

export default function StatsPanel({ stats, graphData }) {
  if (!stats) {
    return (
      <div className="border border-dashed border-border bg-card/50 p-12 rounded-sm text-center" data-testid="stats-empty">
        <BarChart3 className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          Loading statistics...
        </p>
      </div>
    );
  }

  const nodeCounts = stats.node_counts || {};
  const verdictDist = stats.verdict_distribution || {};
  const suspiciousSources = stats.suspicious_sources || [];
  const totalNews = nodeCounts.News || 0;
  const totalRelationships = stats.total_relationships || 0;

  return (
    <div className="space-y-4" data-testid="stats-panel">
      {/* Overview cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Shield} label="Total Articles" value={totalNews} sub={`${totalRelationships} relationships`} />
        <StatCard icon={Globe} label="Sources" value={nodeCounts.Source || 0} />
        <StatCard icon={Users} label="Authors" value={nodeCounts.Author || 0} />
        <StatCard icon={AlertTriangle} label="Topics" value={nodeCounts.Topic || 0} />
      </div>

      {/* Verdict Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border border-border bg-card p-5 rounded-sm">
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground block mb-4">
            Verdict Distribution
          </span>
          <div className="space-y-3">
            {[
              { key: "LIKELY TRUE", color: "bg-blue-500", label: "Trustworthy" },
              { key: "SUSPICIOUS", color: "bg-yellow-500", label: "Suspicious" },
              { key: "LIKELY FAKE", color: "bg-red-500", label: "Likely Fake" },
            ].map(({ key, color, label }) => {
              const count = verdictDist[key] || 0;
              const pct = totalNews > 0 ? (count / totalNews) * 100 : 0;
              return (
                <div key={key} className="space-y-1" data-testid={`verdict-stat-${key.toLowerCase().replace(/\s/g, '-')}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{label}</span>
                    <span className="font-mono text-xs font-bold">{count} ({pct.toFixed(0)}%)</span>
                  </div>
                  <div className="w-full h-2 bg-muted rounded-none overflow-hidden">
                    <div className={`h-full ${color} transition-all`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Suspicious Sources */}
        <div className="border border-border bg-card p-5 rounded-sm">
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground block mb-4">
            Source Credibility
          </span>
          <div className="space-y-2">
            {suspiciousSources.length === 0 ? (
              <p className="text-xs text-muted-foreground">No source data available</p>
            ) : (
              suspiciousSources.map((s, i) => (
                <div
                  key={s.source}
                  className="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0"
                  data-testid={`source-stat-${i}`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-muted-foreground w-4">{i + 1}.</span>
                    <span className="text-sm">{s.source}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[10px] text-muted-foreground">
                      {s.fake_count}/{s.total} fake
                    </span>
                    <Badge
                      variant="outline"
                      className={`rounded-sm text-[10px] font-mono ${
                        s.fake_ratio > 0.5
                          ? "text-red-500 border-red-500/30"
                          : s.fake_ratio > 0.2
                          ? "text-yellow-500 border-yellow-500/30"
                          : "text-blue-500 border-blue-500/30"
                      }`}
                    >
                      {(s.fake_ratio * 100).toFixed(0)}%
                    </Badge>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Node type breakdown */}
      <div className="border border-border bg-card p-5 rounded-sm">
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground block mb-4">
          Graph Node Types
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {Object.entries(nodeCounts).map(([type, count]) => (
            <div key={type} className="text-center p-3 border border-border/50 rounded-sm">
              <div className="font-mono text-2xl font-bold">{count}</div>
              <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{type}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
