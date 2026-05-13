import { useAuthStore } from "@/store/authStore";

const DEFAULT_API_BASE = "https://web-production-d8369.up.railway.app";

export const API_BASE = import.meta.env.VITE_API_BASE ?? DEFAULT_API_BASE;

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = true, headers, ...rest } = options;
  const finalHeaders: Record<string, string> = {
    ...(headers as Record<string, string> | undefined),
  };
  if (auth) {
    const token = useAuthStore.getState().token;
    if (token) finalHeaders["Authorization"] = `Bearer ${token}`;
  }
  if (rest.body && !(rest.body instanceof FormData) && !finalHeaders["Content-Type"]) {
    finalHeaders["Content-Type"] = "application/json";
  }
  const res = await fetch(`${API_BASE}${path}`, { ...rest, headers: finalHeaders });
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      msg = data.detail || data.message || msg;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export interface LoginResponse {
  access_token: string;
  token_type?: string;
}

export interface MeResponse {
  id: number;
  email: string;
  has_resume: boolean;
}

export interface Job {
  title: string;
  company: string;
  location: string;
  url: string;
  score: number;
  final_score: number;
  skills_match_pct: number;
  missing_skills: string[];
  seniority_fit: "good fit" | "underqualified" | "overqualified";
  reason: string;
  scraped_at: string;
  is_new: boolean;
}

export interface JobsResponse {
  total_scraped: number;
  returned: number;
  duration_seconds: number;
  jobs: Job[];
}

export interface PipelineStatus {
  status: "success" | "failed" | string;
  jobs_scraped: number;
  new_jobs: number;
  emails_sent: number;
  duration_seconds: number;
  timestamp: string;
}

export const api = {
  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      auth: false,
    }),
  register: (email: string, password: string) =>
    request<unknown>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
      auth: false,
    }),
  me: () => request<MeResponse>("/auth/me", { method: "GET" }),
  uploadResume: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<unknown>("/auth/upload-resume", { method: "POST", body: fd });
  },
  fetchJobs: (pages = 2) => request<JobsResponse>(`/jobs?pages=${pages}`, { method: "GET" }),
  sendDigest: () =>
    request<unknown>("/send-digest", {
      method: "POST",
      body: JSON.stringify({ recipient_email: "" }),
    }),
  runPipeline: () => request<unknown>("/run-pipeline", { method: "POST" }),
  pipelineStatus: () =>
    request<PipelineStatus>("/pipeline/status", { method: "GET" }),
};