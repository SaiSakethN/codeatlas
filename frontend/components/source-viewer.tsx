"use client";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
SyntaxHighlighter.registerLanguage("python", python);

export default function SourceViewer({ content, start }: { content: string; start: number }) {
  return <SyntaxHighlighter language="python" style={vscDarkPlus} showLineNumbers startingLineNumber={start} customStyle={{ background: "#111218", fontSize: 12, padding: "16px 8px", border: "1px solid #292b36", borderRadius: 6 }} wrapLongLines={false}>{content}</SyntaxHighlighter>;
}
