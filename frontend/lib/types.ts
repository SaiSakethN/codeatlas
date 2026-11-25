export type Repository = { id: string; name: string; source: string; statistics: { chunks?: number } };
export type Job = { id: string; status: "queued" | "indexing" | "completed" | "failed"; progress: number; repository_id?: string; error?: string };
export type Source = { id?: string; file_path: string; start_line: number; end_line: number; content: string };
export type Answer = { answer: string; sources: Source[]; citations_valid: boolean; termination_reason: string; trace?: Record<string, unknown>[]; duration_seconds?: number };
export type Overview = {
  name: string; python_files: number; symbols: number; lines: number; test_files: number;
  nodes: { id: string; label: string; symbols: number; lines: number }[];
  edges: { source: string; target: string }[]; external_imports: Record<string, number>;
  onboarding: { summary: string; entrypoints: string[]; tests: string[]; suggested_questions: string[]; method: string };
  limitations: string; failed_files: string[];
};
export type Impact = { available: boolean; reason?: string; comparison?: string; changed?: string[]; potentially_affected?: string[]; method?: string };
