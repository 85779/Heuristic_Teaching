// Student domain types
export interface KPMastery {
  mastery: number;
  attempt: number;
  correct: number;
  totalHints: number;
}

export interface InterventionRecord {
  id: string;
  problemId: string;
  problem: string;
  dimension: "RESOURCE" | "METACOGNITIVE";
  level: string;
  kpIds: string[];
  outcome: "SOLVED" | "ESCALATED" | "TERMINATED";
  timestamp: string;
}

export interface Student {
  id: string;
  name: string;
  avatar: string;
  grade: string;
  activeDays: number;
  totalProblems: number;
  dimensionRatio: number;
  ratioTrend: "rising" | "falling" | "stable";
  trendConfidence: number;
  kpMastery: Record<string, KPMastery>;
  weakKpIds: string[];
  weakTopics: string[];
  interventionHistory: InterventionRecord[];
  totalInterventions: number;
  totalSolved: number;
  totalEscalation: number;
  status: "normal" | "warning" | "attention";
}

export type StudentStatus = "normal" | "warning" | "attention";
export type Dimension = "RESOURCE" | "METACOGNITIVE";
export type InterventionOutcome = "SOLVED" | "ESCALATED" | "TERMINATED";
