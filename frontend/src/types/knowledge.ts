// Knowledge domain types
export interface KnowledgePoint {
  id: string;
  name: string;
  chapter: number;
  chapterName: string;
  type: "knowledge" | "method";
  content: string;
  formula: string | null;
  relatedTypes: string[];
  prerequisites: string[];
}

export interface KnowledgeNode {
  id: string;
  name: string;
  chapter: number;
  type: "knowledge" | "method";
  mastery?: number;
  x?: number;
  y?: number;
}

export interface KnowledgeEdge {
  source: string;
  target: string;
}

export type KPType = "knowledge" | "method";
