import React, { useRef, useEffect, useState, useCallback } from "react";
import * as d3 from "d3";
import { Network, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function GraphVisualization({ graphData, fullScreen = false }) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const simulationRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);

  const drawGraph = useCallback(() => {
    if (!svgRef.current || !graphData?.nodes?.length) return;

    const container = containerRef.current;
    const width = container.clientWidth || 800;
    const rawHeight = container.clientHeight;
    const height = fullScreen ? Math.max(rawHeight - 42, 500) : 380;

    // Deep copy to avoid D3 mutating shared state
    const nodes = graphData.nodes.map((n) => ({ ...n }));
    const links = graphData.links.map((l) => ({ ...l }));

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.attr("width", width).attr("height", height);

    // Zoom behavior
    const g = svg.append("g");
    const zoom = d3.zoom()
      .scaleExtent([0.1, 5])
      .on("zoom", (event) => g.attr("transform", event.transform));
    svg.call(zoom);

    // Adjust forces based on graph size
    const nodeCount = nodes.length;
    const chargeStrength = nodeCount > 100 ? -60 : nodeCount > 50 ? -120 : -200;
    const linkDist = nodeCount > 100 ? 40 : nodeCount > 50 ? 60 : 80;

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d) => d.id).distance(linkDist))
      .force("charge", d3.forceManyBody().strength(chargeStrength))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius((d) => (d.size || 8) + 2));

    simulationRef.current = simulation;

    // Links
    const link = g
      .append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", (d) => d.type === "PUBLISHED_BY" ? "hsl(var(--accent-fake) / 0.4)" : "hsl(var(--muted-foreground) / 0.2)")
      .attr("stroke-width", 1);

    // Node groups
    const node = g
      .append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .call(
        d3.drag()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Node circles
    node
      .append("circle")
      .attr("r", (d) => d.size || 8)
      .attr("fill", (d) => d.color || "#94A3B8")
      .attr("stroke", (d) => d.color || "#94A3B8")
      .attr("stroke-width", 2)
      .attr("fill-opacity", 0.15)
      .style("cursor", "grab");

    // Node labels
    node
      .append("text")
      .text((d) => {
        const label = d.label || d.id;
        return label.length > 20 ? label.slice(0, 18) + ".." : label;
      })
      .attr("dx", (d) => (d.size || 8) + 4)
      .attr("dy", 3)
      .attr("font-size", "9px")
      .attr("font-family", "'IBM Plex Mono', monospace")
      .attr("fill", "hsl(var(--foreground) / 0.7)");

    // Hover events
    node
      .on("mouseenter", (event, d) => {
        const rect = container.getBoundingClientRect();
        setTooltip({
          x: event.clientX - rect.left,
          y: event.clientY - rect.top - 10,
          data: d,
        });
      })
      .on("mouseleave", () => setTooltip(null));

    // Tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    // Auto-fit after simulation settles
    simulation.on("end", () => {
      const bounds = g.node().getBBox();
      if (bounds.width > 0 && bounds.height > 0) {
        const scale = Math.min(
          (width - 40) / bounds.width,
          (height - 40) / bounds.height,
          1.5
        );
        const tx = (width - bounds.width * scale) / 2 - bounds.x * scale;
        const ty = (height - bounds.height * scale) / 2 - bounds.y * scale;
        svg.transition().duration(500).call(
          zoom.transform,
          d3.zoomIdentity.translate(tx, ty).scale(scale)
        );
      }
    });

    return () => simulation.stop();
  }, [graphData, fullScreen]);

  useEffect(() => {
    drawGraph();
    const handleResize = () => drawGraph();
    window.addEventListener("resize", handleResize);
    return () => {
      window.removeEventListener("resize", handleResize);
      if (simulationRef.current) simulationRef.current.stop();
    };
  }, [drawGraph]);

  const handleZoom = (direction) => {
    const svg = d3.select(svgRef.current);
    const zoomBehavior = d3.zoom().scaleExtent([0.3, 5]);
    if (direction === "in") {
      svg.transition().duration(300).call(zoomBehavior.scaleBy, 1.5);
    } else {
      svg.transition().duration(300).call(zoomBehavior.scaleBy, 0.67);
    }
  };

  const hasData = graphData?.nodes?.length > 0;

  return (
    <div
      ref={containerRef}
      className={`border border-border bg-card rounded-sm relative ${fullScreen ? "h-full" : ""}`}
      data-testid="graph-visualization"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-muted-foreground" />
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            Knowledge Graph
          </span>
          {hasData && (
            <span className="font-mono text-[10px] text-muted-foreground/60">
              {graphData.nodes.length} nodes / {graphData.links.length} edges
            </span>
          )}
        </div>
        {hasData && (
          <div className="flex gap-1">
            <Button
              variant="ghost" size="icon"
              className="h-6 w-6 rounded-sm"
              onClick={() => handleZoom("in")}
              data-testid="graph-zoom-in"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="ghost" size="icon"
              className="h-6 w-6 rounded-sm"
              onClick={() => handleZoom("out")}
              data-testid="graph-zoom-out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </Button>
          </div>
        )}
      </div>

      {/* Graph */}
      {hasData ? (
        <svg ref={svgRef} className="w-full" style={{ height: fullScreen ? "calc(100% - 44px)" : 380, minHeight: fullScreen ? 500 : 380 }} />
      ) : (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground/40">
          <Network className="w-10 h-10 mb-3" />
          <p className="font-mono text-xs uppercase tracking-wider">
            No graph data yet
          </p>
          <p className="text-xs mt-1 text-muted-foreground/30">
            Seed the database or analyze an article
          </p>
        </div>
      )}

      {/* Tooltip */}
      {tooltip && (
        <div
          className="absolute pointer-events-none bg-popover border border-border px-3 py-2 rounded-sm shadow-lg z-50"
          style={{ left: tooltip.x + 12, top: tooltip.y - 40 }}
        >
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">
            {tooltip.data.type}
          </div>
          <div className="text-sm font-medium">{tooltip.data.label}</div>
          {tooltip.data.score !== undefined && (
            <div className="font-mono text-xs mt-0.5">
              Score: <span className="font-bold">{tooltip.data.score}</span>
            </div>
          )}
          {tooltip.data.verdict && (
            <div className="font-mono text-[10px] mt-0.5" style={{ color: tooltip.data.color }}>
              {tooltip.data.verdict}
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      {hasData && (
        <div className="absolute bottom-2 left-3 flex flex-wrap gap-3 text-[10px] font-mono text-muted-foreground/60">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500" />Trustworthy</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />Fake</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" />Suspicious</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-indigo-500" />Source</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" />Author</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />Topic</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-pink-500" />Person</span>
        </div>
      )}
    </div>
  );
}
