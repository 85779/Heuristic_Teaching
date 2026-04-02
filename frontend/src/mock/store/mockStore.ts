// Mock Store: Zustand store for mock data access
import { create } from "zustand";
import { MOCK_STUDENTS, ALL_STUDENTS, type Student } from "../data/students";
import {
  MOCK_KNOWLEDGE_POINTS,
  KNOWLEDGE_GRAPH_NODES,
  KNOWLEDGE_GRAPH_EDGES,
  type KnowledgePoint,
  type KnowledgeNode,
  type KnowledgeEdge,
} from "../data/knowledge";

interface MockState {
  // Student data
  students: Record<string, Student>;
  allStudents: Student[];
  getStudent: (id: string) => Student | undefined;

  // Knowledge data
  knowledgePoints: Record<string, KnowledgePoint>;
  knowledgeNodes: KnowledgeNode[];
  knowledgeEdges: KnowledgeEdge[];
  getKnowledgePoint: (id: string) => KnowledgePoint | undefined;

  // UI state
  selectedStudentId: string | null;
  setSelectedStudentId: (id: string | null) => void;

  // Demo state
  isDemoRunning: boolean;
  setDemoRunning: (running: boolean) => void;
  currentDemoStep: number;
  setDemoStep: (step: number) => void;
}

export const useMockStore = create<MockState>((set, get) => ({
  // Student data
  students: MOCK_STUDENTS,
  allStudents: ALL_STUDENTS,
  getStudent: (id: string) => get().students[id],

  // Knowledge data
  knowledgePoints: MOCK_KNOWLEDGE_POINTS,
  knowledgeNodes: KNOWLEDGE_GRAPH_NODES,
  knowledgeEdges: KNOWLEDGE_GRAPH_EDGES,
  getKnowledgePoint: (id: string) => get().knowledgePoints[id],

  // UI state
  selectedStudentId: null,
  setSelectedStudentId: (id) => set({ selectedStudentId: id }),

  // Demo state
  isDemoRunning: false,
  setDemoRunning: (running) => set({ isDemoRunning: running }),
  currentDemoStep: 0,
  setDemoStep: (step) => set({ currentDemoStep: step }),
}));
