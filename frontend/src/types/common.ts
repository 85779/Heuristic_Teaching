export interface Session {
  session_id: string;
  status: "active" | "paused" | "completed";
  created_at: string;
  current_phase?: string;
}

export interface Problem {
  content: string;
  type?: string;
  difficulty?: string;
}

export interface SolutionStep {
  step_name: string;
  content: string;
  key_insights: string[];
}

export interface SolutionThread {
  problem: Problem;
  steps: SolutionStep[];
  complete: boolean;
}

export interface InterventionHint {
  level: number;
  content: string;
  delivered_at: string;
}
