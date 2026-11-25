import { FileCode2 } from "lucide-react";

export function FileTree({ files, onSelect, prefix = "" }: { files: string[]; onSelect: (path: string) => void; prefix?: string }) {
  const entries = [...new Set(files.map(file => file.slice(prefix.length).split("/")[0]))];
  return <div className="file-tree">{entries.map(entry => {
    const path = prefix + entry;
    const children = files.filter(file => file.startsWith(path + "/"));
    return children.length ? <details key={path}><summary>{entry}</summary><div className="children"><FileTree files={children} prefix={path + "/"} onSelect={onSelect} /></div></details>
      : <button key={path} onClick={() => onSelect(path)} title={path}><FileCode2 size={13} className="shrink-0" />{entry}</button>;
  })}</div>;
}
