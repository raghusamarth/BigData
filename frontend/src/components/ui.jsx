export function SectionLabel({ no, title }) {
  return (
    <div className="flex items-center gap-3 border-b-4 border-ink pb-2 mb-6">
      <span className="bg-ink text-paper font-mono text-xs px-2 py-1">§{no}</span>
      <h2 className="font-serif font-black text-4xl lg:text-5xl">{title}</h2>
    </div>
  );
}

export function Meta({ children }) {
  return <p className="font-mono text-xs uppercase tracking-widest text-neutral-500">{children}</p>;
}

export function DbOps({ children, light = false }) {
  return <p className={`font-mono text-[11px] mt-1 tabular-nums ${light ? 'text-neutral-400' : 'text-neutral-500'}`}>DB · {children}</p>;
}

export function Card({ children, className = '', hover = false }) {
  return (
    <div className={`sharp-corners border border-ink bg-paper p-6 ${hover ? 'hard-shadow-hover hover:bg-neutral-100' : ''} ${className}`}>
      {children}
    </div>
  );
}

export function Btn({ children, variant = 'primary', ...props }) {
  const base = 'sharp-corners font-sans text-xs uppercase tracking-widest px-5 py-3 min-h-[44px] transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neutral-950 focus-visible:ring-offset-2 ';
  const styles = {
    primary: 'bg-ink text-paper border border-transparent hover:bg-white hover:text-ink hover:border-ink',
    secondary: 'border border-ink bg-transparent hover:bg-ink hover:text-paper',
    breaking: 'bg-editorial text-white border border-transparent hover:bg-ink',
  };
  return <button className={base + styles[variant]} {...props}>{children}</button>;
}
