const B = '/api/v1';
async function req<T>(m: string, p: string, b?: unknown): Promise<T> {
  const r = await fetch(`${B}${p}`, { method: m, headers: b ? { 'Content-Type': 'application/json' } : undefined, body: b ? JSON.stringify(b) : undefined });
  if (!r.ok) { const t = await r.text().catch(() => ''); const e: any = new Error(`${r.status}: ${t}`); e.status = r.status; throw e; }
  return r.json();
}
export const api = { get: <T>(p: string) => req<T>('GET', p), post: <T>(p: string, b?: unknown) => req<T>('POST', p, b) };
export const solving = { solve: (d: any) => api.post<any>('/solving/reference', d) };
export const intervention = { create: (d: any) => api.post<any>('/interventions', d) };
export const recommend = { rec: (d: any) => api.post<any>('/recommendations/recommend', d) };
export const profile = { get: (id: string) => api.get<any>(`/profile/${id}`), hint: (id: string) => api.get<any>(`/profile/${id}/routing-hint`) };
export const teaching = { strategy: (id: string) => api.post<any>('/teaching/strategy', { student_id: id }) };
