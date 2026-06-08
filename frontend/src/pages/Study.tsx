import { useState } from 'react';
import { solving, intervention, recommend } from '../core/api/client';

type Step = 'input' | 'evaluating' | 'result' | 'hint' | 'recommend';

export default function Study() {
  const [problem, setProblem] = useState('');
  const [studentWork, setStudentWork] = useState('');
  const [step, setStep] = useState<Step>('input');
  const [evaluation, setEval] = useState<any>(null);
  const [solution, setSolution] = useState<any>(null);
  const [hint, setHint] = useState<any>(null);
  const [rec, setRec] = useState<any>(null);
  const [error, setError] = useState('');
  const [studentId] = useState('student_001');

  const handleSubmit = async () => {
    if (!problem.trim()) return;
    setStep('evaluating'); setError('');
    try {
      const res = await solving.solve({
        problem: problem.trim(),
        student_work: studentWork.trim() || undefined,
      });
      setEval(res.evaluation);
      setSolution(res.solution);
      setStep('result');

      // Auto-trigger intervention if student got it wrong
      if (res.evaluation && !res.evaluation.is_correct && studentWork.trim()) {
        setStep('hint');
        try {
          const ir = await intervention.create({
            student_id: studentId, session_id: studentId,
            student_input: studentWork.trim(), intervention_type: 'hint',
          });
          setHint(ir.intervention);
        } catch {}

        // Also get recommendation
        try {
          const rr = await recommend.rec({
            student_id: studentId,
            trigger: { outcome: 'SOLVED', current_problem_kps: [[]], current_method: '', current_difficulty: 2, session_id: studentId },
          });
          setRec(rr.recommendation);
        } catch {}
      }

      // If correct, get recommendation
      if (res.evaluation?.is_correct && studentWork.trim()) {
        setStep('recommend');
        try {
          const rr = await recommend.rec({
            student_id: studentId,
            trigger: { outcome: 'SOLVED', current_problem_kps: [[]], current_method: '', current_difficulty: 2, session_id: studentId },
          });
          setRec(rr.recommendation);
        } catch {}
      }
    } catch (e: any) { setError(e.message); setStep('input'); }
  };

  const reset = () => { setProblem(''); setStudentWork(''); setStep('input'); setEval(null); setSolution(null); setHint(null); setRec(null); setError(''); };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Input area — always visible */}
      <div className="bg-white/80 border border-ink/5 rounded-2xl p-6 space-y-4">
        <h2 className="font-serif text-2xl font-bold text-ink">学习</h2>
        <p className="text-xs text-slate/50 font-sans -mt-3">输入题目和作答，系统自动评估、给出提示、推荐下一题</p>

        <div>
          <div className="flex gap-4"><div className="flex-1"><label className="block text-xs text-slate/50 uppercase tracking-wider mb-2 font-sans">题目</label>
          <textarea className="w-full bg-cream/50 border border-ink/10 rounded-xl p-4 text-sm text-ink placeholder:text-slate/30 focus:outline-none focus:border-chalk/50 transition font-sans resize-none" rows={2}
            placeholder="输入数学题，支持 LaTeX" value={problem} onChange={e => setProblem(e.target.value)} /></div><div className="w-36"><label className="block text-xs text-slate/50 uppercase tracking-wider mb-2 font-sans">学生</label><input className="w-full bg-cream/50 border border-ink/10 rounded-xl p-4 text-sm text-ink font-sans focus:outline-none focus:border-chalk/50 transition" value={studentId} onChange={e => setStudentId(e.target.value)} /></div></div>
        </div>
        <div>
          <label className="block text-xs text-slate/50 uppercase tracking-wider mb-2 font-sans">你的作答（可选，留空则只生成参考解法）</label>
          <textarea className="w-full bg-cream/50 border border-ink/10 rounded-xl p-4 text-sm text-ink placeholder:text-slate/30 focus:outline-none focus:border-ink/30 transition font-sans resize-none" rows={4}
            placeholder="写下你的解题过程..." value={studentWork} onChange={e => setStudentWork(e.target.value)} />
        </div>

        <div className="flex gap-3">
          <button onClick={handleSubmit} disabled={!problem.trim() || step === 'evaluating'}
            className="px-5 py-2.5 bg-ink text-white rounded-xl text-sm font-sans font-medium hover:bg-ink/90 disabled:opacity-30 transition-all">
            {step === 'evaluating' ? '分析中...' : studentWork.trim() ? '提交并评估' : '生成参考解法'}
          </button>
          {step !== 'input' && (
            <button onClick={reset} className="px-5 py-2.5 bg-ink/5 text-ink/60 rounded-xl text-sm font-sans hover:bg-ink/10 transition-all">重新开始</button>
          )}
        </div>
        {error && <p className="text-rose text-sm font-sans">{error}</p>}
      </div>

      {/* Evaluation result */}
      {evaluation && (
        <div className={`rounded-2xl p-6 ${evaluation.is_correct ? 'bg-sage/5 border border-sage/20' : 'bg-rose/5 border border-rose/20'}`}>
          <div className="flex items-center gap-3 mb-3">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${evaluation.is_correct ? 'bg-sage/20 text-sage' : 'bg-rose/20 text-rose'}`}>
              {evaluation.is_correct ? '✓' : '✕'}
            </div>
            <div>
              <p className={`font-serif text-lg font-bold ${evaluation.is_correct ? 'text-sage' : 'text-rose'}`}>
                {evaluation.is_correct ? '作答正确' : '发现问题'}
              </p>
              <p className="text-xs text-slate/50 font-sans">置信度 {Math.round(evaluation.confidence * 100)}%</p>
            </div>
          </div>
          {evaluation.issues?.map((iss: any, i: number) => (
            <p key={i} className="text-sm text-ink/70 leading-relaxed ml-11 font-sans">
              {iss.step && <span className="text-xs text-slate/40 mr-1">步骤{iss.step}</span>}{iss.description}
            </p>
          ))}
        </div>
      )}

      {/* Solution */}
      {solution && (
        <div className="bg-white/80 border border-ink/5 rounded-2xl p-6 space-y-4">
          <h3 className="font-serif text-lg font-semibold text-ink">参考解法</h3>
          {solution.steps?.map((st: any, i: number) => (
            <div key={i} className="bg-cream/50 rounded-xl p-4">
              <div className="flex items-center gap-3 mb-2">
                <span className="w-7 h-7 rounded-full bg-chalk/10 text-chalk text-xs font-bold flex items-center justify-center font-sans">{i + 1}</span>
                <span className="font-medium text-ink font-sans text-sm">{st.step_name}</span>
              </div>
              <p className="text-sm text-ink/70 leading-relaxed whitespace-pre-wrap font-sans ml-10">{st.content}</p>
            </div>
          ))}
          {solution.answer && (
            <div className="p-4 bg-chalk/5 rounded-xl border border-chalk/10">
              <span className="text-xs text-chalk font-medium font-sans">答案</span>
              <span className="text-sm text-ink font-sans ml-2">{solution.answer}</span>
            </div>
          )}
        </div>
      )}

      {/* Intervention hint — shown when student got it wrong */}
      {hint && (
        <div className="bg-white/80 border border-ink/5 rounded-2xl p-6 space-y-3">
          <h3 className="font-serif text-lg font-semibold text-ink">智能提示</h3>
          <div className="flex gap-2">
            <span className="px-2 py-0.5 text-xs rounded-full bg-chalk/10 text-chalk font-sans">{hint.intervention_type}</span>
            <span className="px-2 py-0.5 text-xs rounded-full bg-ink/5 text-slate font-sans">{hint.status}</span>
          </div>
          <div className="bg-cream/50 rounded-xl p-4">
            <p className="text-sm text-ink/80 leading-relaxed whitespace-pre-wrap font-sans">{hint.content}</p>
          </div>
        </div>
      )}

      {/* Recommendation — shown after completing */}
      {rec && (
        <div className="bg-white/80 border border-ink/5 rounded-2xl p-6 space-y-3">
          <h3 className="font-serif text-lg font-semibold text-ink">推荐练习</h3>
          <div className="text-xs text-slate/50 font-sans">难度 {rec.difficulty}/5 · 方法：{rec.method_used}</div>
          <div className="bg-cream/50 rounded-xl p-4 text-sm text-ink/80 leading-relaxed font-sans">{rec.problem_text}</div>
          <details className="group">
            <summary className="text-xs text-chalk cursor-pointer font-sans hover:text-chalk/80">查看答案和提示</summary>
            <div className="grid grid-cols-2 gap-3 mt-3">
              <div className="bg-sage/5 rounded-xl p-3"><p className="text-xs text-sage font-sans mb-1">答案</p><p className="text-sm text-ink font-sans">{rec.answer}</p></div>
              <div className="bg-chalk/5 rounded-xl p-3"><p className="text-xs text-chalk font-sans mb-1">提示</p><p className="text-sm text-ink font-sans">{rec.solution_hint}</p></div>
            </div>
          </details>
        </div>
      )}
    </div>
  );
}
