import { useEffect, useState } from 'react';
import { Masthead, Ticker } from './components/Masthead';
import { MarketOverview } from './components/MarketOverview';
import { StockExplorer } from './components/StockExplorer';
import { Analytics } from './components/Analytics';
import { Pipeline } from './components/Pipeline';
import { Trading, Footer } from './components/Trading';
import { Manager } from './components/Manager';
import { api } from './api';

export default function App() {
  const [top, setTop] = useState([]);
  useEffect(() => {
    const end = new Date().toISOString().slice(0, 10);
    const start = new Date(Date.now() - 90 * 864e5).toISOString().slice(0, 10);
    api.topGainers(start, end, 12).then((d) => setTop(Array.isArray(d) ? d : d.data || [])).catch(() => {});
  }, []);
  return (
    <div className="sharp-corners min-h-screen bg-paper text-ink font-body">
      <Masthead />
      <Ticker items={top} />
      <main>
        <MarketOverview />
        <div className="py-4 text-center font-serif text-2xl text-neutral-400 tracking-[1em]" aria-hidden="true">✦ ✦ ✦</div>
        <StockExplorer />
        <Analytics />
        <Pipeline />
        <Trading />
        <Manager />
      </main>
      <Footer />
    </div>
  );
}
