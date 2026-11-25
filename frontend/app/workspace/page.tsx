"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { Compass, Plus, MessagesSquare, LayoutDashboard, GitBranch, BookOpen, GitCompareArrows, PanelLeft, PanelRight, X, Send, LoaderCircle, FileCode2, Trash2, LockKeyhole, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FileTree } from "@/components/file-tree";
import { GroundedAnswer } from "@/components/answer";
import { api } from "@/lib/api";
import type { Repository, Overview, Impact, Job, Source, Answer } from "@/lib/types";

const Architecture = dynamic(() => import("@/components/architecture"), { ssr: false, loading: () => <p className="muted">Loading architecture viewer…</p> });
const SourceViewer = dynamic(() => import("@/components/source-viewer"), { ssr: false, loading: () => <p className="muted">Loading source viewer…</p> });
type View = "investigation" | "overview" | "architecture" | "onboarding" | "impact";
type Turn = { question: string; result: Answer };
const navigation = [
  { id: "investigation", label: "Investigation", icon: MessagesSquare },
  { id: "overview", label: "Repository overview", icon: LayoutDashboard },
  { id: "architecture", label: "Architecture", icon: GitBranch },
  { id: "onboarding", label: "Onboarding", icon: BookOpen },
  { id: "impact", label: "Change impact", icon: GitCompareArrows },
] as const;

export default function Workspace() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selected, setSelected] = useState("");
  const [view, setView] = useState<View>("investigation");
  const [files, setFiles] = useState<string[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [impact, setImpact] = useState<Impact | null>(null);
  const [source, setSource] = useState<(Source & { imports?: string[] }) | null>(null);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<"rag" | "agent">("rag");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [url, setUrl] = useState("");
  const [showImport, setShowImport] = useState(false);
  const [job, setJob] = useState<Job | null>(null);
  const [mobileNav, setMobileNav] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [filter, setFilter] = useState("");
  const [password, setPassword] = useState("");
  const [needsLogin, setNeedsLogin] = useState(false);
  const [reload, setReload] = useState(0);
  const generation = useRef(0);
  const sourceGeneration = useRef(0);
  const endRef = useRef<HTMLDivElement>(null);
  const repository = repositories.find(r => r.id === selected);

  useEffect(() => {
    let cancelled = false;
    api<Repository[]>("/api/repositories").then(data => {
      if (cancelled) return;
      setRepositories(data); setSelected(current => data.some(r => r.id === current) ? current : data[0]?.id || "");
      setNeedsLogin(false); setError("");
    }).catch(e => { if (!cancelled) { setError(e.message); setNeedsLogin(e.message.includes("Sign in")); } })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [reload]);

  useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    Promise.all([
      api<{ files: string[] }>(`/api/repositories/${selected}/tree`),
      api<Overview>(`/api/repositories/${selected}/overview`),
      api<Impact>(`/api/repositories/${selected}/impact`),
    ]).then(([tree, details, changes]) => {
      if (!cancelled) { setFiles(tree.files); setOverview(details); setImpact(changes); }
    }).catch(e => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [selected, reload]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [turns, busy]);

  useEffect(() => {
    if (!job || !["queued", "indexing"].includes(job.status)) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      api<Job>(`/api/jobs/${job.id}`).then(next => {
        if (cancelled) return;
        setJob(next);
        if (next.status === "completed") { switchRepository(next.repository_id || ""); setReload(v => v + 1); setShowImport(false); }
        if (next.status === "failed") setError(next.error || "Import failed.");
      }).catch(e => { if (!cancelled) { setError(e.message); setJob(null); } });
    }, 1500);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [job]);

  function switchRepository(id: string) {
    generation.current++; sourceGeneration.current++;
    setSelected(id); setTurns([]); setSource(null); setOverview(null); setImpact(null); setFiles([]); setError(""); setView("investigation"); setBusy(false); setFilter("");
  }

  async function openFile(path: string, start = 1) {
    const requestId = ++sourceGeneration.current;
    setEvidenceOpen(true); setSourceLoading(true);
    try {
      const result = await api<Source & { imports: string[] }>(`/api/repositories/${selected}/source?path=${encodeURIComponent(path)}&start=${start}`);
      if (requestId === sourceGeneration.current) setSource(result);
    } catch (e) { if (requestId === sourceGeneration.current) setError((e as Error).message); }
    finally { if (requestId === sourceGeneration.current) setSourceLoading(false); }
  }

  async function ask(text = question) {
    if (!text.trim() || !selected || busy) return;
    const requestGeneration = generation.current;
    setBusy(true); setError(""); setQuestion(""); setView("investigation");
    try {
      const result = await api<Answer>(`/api/repositories/${selected}/questions`, {
        method: "POST", body: JSON.stringify({ question: text, mode, history: turns.slice(-3).flatMap(t => [{ role: "user", content: t.question }, { role: "assistant", content: t.result.answer }]) }),
      });
      if (requestGeneration === generation.current) setTurns(previous => [...previous, { question: text, result }]);
    } catch (e) { if (requestGeneration === generation.current) { setError((e as Error).message); setQuestion(text); } }
    finally { if (requestGeneration === generation.current) setBusy(false); }
  }

  async function importRepository(event: React.FormEvent) {
    event.preventDefault(); setError("");
    try { setJob(await api<Job>("/api/repositories", { method: "POST", body: JSON.stringify({ url }) })); }
    catch (e) { setError((e as Error).message); }
  }

  async function removeRepository() {
    if (!repository || !window.confirm(`Remove ${repository.name} from the catalog and clear its current index?`)) return;
    try { await api(`/api/repositories/${selected}`, { method: "DELETE" }); switchRepository(""); setReload(v => v + 1); }
    catch (e) { setError((e as Error).message); }
  }

  async function login(event: React.FormEvent) {
    event.preventDefault();
    try {
      const response = await fetch("/api/session", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      setPassword(""); setReload(v => v + 1);
    } catch (e) { setError((e as Error).message); }
  }

  const activeJob = job && ["queued", "indexing"].includes(job.status);
  const suggested = overview?.onboarding.suggested_questions || ["What are the main entry points?", "How does error handling work?", "Where should a new contributor start?"];

  return <main className={`workspace ${evidenceOpen ? "" : "evidence-collapsed"}`}>
    <aside className={`sidebar ${mobileNav ? "open" : ""}`} aria-label="Repository navigation">
      <div className="flex items-center justify-between"><Link href="/" className="brand"><Compass size={24} />CodeAtlas</Link><Button className="mobile-toggle" variant="ghost" size="icon" aria-label="Close navigation" onClick={() => setMobileNav(false)}><X /></Button></div>
      <div><label className="eyebrow block mb-3" htmlFor="repository">Repository</label><select id="repository" value={selected} onChange={e => switchRepository(e.target.value)}><option value="">Select a repository</option>{repositories.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select><Button className="w-full mt-3" variant="outline" size="sm" onClick={() => { setShowImport(true); setMobileNav(false); }}><Plus />Import repository</Button></div>
      <nav className="navigation">{navigation.map(item => <button className={`nav-item ${view === item.id ? "active" : ""}`} key={item.id} onClick={() => { setView(item.id); setMobileNav(false); }}><item.icon size={16} />{item.label}</button>)}</nav>
      {selected && <section><div className="eyebrow mb-3">Source explorer</div><label className="relative block mb-3"><Search size={14} className="absolute left-2 top-3 text-zinc-500" /><input className="w-full text-xs pl-7" aria-label="Filter files" placeholder="Filter files…" value={filter} onChange={e => setFilter(e.target.value)} /></label><FileTree files={files.filter(f => f.toLowerCase().includes(filter.toLowerCase()))} onSelect={path => { void openFile(path); setMobileNav(false); }} /></section>}
      <div className="mt-auto pt-5 border-t border-white/10 text-xs muted leading-6">Python repository intelligence<br /><span className="text-violet-300">Read-only investigation tools</span>{selected && <Button variant="ghost" size="sm" className="mt-3 w-full" onClick={removeRepository} disabled={busy || !!activeJob}><Trash2 />Remove repository</Button>}</div>
    </aside>
    <section className="main-panel">
      <header className="panel-header"><div className="flex gap-3 items-center"><Button className="mobile-toggle" variant="ghost" size="icon" aria-label="Open navigation" onClick={() => setMobileNav(true)}><PanelLeft /></Button><h1>{navigation.find(n => n.id === view)?.label}</h1><span className="muted text-xs hidden sm:inline">/ {repository?.name || "No repository"}</span></div><Button variant="ghost" size="icon" aria-label="Open source evidence" onClick={() => setEvidenceOpen(!evidenceOpen)}><PanelRight /></Button></header>
      <div className="content">
        {error && <div className="notice" role="alert">{error}<button className="float-right ml-3" aria-label="Dismiss error" onClick={() => setError("")}><X size={16} /></button></div>}
        {needsLogin ? <form className="empty-state" onSubmit={login}><LockKeyhole className="text-violet-300" /><h2>Your investigation workspace</h2><p>Enter the workspace password to access repositories and AI tools.</p><label className="block mt-6">Workspace password<input className="block w-full mt-2" type="password" required maxLength={256} autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} /></label><Button className="mt-4" type="submit">Sign in</Button></form>
        : showImport || (!selected && !loading) ? <div className="empty-state"><Compass size={34} className="text-violet-300" /><h2>Find your way through the code.</h2><p>Import a public Python repository from GitHub. CodeAtlas indexes its source so you can explore, ask questions, and inspect the evidence.</p><form onSubmit={importRepository} className="mt-7"><label htmlFor="repo-url" className="block text-sm mb-2">Public GitHub repository URL</label><input id="repo-url" className="w-full" type="url" placeholder="https://github.com/psf/requests" required maxLength={250} value={url} onChange={e => setUrl(e.target.value)} disabled={!!activeJob} /><div className="flex items-center gap-3 mt-4"><Button type="submit" disabled={!!activeJob}>{activeJob ? <LoaderCircle className="pulse" /> : <Plus />}{activeJob ? "Indexing repository…" : "Import & index"}</Button>{selected && <Button variant="ghost" type="button" onClick={() => setShowImport(false)}>Cancel</Button>}</div></form>{job && <div className="mt-6 text-sm muted" role="status"><p>{job.status} · {job.progress}%</p><progress className="w-full mt-2 accent-violet-500" max={100} value={job.progress} /></div>}<p className="text-xs mt-6">Python files only. Provider availability and repository limits apply. Imported code is never executed.</p></div>
        : loading ? <p className="muted" role="status">Connecting to your workspace…</p>
        : view === "investigation" ? <>{turns.length === 0 && !busy && <div className="empty-state"><Compass size={32} className="text-violet-300" /><span className="eyebrow block mt-6">Start with a question</span><h2>Less searching.<br />More understanding.</h2><p>Ask about {repository?.name}. Follow the answer into the source, or let the agent investigate the connections.</p><div className="suggestions">{suggested.map(text => <button key={text} onClick={() => void ask(text)}>{text}</button>)}</div></div>}{turns.map((turn, i) => <article className="message" key={i}><div className="question">{turn.question}</div><div className="message-label"><Compass size={16} className="text-violet-300" />CodeAtlas <span className="ml-auto text-xs">{turn.result.duration_seconds !== undefined ? `${turn.result.duration_seconds}s` : mode.toUpperCase()}</span></div><GroundedAnswer text={turn.result.answer} sources={turn.result.sources} onSource={s => void openFile(s.file_path, s.start_line)} /><div className="flex flex-wrap gap-2 mt-4">{turn.result.sources.map(s => <button key={s.id} className="citation" onClick={() => void openFile(s.file_path, s.start_line)}>{s.id} · {s.file_path.split("/").pop()}:{s.start_line}</button>)}</div><p className="muted text-xs mt-3">{turn.result.citations_valid ? "Citation identifiers verified · Check source for factual accuracy." : "Citation identifiers not verified."} · {turn.result.termination_reason}</p>{!!turn.result.trace?.length && <details className="mt-4 text-sm muted"><summary>Tool execution trace · {turn.result.trace.length} events</summary><pre className="text-xs overflow-auto mt-3 p-3 bg-white/3 rounded">{JSON.stringify(turn.result.trace, null, 2)}</pre></details>}</article>)}{busy && <div role="status" className="flex gap-3 text-sm text-violet-300 items-center"><LoaderCircle className="pulse" size={18} />{mode === "agent" ? "Investigating with bounded repository tools…" : "Retrieving source evidence and generating an answer…"}</div>}<div ref={endRef} /></>
        : !overview ? <p className="muted">Loading repository analysis…</p>
        : view === "architecture" ? <Architecture overview={overview} onSelect={p => void openFile(p)} />
        : view === "overview" ? <><p className="eyebrow">Repository intelligence</p><h2 className="section-title">{overview.name}</h2><a className="text-sm text-violet-300 break-all" href={repository?.source} target="_blank" rel="noreferrer">{repository?.source}</a><div className="stat-grid"><div><strong>{overview.python_files}</strong><span>Python files</span></div><div><strong>{overview.symbols}</strong><span>Symbols</span></div><div><strong>{repository?.statistics.chunks ?? "—"}</strong><span>Indexed chunks</span></div></div><h3 className="mb-3">A map of the implementation</h3><p className="muted leading-7">{overview.lines.toLocaleString()} lines across parsed Python source, {overview.test_files} test files, and {overview.edges.length} static import relationships.</p><h3 className="mt-8 mb-3">Imported namespaces</h3><div className="flex flex-wrap gap-2">{Object.keys(overview.external_imports).map(name => <span className="mono text-xs bg-white/5 px-3 py-2 rounded" key={name}>{name}</span>)}</div><p className="muted text-xs mt-5">Import names are not a dependency lockfile. {overview.limitations}</p>{!!overview.failed_files.length && <p className="notice mt-5">Could not parse {overview.failed_files.length} files. Statistics exclude their contents.</p>}</>
        : view === "onboarding" ? <><p className="eyebrow">Your first contribution starts here</p><h2 className="section-title">Get oriented.</h2><p className="muted leading-7">{overview.onboarding.summary}</p><h3 className="mt-8 mb-3">Potential entry points</h3>{overview.onboarding.entrypoints.length ? overview.onboarding.entrypoints.map(p => <button key={p} className="list-row" onClick={() => void openFile(p)}>{p}</button>) : <p className="muted text-sm">No conventional entry-point filenames found.</p>}<h3 className="mt-8 mb-3">Start with the tests</h3>{overview.onboarding.tests.map(p => <button key={p} className="list-row" onClick={() => void openFile(p)}>{p}</button>)}<p className="muted text-xs mt-5">{overview.onboarding.method}</p><div className="suggestions">{suggested.map(text => <button key={text} onClick={() => void ask(text)}>{text}</button>)}</div></>
        : <><p className="eyebrow">Git change analysis</p><h2 className="section-title">Understand the ripple effect.</h2>{impact?.available ? <><p className="muted">Comparing {impact.comparison}</p><h3 className="mt-6">Changed Python files</h3>{impact.changed?.length ? impact.changed.map(p => <button key={p} className="list-row" onClick={() => void openFile(p)}>{p}</button>) : <p className="muted mt-3">No indexed Python files changed in this comparison.</p>}<h3 className="mt-6">Potentially affected modules</h3>{impact.potentially_affected?.map(p => <button key={p} className="list-row" onClick={() => void openFile(p)}>{p}</button>)}<p className="muted text-sm mt-6">{impact.method}</p></> : <p className="muted leading-7 mt-5">{impact?.reason || "Loading commit analysis…"}</p>}</>}
      </div>
      {selected && view === "investigation" && !showImport && !needsLogin && <form className="composer" onSubmit={e => { e.preventDefault(); void ask(); }}><div className="composer-box"><textarea aria-label="Ask about this repository" placeholder={`Ask about ${repository?.name || "this repository"}…`} value={question} maxLength={4000} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void ask(); } }} disabled={busy} /><div className="composer-footer"><select aria-label="Investigation mode" className="text-xs py-1 border-0" value={mode} onChange={e => setMode(e.target.value as "rag" | "agent")} disabled={busy}><option value="rag">Standard RAG</option><option value="agent">Autonomous agent</option></select><Button size="sm" type="submit" disabled={busy || !question.trim()}><Send />Ask</Button></div></div><p className="muted text-xs mt-3 text-center">Grounded in source. AI can make mistakes — inspect the citations.</p></form>}
    </section>
    <aside className={`evidence ${evidenceOpen ? "" : "closed"}`} aria-label="Source evidence"><div className="panel-header"><h2 className="text-sm flex items-center gap-2"><FileCode2 size={16} />Source evidence</h2><Button variant="ghost" size="icon" aria-label="Close source evidence" onClick={() => setEvidenceOpen(false)}><X /></Button></div>{sourceLoading ? <p className="evidence-empty" role="status">Loading source…</p> : source ? <div className="evidence-body"><p className="source-path">{source.file_path}</p><p className="muted text-xs mb-3">Lines {source.start_line}–{source.end_line}</p><SourceViewer content={source.content} start={source.start_line} /><div className="flex justify-between mt-3"><Button variant="ghost" size="sm" disabled={source.start_line === 1} onClick={() => void openFile(source.file_path, Math.max(1, source.start_line - 120))}>Previous lines</Button><Button variant="ghost" size="sm" onClick={() => void openFile(source.file_path, source.end_line + 1)}>Next lines</Button></div><h3 className="eyebrow mt-8 mb-4">Imports</h3>{source.imports?.length ? source.imports.map(name => <p className="mono text-xs muted mb-2" key={name}>{name}</p>) : <p className="muted text-sm">No imports found.</p>}</div> : <div className="evidence-empty"><FileCode2 size={26} className="mx-auto mb-5 text-zinc-600" />The answer is a starting point.<br />The code is the evidence.<p className="mt-4">Select a file or citation to inspect its source and imports here.</p></div>}</aside>
  </main>;
}
