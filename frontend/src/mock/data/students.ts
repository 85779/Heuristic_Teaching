// Mock Data: Students
// API: GET /api/students/:id

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

export const MOCK_STUDENTS: Record<string, Student> = {
  student_001: {
    id: "student_001",
    name: "李明",
    avatar: "👨‍🎓",
    grade: "高三（1）班",
    activeDays: 12,
    totalProblems: 47,
    dimensionRatio: 0.65,
    ratioTrend: "falling",
    trendConfidence: 0.82,
    kpMastery: {
      KP_2_04: { mastery: 0.85, attempt: 5, correct: 4, totalHints: 3 },
      KP_3_27: { mastery: 0.42, attempt: 6, correct: 2, totalHints: 8 },
      KP_4_07: { mastery: 0.28, attempt: 3, correct: 0, totalHints: 9 },
      KP_4_08: { mastery: 0.35, attempt: 4, correct: 1, totalHints: 7 },
      KP_5_01: { mastery: 0.78, attempt: 3, correct: 2, totalHints: 2 },
      KP_3_32: { mastery: 0.55, attempt: 4, correct: 2, totalHints: 4 },
    },
    weakKpIds: ["KP_4_07", "KP_4_08", "KP_3_27"],
    weakTopics: ["正弦型函数", "三角函数图象变换", "函数单调性"],
    interventionHistory: [
      {
        id: "int_001",
        problemId: "prob_001",
        problem: "判断f(x)=x²+2x+1的单调性",
        dimension: "RESOURCE",
        level: "R2",
        kpIds: ["KP_3_27"],
        outcome: "SOLVED",
        timestamp: "2026-04-01T14:30:00Z",
      },
      {
        id: "int_002",
        problemId: "prob_002",
        problem: "三角函数图象变换",
        dimension: "METACOGNITIVE",
        level: "M3",
        kpIds: ["KP_4_08"],
        outcome: "ESCALATED",
        timestamp: "2026-04-01T10:15:00Z",
      },
      {
        id: "int_003",
        problemId: "prob_003",
        problem: "向量坐标运算",
        dimension: "RESOURCE",
        level: "R1",
        kpIds: ["KP_6_02"],
        outcome: "SOLVED",
        timestamp: "2026-03-31T16:42:00Z",
      },
      {
        id: "int_004",
        problemId: "prob_004",
        problem: "等差数列通项公式",
        dimension: "RESOURCE",
        level: "R2",
        kpIds: ["KP_8_01"],
        outcome: "SOLVED",
        timestamp: "2026-03-31T11:20:00Z",
      },
      {
        id: "int_005",
        problemId: "prob_005",
        problem: "复数代数运算",
        dimension: "RESOURCE",
        level: "R1",
        kpIds: ["KP_7_02"],
        outcome: "SOLVED",
        timestamp: "2026-03-30T09:00:00Z",
      },
    ],
    totalInterventions: 23,
    totalSolved: 18,
    totalEscalation: 3,
    status: "normal",
  },

  student_002: {
    id: "student_002",
    name: "张伟",
    avatar: "👨‍🎓",
    grade: "高三（1）班",
    activeDays: 8,
    totalProblems: 19,
    dimensionRatio: 0.89,
    ratioTrend: "stable",
    trendConfidence: 0.65,
    kpMastery: {
      KP_2_04: { mastery: 0.22, attempt: 8, correct: 1, totalHints: 15 },
      KP_2_05: { mastery: 0.18, attempt: 6, correct: 0, totalHints: 12 },
      KP_2_07: { mastery: 0.31, attempt: 5, correct: 1, totalHints: 9 },
      KP_3_27: { mastery: 0.15, attempt: 4, correct: 0, totalHints: 10 },
    },
    weakKpIds: ["KP_2_04", "KP_2_05", "KP_2_07", "KP_3_27"],
    weakTopics: ["不等式基础", "韦达定理", "基本不等式", "函数单调性"],
    interventionHistory: [
      {
        id: "int_101",
        problemId: "prob_006",
        problem: "一元二次不等式求解",
        dimension: "RESOURCE",
        level: "R3",
        kpIds: ["KP_2_04"],
        outcome: "ESCALATED",
        timestamp: "2026-04-01T15:00:00Z",
      },
      {
        id: "int_102",
        problemId: "prob_007",
        problem: "韦达定理应用",
        dimension: "RESOURCE",
        level: "R4",
        kpIds: ["KP_2_05"],
        outcome: "TERMINATED",
        timestamp: "2026-04-01T11:30:00Z",
      },
    ],
    totalInterventions: 12,
    totalSolved: 4,
    totalEscalation: 6,
    status: "warning",
  },

  student_003: {
    id: "student_003",
    name: "王芳",
    avatar: "👩‍🎓",
    grade: "高三（1）班",
    activeDays: 5,
    totalProblems: 8,
    dimensionRatio: 0.35,
    ratioTrend: "rising",
    trendConfidence: 0.45,
    kpMastery: {
      KP_3_32: { mastery: 0.72, attempt: 2, correct: 1, totalHints: 2 },
      KP_4_09: { mastery: 0.58, attempt: 3, correct: 1, totalHints: 4 },
    },
    weakKpIds: [],
    weakTopics: [],
    interventionHistory: [
      {
        id: "int_201",
        problemId: "prob_008",
        problem: "导数综合应用",
        dimension: "METACOGNITIVE",
        level: "M2",
        kpIds: ["KP_3_32"],
        outcome: "ESCALATED",
        timestamp: "2026-04-01T09:00:00Z",
      },
    ],
    totalInterventions: 5,
    totalSolved: 3,
    totalEscalation: 1,
    status: "attention",
  },

  student_004: {
    id: "student_004",
    name: "刘洋",
    avatar: "👨‍🎓",
    grade: "高三（1）班",
    activeDays: 15,
    totalProblems: 62,
    dimensionRatio: 0.52,
    ratioTrend: "stable",
    trendConfidence: 0.78,
    kpMastery: {
      KP_2_04: { mastery: 0.88, attempt: 7, correct: 6, totalHints: 2 },
      KP_3_27: { mastery: 0.75, attempt: 8, correct: 5, totalHints: 4 },
      KP_5_01: { mastery: 0.82, attempt: 5, correct: 4, totalHints: 2 },
    },
    weakKpIds: [],
    weakTopics: [],
    interventionHistory: [],
    totalInterventions: 15,
    totalSolved: 12,
    totalEscalation: 1,
    status: "normal",
  },

  student_005: {
    id: "student_005",
    name: "陈静",
    avatar: "👩‍🎓",
    grade: "高三（1）班",
    activeDays: 10,
    totalProblems: 38,
    dimensionRatio: 0.71,
    ratioTrend: "falling",
    trendConfidence: 0.7,
    kpMastery: {
      KP_4_07: { mastery: 0.38, attempt: 5, correct: 1, totalHints: 9 },
      KP_4_08: { mastery: 0.45, attempt: 4, correct: 1, totalHints: 6 },
    },
    weakKpIds: ["KP_4_07", "KP_4_08"],
    weakTopics: ["正弦型函数", "三角函数图象变换"],
    interventionHistory: [],
    totalInterventions: 18,
    totalSolved: 12,
    totalEscalation: 4,
    status: "normal",
  },
};

export const ALL_STUDENTS = Object.values(MOCK_STUDENTS);
