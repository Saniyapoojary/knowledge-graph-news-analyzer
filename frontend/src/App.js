import React, { useState, useCallback, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import Header from "@/components/Header";
import AnalysisPanel from "@/components/AnalysisPanel";
import ResultsPanel from "@/components/ResultsPanel";
import GraphVisualization from "@/components/GraphVisualization";
import HistoryPanel from "@/components/HistoryPanel";
import StatsPanel from "@/components/StatsPanel";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [theme, setTheme] = useState("dark");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [activeView, setActiveView] = useState("analyze");
  const [isSeeded, setIsSeeded] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/history`);
      setHistory(res.data);
    } catch (e) {
      console.error("Failed to fetch history", e);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/stats`);
      setStats(res.data);
    } catch (e) {
      console.error("Failed to fetch stats", e);
    }
  }, []);

  const fetchGraph = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/graph`);
      setGraphData(res.data);
    } catch (e) {
      console.error("Failed to fetch graph", e);
    }
  }, []);

  const seedDatabase = useCallback(async () => {
    try {
      const res = await axios.post(`${API}/seed`);
      setIsSeeded(true);
      fetchStats();
      fetchGraph();
      fetchHistory();
      return res.data;
    } catch (e) {
      console.error("Failed to seed database", e);
      throw e;
    }
  }, [fetchStats, fetchGraph, fetchHistory]);

  const analyzeNews = useCallback(
    async (text, source, author) => {
      setIsAnalyzing(true);
      try {
        const res = await axios.post(`${API}/analyze`, { text, source, author });
        setAnalysisResult(res.data);
        setGraphData(res.data.graph_data);
        fetchHistory();
        fetchStats();
        return res.data;
      } catch (e) {
        console.error("Analysis failed", e);
        throw e;
      } finally {
        setIsAnalyzing(false);
      }
    },
    [fetchHistory, fetchStats]
  );

  useEffect(() => {
    fetchHistory();
    fetchStats();
    fetchGraph();
  }, [fetchHistory, fetchStats, fetchGraph]);

  return (
    <div
      className="min-h-screen bg-background text-foreground"
      data-testid="app-container"
    >
      <Header
        theme={theme}
        toggleTheme={toggleTheme}
        activeView={activeView}
        setActiveView={setActiveView}
        seedDatabase={seedDatabase}
        isSeeded={isSeeded}
      />

      <main className="max-w-[1600px] mx-auto px-4 pt-4 pb-8">
        {activeView === "analyze" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Left: Input */}
            <div className="lg:col-span-5 space-y-4">
              <AnalysisPanel
                onAnalyze={analyzeNews}
                isAnalyzing={isAnalyzing}
              />
            </div>

            {/* Right: Results + Graph */}
            <div className="lg:col-span-7 space-y-4">
              <ResultsPanel result={analysisResult} isAnalyzing={isAnalyzing} />
              <GraphVisualization
                graphData={
                  analysisResult ? analysisResult.graph_data : graphData
                }
              />
            </div>
          </div>
        )}

        {activeView === "history" && <HistoryPanel history={history} />}

        {activeView === "stats" && (
          <StatsPanel stats={stats} graphData={graphData} />
        )}

        {activeView === "graph" && (
          <div className="h-[calc(100vh-120px)]">
            <GraphVisualization graphData={graphData} fullScreen />
          </div>
        )}
      </main>

      <Toaster position="bottom-right" />
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
