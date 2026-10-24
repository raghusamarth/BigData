import { useEffect, useState } from 'react';
import { BrainCircuit, AlertTriangle } from 'lucide-react';
import { api } from '../api';
import { SectionLabel, Meta, Card, DbOps } from './ui';

export function Analytics() {
  const [corr, setCorr] = useState(null);
  const [anom, setAnom] = useState([]);
  useEffect(() => {
    api.correlation().then(setCorr).catch(() => setCorr({ message: 'API offline' }));
    api.anomalies(50).then((d) => setAnom(Array.isArray(d) ? d : [])).catch(() => {});
  }, []);
  return (
    <section id="analytics" className="bg-ink text-paper newsprint-texture">
      <div className="max-w-screen-xl mx-auto px-4 py-16">
        <div className="flex items-center gap-3 border-b-4 border-paper pb-2 mb-6">
          <span className="bg-editorial text-white font-mono text-xs px-2 py-1">§3</span>
          <h2 className="font-serif font-black text-4xl lg:text-5xl">Big Data Analytics</h2>
        </div>
        <Meta><span className="text-neutral-400">Fig. 3.1 — PySpark outputs cached in analytics_results · inverted plate</span></Meta>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 mt-4 border-t border-l border-paper">
          <div className="lg:col-span-7 border-r border-b border-paper p-6 grid-border-r">
            <h3 className="font-serif font-bold text-2xl flex items-center gap-2"><BrainCircuit strokeWidth={1.5} /> Correlation Matrix</h3>
            <DbOps light>analytics_results.find({"{"}type: 'correlation'{"}"}) — cached Spark output</DbOps>
            <p className="font-body text-sm mt-2 text-neutral-300">Pairwise return correlations across the symbol universe — the O(n²) workload that justifies Spark. Computed in distributed mode, served from cache.</p>
            <pre className="sharp-corners font-mono text-xs bg-paper text-ink p-4 mt-4 overflow-auto max-h-72">{JSON.stringify(corr, null, 2)}</pre>
          </div>
          <div className="lg:col-span-5 border-b border-paper p-6">
            <h3 className="font-serif font-bold text-2xl flex items-center gap-2"><AlertTriangle strokeWidth={1.5} /> Anomalies</h3>
            <DbOps light>find({"{"}type: 'anomaly'{"}"}) — z-score flags, served from cache</DbOps>
            <p className="font-body text-sm mt-2 text-neutral-300">Z-score flags (|z| &gt; 3) on daily returns — unusual sessions worth a headline.</p>
            <div className="mt-4 space-y-0 border-t border-l border-paper font-mono text-xs">
              {anom.length ? anom.slice(0, 12).map((a, i) => (
                <div key={i} className="border-r border-b border-paper px-2 py-2 flex justify-between">
                  <span>{a.symbol}</span><span className="text-editorial">{a.timestamp || a.date || ''}</span>
                </div>
              )) : <p className="p-2">No anomalies cached — run the Spark job.</p>}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
