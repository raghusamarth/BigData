import { useEffect, useState } from 'react';
import { Database, ArrowRight } from 'lucide-react';
import { api } from '../api';
import { SectionLabel, Meta, Card, DbOps } from './ui';

const STAGES = ['yfinance', 'ingest + clean', 'MongoDB time-series', 'Mongo Agg ∥ PySpark', 'analytics_results', 'FastAPI', 'This page'];

export function Pipeline() {
  const [stats, setStats] = useState(null);
  useEffect(() => { api.stats().then(setStats).catch(() => {}); }, []);
  return (
    <section id="pipeline" className="max-w-screen-xl mx-auto px-4 py-16 border-t-4 border-ink">
      <SectionLabel no="4" title="Data Pipeline" />
      <Meta>Fig. 4.1 — From source to print · counts are live</Meta>
      <div className="flex flex-wrap items-stretch gap-0 mt-4 border-t border-l border-ink font-mono text-xs">
        {STAGES.map((s, i) => (
          <div key={s} className="flex items-center border-r border-b border-ink grid-border-r">
            <span className={`px-3 py-3 uppercase tracking-widest ${i === 2 ? 'bg-ink text-paper' : ''}`}>{s}</span>
            {i < STAGES.length - 1 && <ArrowRight className="h-4 w-4 mx-1" strokeWidth={1.5} />}
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-0 mt-6 border-t border-l border-ink">
        {[
          ['Price docs', stats?.total_price_docs ?? '—'],
          ['Symbols', stats?.symbols ?? '—'],
          ['Indicator docs', stats?.indicator_docs ?? '—'],
          ['Collections', stats?.collections?.length ?? '—'],
        ].map(([k, v]) => (
          <div key={k} className="border-r border-b border-ink p-6 grid-border-r">
            <p className="font-mono text-4xl font-black">{typeof v === 'number' ? v.toLocaleString() : v}</p>
            <p className="font-mono text-xs uppercase tracking-widest mt-1">{k}</p>
          </div>
        ))}
      </div>
      <Card className="mt-6">
        <h3 className="font-serif font-bold text-2xl flex items-center gap-2"><Database strokeWidth={1.5} /> Per-symbol ledger</h3>
        <DbOps>historical_prices.aggregate([$group → counts, $sort]) — ingestion health check</DbOps>
        {stats?.per_symbol?.length ? (
          <table className="w-full font-mono text-xs mt-3 border-t border-l border-ink">
            <thead><tr className="bg-ink text-paper">{['Symbol', 'Rows', 'From', 'To'].map((h) => <th key={h} className="text-left px-2 py-2 uppercase tracking-widest">{h}</th>)}</tr></thead>
            <tbody>{stats.per_symbol.slice(0, 15).map((r) => (
              <tr key={r.symbol} className="border-b border-ink hover:bg-neutral-100"><td className="border-r border-ink px-2 py-1">{r.symbol}</td><td className="border-r border-ink px-2 py-1">{r.rows}</td><td className="border-r border-ink px-2 py-1">{r.min_date}</td><td className="px-2 py-1">{r.max_date}</td></tr>
            ))}</tbody>
          </table>
        ) : <p className="font-mono text-xs mt-2">Empty press — run <span className="bg-ink text-paper px-1">docker compose --profile seed run seed</span>.</p>}
      </Card>
    </section>
  );
}
