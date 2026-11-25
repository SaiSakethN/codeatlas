"use client";
import { useMemo } from "react";
import { ReactFlow, Background, Controls, MiniMap } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { Overview } from "@/lib/types";

export default function Architecture({ overview, onSelect }: { overview: Overview; onSelect: (path: string) => void }) {
  const nodes = useMemo(() => overview.nodes.slice(0, 200).map((node, i) => ({
    id: node.id, data: { label: node.id }, position: { x: (i % 4) * 270, y: Math.floor(i / 4) * 100 },
    style: { background: "#1c1928", color: "#ded3f7", border: "1px solid #635079", width: 240, fontSize: 12 },
  })), [overview]);
  const ids = useMemo(() => new Set(nodes.map(n => n.id)), [nodes]);
  const edges = useMemo(() => overview.edges.filter(e => ids.has(e.source) && ids.has(e.target)).map((edge, i) => ({ id: String(i), ...edge, style: { stroke: "#75608f" } })), [overview, ids]);
  return <><p className="muted text-sm mb-4">Static Python imports · Select a module to inspect its source. {overview.nodes.length > 200 ? "Showing the first 200 modules." : ""}</p><div style={{ height: "60vh", minHeight: 350 }}><ReactFlow nodes={nodes} edges={edges} onNodeClick={(_, node) => onSelect(node.id)} fitView colorMode="dark" nodesDraggable={false} nodesConnectable={false} minZoom={0.1}><Background /><Controls /><MiniMap pannable zoomable /></ReactFlow></div><p className="muted text-sm mt-4">{overview.limitations}</p></>;
}
