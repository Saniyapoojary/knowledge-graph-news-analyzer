import React from "react";
import { Clock, ShieldCheck, ShieldAlert, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function RecentAnalysisCard({ history }) {
  const recent = (history || []).slice(0, 3);

  return (
    <div
      className="border border-border bg-card p-4 rounded-sm flex-1"
      data-testid="recent-analysis-card"
    >
      <div className="flex items-center gap-2 mb-3">
        <Clock className="w-4 h-4 text-muted-foreground" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          Recent Analysis
        </span>
      </div>

      {recent.length === 0 ? (
        <p className="text-xs text-muted-foreground/50 text-center py-3">
          Analyze articles to see recent results here
        </p>
      ) : (
        <div className="space-y-2">
          {recent.map((item, i) => {
            const displayLabel = item.label || item.verdict;
            const isTrust = displayLabel === "Likely True" || displayLabel === "LIKELY TRUE";
            const isFake = displayLabel === "Likely Fake" || displayLabel === "LIKELY FAKE";
            const Icon = isTrust ? ShieldCheck : isFake ? ShieldAlert : AlertTriangle;
            const iconColor = isTrust ? "text-blue-500" : isFake ? "text-red-500" : "text-yellow-500";
            const badgeClass = isTrust
              ? "text-blue-500 border-blue-500/30"
              : isFake
              ? "text-red-500 border-red-500/30"
              : "text-yellow-500 border-yellow-500/30";

            return (
              <div
                key={item.id || i}
                className="flex items-start gap-2.5 p-2 rounded-sm border border-border/50 hover:bg-accent/30 transition-colors"
                data-testid={`recent-item-${i}`}
              >
                <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${iconColor}`} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs truncate leading-snug">
                    {item.text_preview}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="font-mono text-[10px] font-bold">
                      {item.score ?? item.fake_score}
                    </span>
                    <Badge
                      variant="outline"
                      className={`rounded-sm text-[9px] font-mono px-1.5 py-0 h-4 ${badgeClass}`}
                    >
                      {displayLabel}
                    </Badge>
                    <span className="font-mono text-[9px] text-muted-foreground/50 ml-auto">
                      {item.source}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
