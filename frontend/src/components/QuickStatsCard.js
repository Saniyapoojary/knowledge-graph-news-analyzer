import React from "react";
import { BarChart3, ShieldCheck, ShieldAlert, AlertTriangle, Network } from "lucide-react";
import { Separator } from "@/components/ui/separator";

export default function QuickStatsCard({ stats }) {
  const nodeCounts = stats?.node_counts || {};
  const verdictDist = stats?.verdict_distribution || {};
  const totalNews = nodeCounts.News || 0;
  const trueCount = verdictDist["LIKELY TRUE"] || 0;
  const suspiciousCount = verdictDist["SUSPICIOUS"] || 0;
  const fakeCount = verdictDist["LIKELY FAKE"] || 0;
  const totalRels = stats?.total_relationships || 0;

  return (
    <div
      className="border border-border bg-card p-4 rounded-sm"
      data-testid="quick-stats-card"
    >
      <div className="flex items-center gap-2 mb-3">
        <BarChart3 className="w-4 h-4 text-muted-foreground" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          Quick Stats
        </span>
      </div>

      {totalNews === 0 ? (
        <p className="text-xs text-muted-foreground/50 text-center py-3">
          Seed the database to see statistics
        </p>
      ) : (
        <>
          {/* Top row — big numbers */}
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="font-mono text-2xl font-bold">{totalNews}</div>
              <div className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
                Articles
              </div>
            </div>
            <div>
              <div className="font-mono text-2xl font-bold">{nodeCounts.Source || 0}</div>
              <div className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
                Sources
              </div>
            </div>
            <div>
              <div className="font-mono text-2xl font-bold">{totalRels}</div>
              <div className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
                Relations
              </div>
            </div>
          </div>

          <Separator className="my-3" />

          {/* Verdict mini-bars */}
          <div className="space-y-2">
            <VerdictRow icon={ShieldCheck} label="True" count={trueCount} total={totalNews} color="bg-blue-500" textColor="text-blue-500" />
            <VerdictRow icon={AlertTriangle} label="Suspicious" count={suspiciousCount} total={totalNews} color="bg-yellow-500" textColor="text-yellow-500" />
            <VerdictRow icon={ShieldAlert} label="Fake" count={fakeCount} total={totalNews} color="bg-red-500" textColor="text-red-500" />
          </div>
        </>
      )}
    </div>
  );
}

function VerdictRow({ icon: Icon, label, count, total, color, textColor }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex items-center gap-2">
      <Icon className={`w-3.5 h-3.5 ${textColor} shrink-0`} />
      <span className="font-mono text-[10px] w-16 text-muted-foreground">{label}</span>
      <div className="flex-1 h-1.5 bg-muted rounded-none overflow-hidden">
        <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono text-[10px] font-bold w-6 text-right">{count}</span>
    </div>
  );
}
