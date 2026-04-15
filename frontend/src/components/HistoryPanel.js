import React from "react";
import { Clock, ShieldCheck, ShieldAlert, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

function VerdictIcon({ verdict, label }) {
  const v = label || verdict;
  if (v === "LIKELY TRUE" || v === "Likely True") return <ShieldCheck className="w-4 h-4 text-blue-500" />;
  if (v === "LIKELY FAKE" || v === "Likely Fake") return <ShieldAlert className="w-4 h-4 text-red-500" />;
  return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
}

function ScoreBar({ score }) {
  const capped = Math.min(score, 100);
  const color = capped < 30 ? "bg-blue-500" : capped > 70 ? "bg-red-500" : "bg-yellow-500";
  return (
    <div className="w-16 h-1.5 bg-muted rounded-none overflow-hidden">
      <div className={`h-full ${color} transition-all`} style={{ width: `${capped}%` }} />
    </div>
  );
}

export default function HistoryPanel({ history }) {
  if (!history?.length) {
    return (
      <div className="border border-dashed border-border bg-card/50 p-12 rounded-sm text-center" data-testid="history-empty">
        <Clock className="w-10 h-10 text-muted-foreground/30 mx-auto mb-3" />
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
          No analysis history yet
        </p>
        <p className="text-xs text-muted-foreground/50 mt-1">
          Analyze some articles to see them here
        </p>
      </div>
    );
  }

  return (
    <div className="border border-border bg-card rounded-sm" data-testid="history-panel">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
        <Clock className="w-4 h-4 text-muted-foreground" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          Analysis History
        </span>
        <span className="font-mono text-[10px] text-muted-foreground/50 ml-auto">
          {history.length} records
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground p-3">Preview</th>
              <th className="text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground p-3 w-24">Source</th>
              <th className="text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground p-3 w-20">Score</th>
              <th className="text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground p-3 w-32">Verdict</th>
              <th className="text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground p-3 w-36">Time</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item, i) => (
              <tr
                key={item.id || i}
                className="border-b border-border/50 hover:bg-accent/50 transition-colors"
                data-testid={`history-row-${i}`}
              >
                <td className="p-3 max-w-[300px]">
                  <p className="text-xs truncate">{item.text_preview}</p>
                </td>
                <td className="p-3">
                  <span className="font-mono text-[10px] text-muted-foreground">{item.source}</span>
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold">{item.score ?? item.fake_score}</span>
                    <ScoreBar score={item.score ?? item.fake_score} />
                  </div>
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-1.5">
                    <VerdictIcon verdict={item.verdict} label={item.label} />
                    {(() => {
                      const displayLabel = item.label || item.verdict;
                      const isTrust = displayLabel === "Likely True" || displayLabel === "LIKELY TRUE";
                      const isFake = displayLabel === "Likely Fake" || displayLabel === "LIKELY FAKE";
                      return (
                        <Badge
                          variant="outline"
                          className={`rounded-sm text-[10px] font-mono ${
                            isTrust ? "text-blue-500 border-blue-500/30" :
                            isFake ? "text-red-500 border-red-500/30" :
                            "text-yellow-500 border-yellow-500/30"
                          }`}
                        >
                          {item.label || item.verdict}
                        </Badge>
                      );
                    })()}
                  </div>
                </td>
                <td className="p-3">
                  <span className="font-mono text-[10px] text-muted-foreground">
                    {new Date(item.timestamp).toLocaleString()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
