import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Layers } from 'lucide-react';
import { api } from '../api';
import { SectionLabel, Meta, Card, DbOps } from './ui';

function compact(v) {
  const a = Math.abs(v);
  if (a >= 1e9) return (v / 1e9).toFixed(2) + 'B';
  if (a >= 1e6) return (v / 1e6).toFixed(2) + 'M';
  if (a >= 1e3) return (v / 1e3).toFixed(2) + 'K';
  return v.toFixed(2);
}

function Bars({ rows, vkey, lkey, fmt = (v) => v.toFixed(2) }) {
  const max = Math.max(...rows.map((r) => Math.abs(Number(r[vkey]) || 0)), 1);
  return (
    <div className="space-y-2">
      {rows.slice(0, 10).map((r) => {
        const v = Number(r[vkey]) || 0;
        return (
          <div key={r[lkey]} className="grid grid-cols-12 items-center gap-2 font-mono text-xs tabular-nums leading-5">
            <span className="col-span-4 truncate pr-2" title={r[lkey]}>{r[lkey]}</span>
            <div className="col-span-6 bg-divider h-4 overflow-hidden">
              <div className={`h-4 ${v >= 0 ? 'bg-ink' : 'bg-editorial'}`} style={{ width: `${Math.min(100, (Math.abs(v) / max) * 100)}%` }} />
            </div>
            <span className="col-span-2 text-right whitespace-nowrap">{fmt(v)}</span>
          </div>
        );
      })}
    </div>
  );
}

export function MarketOverview() {
  const [vol, setVol] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [err, setErr] = useState('');
  useEffect(() => {
    api.volatility(10).then((d) => setVol(Array.isArray(d) ? d : d.data || [])).catch((e) => setErr(String(e.message)));
    api.sectors().then((d) => setSectors(Array.isArray(d) ? d : d.data || [])).catch(() => {});
  }, []);
  return (
    <section id="market" className="max-w-screen-xl mx-auto px-4 lg:px-8 py-16">
      <SectionLabel no="1" title="Market Overview" />
      <Meta>Fig. 1.1 — Live MongoDB aggregations · $match → $group → $sort</Meta>
      {err && <p className="font-mono text-xs text-editorial mt-2">API offline: {err} — start the api service.</p>}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 mt-4 border border-ink">
        <div className="lg:col-span-8 border-b lg:border-b-0 lg:border-r border-ink p-6">
          <h3 className="font-serif font-bold text-2xl mb-1 flex items-center gap-2"><TrendingUp strokeWidth={1.5} /> Volatility Ranking</h3>
          <DbOps>historical_prices.aggregate([$group → stdDev, $sort, $limit 10])</DbOps>
          <p className="font-body text-sm text-justify mt-3 mb-4"><span className="float-left font-serif font-black text-5xl leading-[0.85] mt-1 mr-2">V</span>olatility, measured as the coefficient of variation across each symbol's full history, is computed inside MongoDB — the database does the grouping so the API ships only ten rows, not a million documents.</p>
          {vol.length ? <Bars rows={vol} vkey="coef_var" lkey="symbol" /> : <p className="font-mono text-xs">No data yet — run the seed job.</p>}
        </div>
        <div className="lg:col-span-4 p-6">
          <h3 className="font-serif font-bold text-2xl mb-1 flex items-center gap-2"><Layers strokeWidth={1.5} /> Sectors</h3>
          <DbOps>aggregate([$lookup → stocks_meta, $group, $sort])</DbOps>
          <p className="font-body text-sm mt-3 mb-4">Capital-weighted murmur of the street, joined via <span className="font-mono text-xs">$lookup</span> on stocks_meta.</p>
          {sectors.length ? <Bars rows={sectors} vkey="total_volume" lkey="sector" fmt={compact} /> : <p className="font-mono text-xs">No data yet.</p>}
          <div className="mt-6 border border-ink p-4 flex items-center gap-2 font-mono text-xs uppercase tracking-widest">
            <TrendingDown strokeWidth={1.5} className="h-4 w-4" /> Past performance ≠ future results
          </div>
        </div>
      </div>
    </section>
  );
}
