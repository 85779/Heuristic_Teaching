import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { profile } from '../core/api/client';

export default function Profile() {
  const { id } = useParams();
  const [p, setP] = useState<any>(null);
  const [h, setH] = useState<any>(null);
  useEffect(() => {
    if (!id) return;
    profile.get(id).then(setP).catch(() => {});
    profile.hint(id).then(setH).catch(() => {});
  }, [id]);
  if (!p) return <div className="text-slate/30 font-sans text-sm p-8">加载中...</div>;

  const r = p.dimension_ratio || 0.5;
  const rPct = Math.round(r * 100);
  const mPct = 100 - rPct;

  return (
    <div className="space-y-8">
      <h2 className="font-serif text-3xl font-bold text-ink">学生画像</h2>
      <p className="text-sm text-slate/50 font-sans -mt-6">{p.student_id}</p>

      <div className="grid grid-cols-4 gap-4">
        {[
          ['维度比例', r.toFixed(2), 'text-chalk'],
          ['干预总数', p.total_interventions, 'text-sage'],
          ['趋势', p.ratio_trend || '稳定', 'text-amber'],
          ['已解决', p.total_solved, 'text-rose'],
        ].map(([l, v, c]) => (
          <div key={l as string} className="bg-white/80 border border-ink/5 rounded-xl p-5">
            <p className="text-xs text-slate/50 font-sans">{l}</p>
            <p className={`text-2xl font-bold mt-1 font-serif ${c}`}>{String(v)}</p>
          </div>
        ))}
      </div>

      <div className="bg-white/80 border border-ink/5 rounded-2xl p-6">
        <h3 className="font-serif text-sm font-semibold text-ink mb-4">R/M 维度平衡</h3>
        <div className="h-7 bg-cream/80 rounded-full overflow-hidden flex text-xs font-medium font-sans">
          <div className="h-full bg-chalk text-white flex items-center justify-center transition-all duration-700" style={{ width: `${rPct}%` }}>
            {rPct > 10 ? `资源型 R ${rPct}%` : ''}
          </div>
          <div className="h-full bg-slate/60 text-white flex items-center justify-center transition-all duration-700" style={{ width: `${mPct}%` }}>
            {mPct > 10 ? `元认知 M ${mPct}%` : ''}
          </div>
        </div>
      </div>

      {h && (
        <div className="bg-chalk/5 border border-chalk/10 rounded-2xl p-5">
          <h3 className="font-serif text-sm font-semibold text-chalk mb-2">路由提示</h3>
          <p className="text-sm text-ink/70 font-sans">{h.recommended_dimension_hint}</p>
        </div>
      )}
    </div>
  );
}
