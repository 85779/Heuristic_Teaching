// Mock Data: Knowledge Points
// API: GET /api/knowledge/:kp_id

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

export const MOCK_KNOWLEDGE_POINTS: Record<string, KnowledgePoint> = {
  KP_2_04: {
    id: "KP_2_04",
    name: "根据方程根的分布求参数",
    chapter: 2,
    chapterName: "第2章 一元二次函数、方程与不等式",
    type: "method",
    content:
      "根据一元二次方程在某区间上根的情况求参：若只说有根则参变分离；若规定根的个数则考虑判别式、对称轴、端点值",
    formula: "参变分离：对参数一侧求值域",
    relatedTypes: ["类型Ⅲ", "类型IV"],
    prerequisites: [],
  },
  KP_2_05: {
    id: "KP_2_05",
    name: "韦达定理",
    chapter: 2,
    chapterName: "第2章 一元二次函数、方程与不等式",
    type: "method",
    content:
      "一元二次方程ax²+bx+c=0的两根x₁、x₂满足：x₁+x₂=-b/a，x₁x₂=c/a。常用于整体代入求值或求参数",
    formula: "x₁+x₂=-b/a；x₁x₂=c/a",
    relatedTypes: ["类型Ⅲ"],
    prerequisites: ["KP_2_04"],
  },
  KP_3_26: {
    id: "KP_3_26",
    name: "函数的概念与定义域",
    chapter: 3,
    chapterName: "第3章 函数与导数",
    type: "knowledge",
    content:
      "函数是描述两个变量之间对应关系的数学模型，定义域是使表达式有意义的自变量取值集合",
    formula: null,
    relatedTypes: ["类型Ⅰ"],
    prerequisites: [],
  },
  KP_3_27: {
    id: "KP_3_27",
    name: "函数单调性的判断",
    chapter: 3,
    chapterName: "第3章 函数与导数",
    type: "method",
    content: "利用导数判断函数单调性的步骤：①求导 ②解导数不等式 ③确定单调区间",
    formula:
      "f'(x)>0 则 f(x) 在区间上单调递增；f'(x)<0 则 f(x) 在区间上单调递减",
    relatedTypes: ["类型Ⅲ"],
    prerequisites: ["KP_3_32"],
  },
  KP_3_32: {
    id: "KP_3_32",
    name: "导数基础与计算",
    chapter: 3,
    chapterName: "第3章 函数与导数",
    type: "knowledge",
    content:
      "导数描述函数在某一点处的瞬时变化率，基本初等函数的导数公式和求导法则是基础",
    formula: "(xⁿ)' = nxⁿ⁻¹；(sinx)' = cosx；(cosx)' = -sinx",
    relatedTypes: ["类型Ⅰ", "类型Ⅱ"],
    prerequisites: ["KP_3_26"],
  },
  KP_4_07: {
    id: "KP_4_07",
    name: "正弦型函数的图象与性质",
    chapter: 4,
    chapterName: "第4章 三角函数",
    type: "method",
    content:
      "正弦型函数y=Asin(ωx+φ)的图象变换：振幅A决定上下伸缩，周期T=2π/|ω|决定水平伸缩，相位φ决定左右平移",
    formula: "T = 2π/|ω|；A 影响振幅",
    relatedTypes: ["类型1", "类型2", "类型3"],
    prerequisites: ["KP_4_03"],
  },
  KP_4_08: {
    id: "KP_4_08",
    name: "三角函数的图象变换",
    chapter: 4,
    chapterName: "第4章 三角函数",
    type: "method",
    content:
      "三角函数图象变换规律：左加右减（x方向），上加下减（y方向）；先平移后伸缩与先伸缩后平移结果不同",
    formula: "平移：y=sinx → y=sin(x+φ)；伸缩：y=sinx → y=sin(ωx)",
    relatedTypes: ["类型1", "类型2", "类型3"],
    prerequisites: ["KP_4_07"],
  },
  KP_5_01: {
    id: "KP_5_01",
    name: "正弦定理",
    chapter: 5,
    chapterName: "第5章 解三角形",
    type: "knowledge",
    content:
      "正弦定理：a/sinA = b/sinB = c/sinC = 2R，用于已知两边和其中一边对角求其他边或角",
    formula: "a/sinA = b/sinB = c/sinC = 2R",
    relatedTypes: ["类型Ⅰ"],
    prerequisites: [],
  },
  KP_6_02: {
    id: "KP_6_02",
    name: "向量的坐标运算",
    chapter: 6,
    chapterName: "第6章 平面向量",
    type: "method",
    content: "向量坐标运算：加法、减法、数乘、数量积的坐标计算公式",
    formula: "a⃗=(x₁,y₁)，b⃗=(x₂,y₂) → a⃗+b⃗=(x₁+x₂,y₁+y₂)；a⃗·b⃗=x₁x₂+y₁y₂",
    relatedTypes: ["类型1", "类型2"],
    prerequisites: ["KP_6_01"],
  },
  KP_7_02: {
    id: "KP_7_02",
    name: "复数的四则运算",
    chapter: 7,
    chapterName: "第7章 复数",
    type: "method",
    content:
      "复数代数形式z=a+bi的四则运算：加减为实部虚部分别运算，乘法满足分配律，除法需乘共轭复数",
    formula: "(a+bi)(c+di) = (ac-bd) + (ad+bc)i",
    relatedTypes: ["类型Ⅰ"],
    prerequisites: ["KP_7_01"],
  },
  KP_8_01: {
    id: "KP_8_01",
    name: "等差数列的通项公式",
    chapter: 8,
    chapterName: "第8章 数列",
    type: "method",
    content: "等差数列通项：aₙ = a₁ + (n-1)d，由首项和公差唯一确定",
    formula: "aₙ = a₁ + (n-1)d",
    relatedTypes: ["类型Ⅰ"],
    prerequisites: [],
  },
};

// Knowledge graph structure for visualization
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

export const KNOWLEDGE_GRAPH_NODES: KnowledgeNode[] = [
  {
    id: "KP_2_01",
    name: "不等式基本性质",
    chapter: 2,
    type: "knowledge",
    mastery: 0.85,
  },
  {
    id: "KP_2_02",
    name: "一元二次不等式解法",
    chapter: 2,
    type: "method",
    mastery: 0.72,
  },
  {
    id: "KP_2_04",
    name: "根的分布与参数",
    chapter: 2,
    type: "method",
    mastery: 0.68,
  },
  {
    id: "KP_2_05",
    name: "韦达定理",
    chapter: 2,
    type: "method",
    mastery: 0.55,
  },
  {
    id: "KP_2_07",
    name: "基本不等式",
    chapter: 2,
    type: "method",
    mastery: 0.62,
  },
  {
    id: "KP_2_09",
    name: "柯西不等式",
    chapter: 2,
    type: "knowledge",
    mastery: 0.45,
  },
  {
    id: "KP_3_26",
    name: "函数概念",
    chapter: 3,
    type: "knowledge",
    mastery: 0.78,
  },
  {
    id: "KP_3_27",
    name: "单调性判断",
    chapter: 3,
    type: "method",
    mastery: 0.42,
  },
  {
    id: "KP_3_32",
    name: "导数基础",
    chapter: 3,
    type: "knowledge",
    mastery: 0.65,
  },
  {
    id: "KP_4_07",
    name: "正弦型函数",
    chapter: 4,
    type: "method",
    mastery: 0.28,
  },
  {
    id: "KP_4_08",
    name: "图象变换",
    chapter: 4,
    type: "method",
    mastery: 0.35,
  },
  {
    id: "KP_5_01",
    name: "正弦定理",
    chapter: 5,
    type: "knowledge",
    mastery: 0.72,
  },
];

export const KNOWLEDGE_GRAPH_EDGES: KnowledgeEdge[] = [
  { source: "KP_2_01", target: "KP_2_02" },
  { source: "KP_2_02", target: "KP_2_04" },
  { source: "KP_2_04", target: "KP_2_05" },
  { source: "KP_2_05", target: "KP_2_07" },
  { source: "KP_2_02", target: "KP_2_07" },
  { source: "KP_3_26", target: "KP_3_32" },
  { source: "KP_3_32", target: "KP_3_27" },
  { source: "KP_4_07", target: "KP_4_08" },
];
