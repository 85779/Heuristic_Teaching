// Intervention & routing types
export interface RoutingHint {
  targetModule: number;
  dimension: "RESOURCE" | "METACOGNITIVE";
  level: string;
  weakKpIds: string[];
  weakTopics: string[];
  confidence: number;
  reasoning: string;
}

export interface TopicMastery {
  topic: string;
  kpIds: string[];
  mastery: number;
  correctRate: number;
  hintPenalty: number;
}

export interface InterventionContext {
  studentId: string;
  problemId: string;
  problem: string;
  dimension: "RESOURCE" | "METACOGNITIVE";
  level: string;
  kpIds: string[];
  hintsDelivered: number;
}
