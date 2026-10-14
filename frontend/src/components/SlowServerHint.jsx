import { useEffect, useState } from "react";

const DELAY_MS = 4000;

// The API runs on a free host that sleeps when idle; explain long first loads instead of
// leaving people staring at a spinner.
export default function SlowServerHint({ active }) {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    if (!active) return undefined;
    const timer = setTimeout(() => setSlow(true), DELAY_MS);
    return () => {
      clearTimeout(timer);
      setSlow(false);
    };
  }, [active]);

  if (!active || !slow) return null;
  return (
    <p role="status" className="text-center text-xs text-slate-500">
      Waking up the server… the free hosting sleeps when idle and can take up to a minute.
    </p>
  );
}
