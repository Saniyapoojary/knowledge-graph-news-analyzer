import React, { useState } from "react";
import { Send, FileText, User, Globe, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

const EXAMPLE_ARTICLES = [
  {
    label: "Trustworthy",
    text: "The Federal Reserve announced today that it will maintain current interest rates, citing stable employment numbers and controlled inflation at 2.1%. Chair Jerome Powell said the committee will continue monitoring economic indicators before making any changes. Markets responded calmly with modest gains across major indices.",
    source: "reuters",
    author: "jane martinez",
  },
  {
    label: "Suspicious",
    text: "SHOCKING: Secret documents LEAKED showing government covered up major health crisis! They don't want you to know the truth about what's really happening. Share this before it gets deleted! The mainstream media is REFUSING to cover this story!",
    source: "truthrevealed.net",
    author: "anonymous whistleblower",
  },
  {
    label: "Mixed",
    text: "An unverified report circulating online suggests a major tech company may be developing an advanced surveillance system. While some former employees have expressed concerns, the company has neither confirmed nor denied the claims. Independent verification is still pending.",
    source: "tech daily",
    author: "alex reed",
  },
];

export default function AnalysisPanel({ onAnalyze, isAnalyzing }) {
  const [text, setText] = useState("");
  const [source, setSource] = useState("");
  const [author, setAuthor] = useState("");

  const handleSubmit = async () => {
    if (!text.trim() || text.trim().length < 10) {
      toast.error("Please enter at least 10 characters of article text");
      return;
    }
    try {
      await onAnalyze(text.trim(), source.trim() || "unknown", author.trim() || "unknown");
      toast.success("Analysis complete");
    } catch {
      toast.error("Analysis failed. Please try again.");
    }
  };

  const loadExample = (example) => {
    setText(example.text);
    setSource(example.source);
    setAuthor(example.author);
  };

  return (
    <div
      className="border border-border bg-card p-5 rounded-sm"
      data-testid="analysis-panel"
    >
      {/* Section label */}
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-4 h-4 text-muted-foreground" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          Article Input
        </span>
      </div>

      {/* Text area */}
      <Textarea
        data-testid="article-input"
        placeholder="Paste your news article text here for analysis..."
        className="min-h-[200px] rounded-sm bg-background border-border font-sans text-sm resize-none focus:ring-2 focus:ring-foreground focus:ring-offset-2 focus:ring-offset-background"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />

      {/* Metadata fields */}
      <div className="grid grid-cols-2 gap-3 mt-3">
        <div className="space-y-1.5">
          <label className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground flex items-center gap-1.5">
            <Globe className="w-3 h-3" />
            Source
          </label>
          <Input
            data-testid="source-input"
            placeholder="e.g. reuters, bbc"
            className="rounded-sm h-8 text-xs bg-background"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <label className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground flex items-center gap-1.5">
            <User className="w-3 h-3" />
            Author
          </label>
          <Input
            data-testid="author-input"
            placeholder="e.g. john doe"
            className="rounded-sm h-8 text-xs bg-background"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
          />
        </div>
      </div>

      {/* Submit */}
      <Button
        data-testid="analyze-button"
        className="w-full mt-4 rounded-sm font-mono text-xs uppercase tracking-wider h-10 transition-all duration-200"
        onClick={handleSubmit}
        disabled={isAnalyzing || text.trim().length < 10}
      >
        {isAnalyzing ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Send className="w-4 h-4 mr-2" />
            Analyze Article
          </>
        )}
      </Button>

      {/* Example articles */}
      <div className="mt-4 pt-4 border-t border-border">
        <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-muted-foreground block mb-2">
          Try an example
        </span>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_ARTICLES.map((ex) => (
            <Button
              key={ex.label}
              variant="outline"
              size="sm"
              className="rounded-sm text-xs h-7 px-2.5"
              onClick={() => loadExample(ex)}
              data-testid={`example-${ex.label.toLowerCase()}`}
            >
              {ex.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Character count */}
      <div className="mt-2 text-right">
        <span className="font-mono text-[10px] text-muted-foreground">
          {text.length} chars
        </span>
      </div>
    </div>
  );
}
