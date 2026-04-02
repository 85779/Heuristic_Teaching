// DemoPage: Interactive demo showing AI tutoring process with step-by-step problem solving - Light Theme
import React, { useState, useCallback, useEffect, useRef } from "react";
import { Outlet } from "react-router-dom";
import { StepIndicator } from "../components/shared/StepIndicator";
import { KPBadge } from "../components/shared/KPBadge";

// Demo steps configuration
const DEMO_STEPS = [
  { label: "选择学生", description: "选择案例" },
  { label: "学生解题", description: "分步作答" },
  { label: "AI干预", description: "断点检测" },
  { label: "解题完成", description: "问题解决" },
];

// Problem definition
const PROBLEM = {
  content: "求函数 f(x)=x²+2x+1 的最小值",
  latex: "f(x) = x^2 + 2x + 1",
};

// Route A: 配方法 (Completing Square)
const ROUTE_A_STEPS = [
  { id: 1, content: "f(x) = x² + 2x + 1", hint: "写出原函数表达式" },
  { id: 2, content: "f(x) = (x+1)²", hint: "配方：x²+2x+1 = (x+1)²" },
  { id: 3, content: "因为 (x+1)² ≥ 0", hint: "利用平方的非负性" },
  { id: 4, content: "当 x = -1 时，最小值 = 0", hint: "找到取得最小值的x" },
];

// Route B: 求导法 (Derivative Method)
const ROUTE_B_STEPS = [
  { id: 1, content: "f'(x) = 2x + 2", hint: "求导数" },
  { id: 2, content: "令 f'(x) = 0 → 2x + 2 = 0", hint: "令导数为零找极值点" },
  { id: 3, content: "x = -1", hint: "解方程" },
  { id: 4, content: "f(-1) = 0，最小值 = 0", hint: "代入原函数求值" },
];

// Reference solution
const REFERENCE_SOLUTION = {
  answer: "最小值 = 0，当 x = -1",
  x: -1,
  minValue: 0,
};

// Breakpoint types
type BreakpointType = "方向错误" | "卡在某步" | "写一半";

// Student scenario with predefined breakpoint
interface StudentScenario {
  id: string;
  name: string;
  avatar: string;
  route: "A" | "B";
  // Steps student will try to input (with potential error)
  studentInputs: (string | { wrong: string; hint: string })[];
  // When to trigger breakpoint
  breakpointAt: number;
  // Type of breakpoint
  breakpointType: BreakpointType;
  // Hint content for this breakpoint
  breakpointHint: string;
  // Reference to which route step they're stuck on
  stuckOnStep: number;
}

// Predefined student scenarios
const STUDENT_SCENARIOS: StudentScenario[] = [
  {
    id: "student_wrong_direction",
    name: "李明",
    avatar: "👨‍🎓",
    route: "A",
    studentInputs: [
      "f(x) = x² + 2x + 1",
      {
        wrong: "f(x) = x² - 1",
        hint: "配方有误，检查一下 x²+2x+1 应该怎么配方",
      },
      { wrong: "因为 x²≥0", hint: "注意：x²+2x+1 不是简单的 x²，你需要先配方" },
    ],
    breakpointAt: 1,
    breakpointType: "方向错误",
    breakpointHint:
      "你用了错误的配方变形。正确做法是：x²+2x+1 = (x+1)²，而不是 x²-1。配方时，要加上一次项系数一半的平方。",
    stuckOnStep: 1,
  },
  {
    id: "student_stuck_next",
    name: "张伟",
    avatar: "👨‍🎓",
    route: "B",
    studentInputs: [
      "f'(x) = 2x + 2",
      "令 f'(x) = 0 → 2x + 2 = 0",
      // Stuck here - can't solve
      { wrong: "...", hint: "接下来要解方程 2x+2=0，两边同时除以2即可" },
    ],
    breakpointAt: 2,
    breakpointType: "卡在某步",
    breakpointHint:
      "你已经列出了方程 2x+2=0，接下来需要解这个方程。提示：两边同时除以2，得到 x+1=0，然后移项得到 x=-1。",
    stuckOnStep: 2,
  },
  {
    id: "student_half_way",
    name: "王芳",
    avatar: "👩‍🎓",
    route: "A",
    studentInputs: [
      "f(x) = x² + 2x + 1",
      // Half way - gives up
      {
        wrong: "最小值是0？",
        hint: "你是怎么得出最小值是0的？让我们一步步来。先把函数配方。",
      },
    ],
    breakpointAt: 1,
    breakpointType: "写一半",
    breakpointHint:
      "不要着急猜测答案！正确的思路是：1）先把函数配方成 (x+1)²，2）因为 (x+1)² ≥ 0，所以最小值在 x=-1 时取得，为0。",
    stuckOnStep: 1,
  },
];

// AI Detection states
type AIDetectionState =
  | "idle"
  | "analyzing"
  | "stuck"
  | "correct"
  | "breakpoint";

interface AIReasoning {
  text: string;
  type?: "info" | "success" | "warning" | "hint" | "breakpoint";
}

export const DemoPage: React.FC = () => {
  // Scenario selection
  const [selectedScenario, setSelectedScenario] =
    useState<StudentScenario | null>(null);

  // Student solving state
  const [studentSteps, setStudentSteps] = useState<string[]>([]);
  const [currentStepInput, setCurrentStepInput] = useState("");
  const [hasError, setHasError] = useState(false);

  // AI state
  const [aiReasoning, setAiReasoning] = useState<AIReasoning[]>([]);
  const [detectionState, setDetectionState] =
    useState<AIDetectionState>("idle");
  const [showHint, setShowHint] = useState(false);
  const [hintContent, setHintContent] = useState("");
  const [breakpointType, setBreakpointType] = useState<BreakpointType | null>(
    null,
  );

  // Progress
  const [currentStep, setCurrentStep] = useState(0);

  // Auto-play state
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const autoPlayRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Get current route steps
  const routeSteps =
    selectedScenario?.route === "A"
      ? ROUTE_A_STEPS
      : selectedScenario?.route === "B"
        ? ROUTE_B_STEPS
        : [];

  // Handle auto-play with scenario
  const handleAutoPlay = useCallback((scenario: StudentScenario) => {
    // Reset first
    setSelectedScenario(scenario);
    setStudentSteps([]);
    setAiReasoning([]);
    setCurrentStep(0);
    setIsAutoPlaying(true);

    setTimeout(() => {
      setCurrentStep(1);
      setAiReasoning([
        {
          text: `👨‍🎓 学生：${scenario.name}`,
          type: "info",
        },
        {
          text: `📝 选择解法：${scenario.route === "A" ? "配方法" : "求导法"}`,
          type: "info",
        },
        { text: "🔍 开始分析解题步骤...", type: "info" },
      ]);
    }, 300);
  }, []);

  const handleStopAutoPlay = useCallback(() => {
    setIsAutoPlaying(false);
    if (autoPlayRef.current) {
      clearTimeout(autoPlayRef.current);
    }
  }, []);

  const handleReset = useCallback(() => {
    setSelectedScenario(null);
    setStudentSteps([]);
    setCurrentStepInput("");
    setAiReasoning([]);
    setDetectionState("idle");
    setShowHint(false);
    setHintContent("");
    setCurrentStep(0);
    setIsAutoPlaying(false);
    setBreakpointType(null);
    if (autoPlayRef.current) {
      clearTimeout(autoPlayRef.current);
    }
  }, []);

  // Auto-play effect
  useEffect(() => {
    if (!isAutoPlaying || !selectedScenario) return;

    const scenario = selectedScenario;
    let currentIndex = studentSteps.length;

    const playNextStep = () => {
      // Check if we've reached the breakpoint
      if (currentIndex === scenario.breakpointAt) {
        // Show the wrong answer at breakpoint
        const breakpointData = scenario.studentInputs[currentIndex];
        if (typeof breakpointData === "object") {
          setCurrentStepInput(breakpointData.wrong);
          setHasError(true);

          setAiReasoning((prev) => [
            ...prev,
            {
              text: `⚠️ 步骤${currentIndex + 1}: ${breakpointData.wrong}`,
              type: "warning",
            },
          ]);

          // Trigger breakpoint after delay
          autoPlayRef.current = setTimeout(() => {
            setDetectionState("breakpoint");
            setBreakpointType(scenario.breakpointType);
            setShowHint(true);
            setHintContent(breakpointData.hint);
            setCurrentStep(2);

            let breakpointLabel = "";
            if (scenario.breakpointType === "方向错误") {
              breakpointLabel = "🚨 检测到：方向错误";
            } else if (scenario.breakpointType === "卡在某步") {
              breakpointLabel = "⏸ 检测到：卡在某步无法继续";
            } else {
              breakpointLabel = "📝 检测到：写了一半停滞";
            }

            setAiReasoning((prev) => [
              ...prev,
              { text: breakpointLabel, type: "breakpoint" },
              { text: `💡 系统提示：${breakpointData.hint}`, type: "hint" },
            ]);

            setCurrentStepInput("");
          }, 1500);

          return;
        }
      }

      // If we've shown the hint, continue to complete solution after a delay
      if (hasError && currentIndex >= scenario.breakpointAt) {
        autoPlayRef.current = setTimeout(() => {
          // Continue with correct steps to finish
          const correctSteps =
            scenario.route === "A" ? ROUTE_A_STEPS : ROUTE_B_STEPS;

          // Add remaining correct steps
          const remainingSteps = correctSteps.slice(currentIndex);
          let delay = 0;

          remainingSteps.forEach((step, i) => {
            delay += 1000;
            autoPlayRef.current = setTimeout(() => {
              setStudentSteps((prev) => [...prev, step.content]);
              setAiReasoning((prev) => [
                ...prev,
                {
                  text: `✓ 步骤${currentIndex + i + 1}: ${step.content} - 正确`,
                  type: "success",
                },
              ]);

              if (i === remainingSteps.length - 1) {
                // Complete
                setDetectionState("correct");
                setCurrentStep(3);
                setAiReasoning((prev) => [
                  ...prev,
                  { text: "🎉 所有步骤完成！", type: "success" },
                  {
                    text: `📌 最终答案：${REFERENCE_SOLUTION.answer}`,
                    type: "success",
                  },
                  { text: "✅ 与参考解法结论一致", type: "success" },
                ]);
                setIsAutoPlaying(false);
              }
            }, delay);
          });
        }, 2000);
        return;
      }

      // Normal step - show correct input
      if (currentIndex < scenario.studentInputs.length) {
        const input = scenario.studentInputs[currentIndex];
        if (typeof input === "string") {
          setCurrentStepInput(input);
          setHasError(false);

          setAiReasoning((prev) => [
            ...prev,
            {
              text: `✓ 步骤${currentIndex + 1}: ${input} - 正确`,
              type: "success",
            },
          ]);

          const newSteps = [...studentSteps, input];
          setStudentSteps(newSteps);
          currentIndex++;
        }
      }

      setCurrentStepInput("");

      // Schedule next step
      if (currentIndex < scenario.studentInputs.length && isAutoPlaying) {
        autoPlayRef.current = setTimeout(playNextStep, 1200);
      }
    };

    autoPlayRef.current = setTimeout(playNextStep, 1000);

    return () => {
      if (autoPlayRef.current) {
        clearTimeout(autoPlayRef.current);
      }
    };
  }, [isAutoPlaying, selectedScenario, studentSteps.length, hasError]);

  // Auto-switch to step 3 when complete
  useEffect(() => {
    if (detectionState === "correct") {
      setCurrentStep(3);
    }
  }, [detectionState]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="max-w-6xl mx-auto p-4 md:p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
              <span className="text-xl">🔬</span>
            </div>
            <h2 className="text-2xl font-bold text-slate-800">智能教学演示</h2>
          </div>
          <div className="flex items-center gap-3">
            {isAutoPlaying ? (
              <button
                onClick={handleStopAutoPlay}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm shadow-sm"
              >
                ⏹ 停止
              </button>
            ) : (
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-white text-slate-600 rounded-lg hover:bg-slate-100 transition-colors text-sm border border-slate-200 shadow-sm"
              >
                重新开始
              </button>
            )}
          </div>
        </div>

        {/* Step Indicator */}
        <div className="mb-6 p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
          <StepIndicator
            steps={DEMO_STEPS}
            currentStep={currentStep}
            orientation="horizontal"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid md:grid-cols-2 gap-4 mb-6">
          {/* Left Panel: Student View */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
              <h3 className="text-slate-800 font-semibold flex items-center gap-2">
                <span>👨‍🎓</span> 学生界面
              </h3>
            </div>
            <div className="p-5">
              {/* Problem */}
              <div className="mb-5">
                <p className="text-xs text-slate-500 mb-2">题目：</p>
                <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                  <p className="text-slate-800 font-medium leading-relaxed">
                    {PROBLEM.content}
                  </p>
                </div>
              </div>

              {/* Scenario Selection */}
              {selectedScenario === null && (
                <div className="space-y-3">
                  <p className="text-xs text-slate-500">选择学生案例：</p>
                  <div className="space-y-2">
                    {STUDENT_SCENARIOS.map((scenario) => (
                      <button
                        key={scenario.id}
                        onClick={() => handleAutoPlay(scenario)}
                        className="w-full p-4 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 hover:border-blue-300 hover:shadow-md transition-all text-left"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{scenario.avatar}</span>
                          <div className="flex-1">
                            <div className="text-slate-800 font-semibold">
                              {scenario.name}
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              {scenario.route === "A"
                                ? "📐 配方法"
                                : "📊 求导法"}{" "}
                              ·
                              <span
                                className={
                                  scenario.breakpointType === "方向错误"
                                    ? "text-red-500"
                                    : scenario.breakpointType === "卡在某步"
                                      ? "text-amber-500"
                                      : "text-blue-500"
                                }
                              >
                                {scenario.breakpointType}
                              </span>
                            </div>
                          </div>
                          <span className="text-blue-500">▶</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Selected Scenario Indicator */}
              {selectedScenario !== null && (
                <div className="mb-4">
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm bg-slate-100 border border-slate-200">
                    <span>{selectedScenario.avatar}</span>
                    <span className="text-slate-800">
                      {selectedScenario.name}
                    </span>
                    <span className="text-slate-400">·</span>
                    <span
                      className={
                        selectedScenario.route === "A"
                          ? "text-purple-600"
                          : "text-blue-600"
                      }
                    >
                      {selectedScenario.route === "A" ? "配方法" : "求导法"}
                    </span>
                    <button
                      onClick={handleReset}
                      className="ml-2 text-xs text-slate-400 hover:text-slate-600"
                    >
                      切换
                    </button>
                  </div>
                </div>
              )}

              {/* Student Steps */}
              {selectedScenario !== null && (
                <div className="space-y-3">
                  <p className="text-xs text-slate-500">
                    学生作答（{studentSteps.length}/{routeSteps.length} 步）：
                  </p>

                  {/* Completed steps */}
                  {studentSteps.map((step, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-lg border bg-emerald-50 border-emerald-200"
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs">
                          ✓
                        </span>
                        <span className="font-mono text-sm text-slate-700">
                          {index + 1}. {step}
                        </span>
                      </div>
                    </div>
                  ))}

                  {/* Error step */}
                  {hasError && currentStepInput && (
                    <div
                      className={`p-3 rounded-lg border ${
                        detectionState === "breakpoint"
                          ? "bg-amber-50 border-amber-200"
                          : "bg-red-50 border-red-200"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-red-500 text-white flex items-center justify-center text-xs">
                          ✗
                        </span>
                        <span className="font-mono text-sm text-red-600">
                          {studentSteps.length + 1}. {currentStepInput}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Current step indicator */}
                  {!hasError &&
                    studentSteps.length < routeSteps.length &&
                    currentStep < 3 && (
                      <div className="p-3 rounded-lg border border-slate-200 bg-slate-50">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-slate-300 text-slate-600 flex items-center justify-center text-xs animate-pulse">
                            {studentSteps.length + 1}
                          </span>
                          <span className="font-mono text-sm text-slate-500">
                            {isAutoPlaying ? "自动作答中..." : "等待输入..."}
                          </span>
                        </div>
                      </div>
                    )}

                  {/* Breakpoint indicator */}
                  {detectionState === "breakpoint" && (
                    <div className="p-3 rounded-lg border border-amber-200 bg-amber-50">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-amber-500 text-white flex items-center justify-center text-xs animate-pulse">
                          !
                        </span>
                        <span className="text-sm text-amber-700">
                          {breakpointType}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel: AI Reasoning */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
              <h3 className="text-slate-800 font-semibold flex items-center gap-2">
                <span>🤖</span> AI推理过程
              </h3>
            </div>
            <div className="p-5 h-[400px] overflow-auto">
              {selectedScenario === null ? (
                <div className="space-y-2">
                  <p className="text-slate-400">
                    请选择一个学生案例开始演示...
                  </p>
                </div>
              ) : (
                <div className="space-y-1 font-mono text-sm">
                  {aiReasoning.map((reasoning, index) => (
                    <p
                      key={index}
                      className={`leading-relaxed ${
                        reasoning.type === "success"
                          ? "text-emerald-600"
                          : reasoning.type === "warning"
                            ? "text-red-600"
                            : reasoning.type === "hint"
                              ? "text-blue-600"
                              : reasoning.type === "breakpoint"
                                ? "text-amber-600 font-semibold"
                                : "text-slate-600"
                      }`}
                    >
                      {reasoning.text}
                    </p>
                  ))}
                  {isAutoPlaying && (
                    <p className="text-slate-400 animate-pulse">
                      <span className="inline-block w-2 h-4 bg-blue-500 ml-1" />
                    </p>
                  )}
                </div>
              )}

              {/* Step 3+ : Show judgment result */}
              {currentStep >= 2 && detectionState !== "idle" && (
                <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <p className="text-xs text-slate-500 mb-2">判定结果：</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div
                      className={`border rounded p-2 ${
                        breakpointType === "方向错误"
                          ? "bg-red-50 border-red-200"
                          : breakpointType === "卡在某步"
                            ? "bg-amber-50 border-amber-200"
                            : "bg-blue-50 border-blue-200"
                      }`}
                    >
                      <span
                        className={
                          breakpointType === "方向错误"
                            ? "text-red-600"
                            : breakpointType === "卡在某步"
                              ? "text-amber-600"
                              : "text-blue-600"
                        }
                      >
                        断点类型
                      </span>
                      <p className="text-slate-800 font-medium">
                        {breakpointType || "-"}
                      </p>
                    </div>
                    <div className="bg-purple-50 border border-purple-200 rounded p-2">
                      <span className="text-purple-600">推荐级别</span>
                      <p className="text-slate-800 font-medium">
                        {breakpointType === "方向错误"
                          ? "R3"
                          : breakpointType === "卡在某步"
                            ? "M2"
                            : "M1"}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Hint Card (Step 3) */}
        {showHint && hintContent && (
          <div className="p-6 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-200 shadow-sm animate-fade-in">
            <div className="flex items-start gap-4">
              <div className="text-3xl">💡</div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <h4 className="text-slate-800 font-semibold">系统提示</h4>
                  <KPBadge kpId="KP_3_27" name="函数单调性" type="method" />
                </div>
                <p className="text-slate-700 leading-relaxed whitespace-pre-line">
                  {hintContent}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Success */}
        {currentStep >= 3 && detectionState === "correct" && (
          <div className="mt-4 p-6 bg-emerald-50 rounded-xl border border-emerald-200 animate-fade-in">
            <div className="flex items-center gap-4">
              <div className="text-4xl">🎉</div>
              <div>
                <h4 className="text-slate-800 font-semibold text-lg">
                  问题解决！
                </h4>
                <p className="text-emerald-700 mt-1">
                  在系统提示的引导下，学生成功完成了解题。
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Student selection hint */}
        {selectedScenario === null && (
          <div className="mt-4 p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
            <p className="text-slate-500 text-sm text-center">
              💡
              选择上方学生案例，观看AI如何检测学生解题过程中的断点并提供针对性提示
            </p>
          </div>
        )}
      </div>
      <Outlet />
    </div>
  );
};
