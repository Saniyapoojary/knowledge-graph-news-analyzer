import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, ShieldAlert, AlertTriangle, Info, ChevronRight, Database } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

function ScoreGauge({ score, label }) {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(score, 100) / 100) * circumference;
  
  const color =
    label === "Likely True" ? "hsl(var(--accent-trust))" :
    label === "Likely Fake" ? "hsl(var(--accent-fake))" :
    "hsl(var(--accent-suspicious))";

  return (
    <div className="relative w-32 h-32 mx-auto" data-testid="score-gauge">
      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
        <circle
          cx="50" cy="50" r={radius}
          fill="none"
          stroke="hsl(var(--border))"
          strokeWidth="6"
        />
        <motion.circle
          cx="50" cy="50" r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
          strokeLinecap="butt"
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.2, ease: "easeOut" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-3xl font-bold" style={{ color }} data-testid="score-value">
          {score}
        </span>
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          score
        </span>
      </div>
    </div>
  );
}

function LabelBadge({ label }) {
  const config = {
    "Likely True": { icon: ShieldCheck, className: "bg-blue-500/10 text-blue-500 border-blue-500/30" },
    "Likely Fake": { icon: ShieldAlert, className: "bg-red-500/10 text-red-500 border-red-500/30" },
    "Suspicious": { icon: AlertTriangle, className: "bg-yellow-500/10 text-yellow-500 border-yellow-500/30" },
  };

  const { icon: Icon, className } = config[label] || config["Suspicious"];

  return (
    <Badge
      variant="outline"
      className={`rounded-sm font-mono text-xs uppercase tracking-wider px-3 py-1 ${className}`}
      data-testid="verdict-badge"
    >
      <Icon className="w-3.5 h-3.5 mr-1.5" />
      {label}
    </Badge>
  );
}

export default function ResultsPanel({ result, isAnalyzing }) {
  if (!result && !isAnalyzing) {
    return (
      <div
        className="border border-dashed border-border bg-card/50 p-8 rounded-sm flex flex-col items-center justify-center min-h-[200px]"
        data-testid="results-empty"
      >
        <Info className="w-8 h-8 text-muted-foreground/40 mb-3" />
        <p className="font-mono text-xs uppercase tracking-wider text-muted-foreground text-center">
          Submit an article to see analysis results
        </p>
      </div>
    );
  }

  if (isAnalyzing) {
    return (
      <div
        className="border border-border bg-card p-8 rounded-sm flex flex-col items-center justify-center min-h-[200px]"
        data-testid="results-loading"
      >
        <div className="flex items-center gap-2 mb-3">
          <span className="font-mono text-sm text-muted-foreground">Processing</span>
          <span className="font-mono text-sm text-foreground cursor-blink">_</span>
        </div>
        <Progress value={66} className="w-48 h-1 rounded-none" />
        <p className="font-mono text-[10px] text-muted-foreground mt-2 uppercase tracking-wider">
          Extracting entities &amp; querying graph...
        </p>
      </div>
    );
  }

  const score = result.score ?? result.fake_score;
  const label = result.label || (result.verdict === "LIKELY TRUE" ? "Likely True" : result.verdict === "LIKELY FAKE" ? "Likely Fake" : "Suspicious");
  const breakdown = result.breakdown || {};

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={result.id}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.3 }}
        className="border border-border bg-card p-5 rounded-sm"
        data-testid="results-panel"
      >
        {/* Header row */}
        <div className="flex items-center justify-between mb-4">
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            Analysis Result
          </span>
          <span className="font-mono text-[10px] text-muted-foreground">
            ID: {result.id}
          </span>
        </div>

        {/* Score + Label */}
        <div className="flex items-center gap-6">
          <ScoreGauge score={score} label={label} />
          <div className="flex-1 space-y-3">
            <LabelBadge label={label} />
            <p className="text-sm text-muted-foreground leading-relaxed">
              {label === "Likely True"
                ? "This article shows patterns consistent with credible reporting."
                : label === "Likely Fake"
                ? "This article exhibits multiple characteristics of misinformation."
                : "This article has some concerning patterns that warrant verification."}
            </p>
          </div>
        </div>

        <Separator className="my-4" />

        {/* Score Breakdown — formula visualization */}
        {breakdown.formula && (
          <>
            <div className="space-y-3" data-testid="score-breakdown">
              <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
                Score Breakdown (Neo4j Graph)
              </span>
              <div className="bg-background border border-border rounded-sm p-3">
                <div className="font-mono text-xs text-center mb-3" data-testid="score-formula">
                  <span className="text-muted-foreground">score = </span>
                  <span className="text-red-400">(source:{breakdown.source_count} x 5)</span>
                  <span className="text-muted-foreground"> + </span>
                  <span className="text-yellow-400">(author:{breakdown.author_count} x 3)</span>
                  <span className="text-muted-foreground"> + </span>
                  <span className="text-blue-400">(topic:{breakdown.topic_frequency} x 2)</span>
                  <span className="text-muted-foreground"> = </span>
                  <span className="text-foreground font-bold">{breakdown.raw_score}</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <BreakdownBar
                    label="Source"
                    count={breakdown.source_count}
                    total={breakdown.source_total}
                    multiplier={5}
                    color="bg-red-500"
                  />
                  <BreakdownBar
                    label="Author"
                    count={breakdown.author_count}
                    total={breakdown.author_total}
                    multiplier={3}
                    color="bg-yellow-500"
                  />
                  <BreakdownBar
                    label="Topic"
                    count={breakdown.topic_frequency}
                    total={breakdown.topic_frequency}
                    multiplier={2}
                    color="bg-blue-500"
                  />
                </div>
              </div>
            </div>
            <Separator className="my-4" />
          </>
        )}

        {/* Reason — detailed explanation using graph data */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
              Reason (Graph Analysis)
            </span>
          </div>
          <div className="space-y-1.5" data-testid="explanation-list">
            {result.explanation.map((exp, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-start gap-2 text-sm"
              >
                <ChevronRight className="w-3.5 h-3.5 text-muted-foreground mt-0.5 shrink-0" />
                <span>{exp}</span>
              </motion.div>
            ))}
          </div>
        </div>

        <Separator className="my-4" />

        {/* Entities */}
        <div className="space-y-2">
          <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground">
            Extracted Entities
          </span>
          <div className="flex flex-wrap gap-1.5" data-testid="entities-list">
            {result.entities?.topics?.map((t) => (
              <Badge key={t} variant="outline" className="rounded-sm text-[10px] font-mono bg-yellow-500/5 text-yellow-600 dark:text-yellow-400 border-yellow-500/20">
                {t}
              </Badge>
            ))}
            {result.entities?.organizations?.map((o) => (
              <Badge key={o} variant="outline" className="rounded-sm text-[10px] font-mono bg-indigo-500/5 text-indigo-600 dark:text-indigo-400 border-indigo-500/20">
                {o}
              </Badge>
            ))}
            {result.entities?.persons?.map((p) => (
              <Badge key={p} variant="outline" className="rounded-sm text-[10px] font-mono bg-green-500/5 text-green-600 dark:text-green-400 border-green-500/20">
                {p}
              </Badge>
            ))}
            {result.entities?.locations?.map((l) => (
              <Badge key={l} variant="outline" className="rounded-sm text-[10px] font-mono bg-blue-500/5 text-blue-600 dark:text-blue-400 border-blue-500/20">
                {l}
              </Badge>
            ))}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}

function BreakdownBar({ label, count, total, multiplier, color }) {
  const contribution = count * multiplier;
  const maxWidth = Math.min((contribution / 50) * 100, 100);
  return (
    <div className="text-center" data-testid={`breakdown-${label.toLowerCase()}`}>
      <div className="font-mono text-lg font-bold">{count}</div>
      <div className="font-mono text-[9px] text-muted-foreground uppercase tracking-wider">{label} (x{multiplier})</div>
      <div className="w-full h-1.5 bg-muted rounded-none mt-1.5 overflow-hidden">
        <div className={`h-full ${color} transition-all duration-700`} style={{ width: `${maxWidth}%` }} />
      </div>
      <div className="font-mono text-[9px] text-muted-foreground mt-0.5">= {contribution} pts</div>
    </div>
  );
}
