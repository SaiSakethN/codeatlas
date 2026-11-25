"use client";
import Markdown from "react-markdown";
import type { Source } from "@/lib/types";

export function GroundedAnswer({ text, sources, onSource }: { text: string; sources: Source[]; onSource: (source: Source) => void }) {
  const linked = text.replace(/\[(S\d+)\]/g, (_, id) => sources.some(s => s.id === id) ? `[${id}](#source-${id})` : `[${id}]`);
  return <div className="answer"><Markdown components={{
    a: ({ href, children }) => {
      if (href?.startsWith("#source-")) {
        const source = sources.find(s => s.id === href.slice(8));
        return <button className="citation" aria-label={`Open source ${source?.id}`} onClick={() => source && onSource(source)}>{children}</button>;
      }
      return <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
    },
  }}>{linked}</Markdown></div>;
}
