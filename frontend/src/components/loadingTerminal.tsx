import { useEffect, useRef, useState } from 'react';
import styled, { keyframes, css } from 'styled-components';

const LINES = [
  '$ jamaat --location scarborough',
  'connecting to jamaat-backend · yyz',
  'GET /prayer-times',
  'reading prayer_times.db',
  'collecting jamaat times per mosque',
  'scrape cadence: daily · 3:00 AM ET',
  'building timetable',
];

const REVEAL_INTERVAL_MS = 600;
const TICK_MS = 100;

function timestamp(): string {
  return new Date().toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

type RevealedLine = { ts: string; text: string };

function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);
  return reduced;
}

export function LoadingTerminal() {
  const reducedMotion = useReducedMotion();

  const [revealed, setRevealed] = useState<RevealedLine[]>(() => {
    if (reducedMotion) {
      return LINES.map((text) => ({ ts: timestamp(), text }));
    }
    return [];
  });

  const [elapsed, setElapsed] = useState(0);
  const [allDone, setAllDone] = useState(reducedMotion);

  const ticksRef = useRef(0);
  const startRef = useRef(Date.now());
  const revealedCountRef = useRef(reducedMotion ? LINES.length : 0);

  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (reducedMotion) return;

    const id = setInterval(() => {
      ticksRef.current += 1;
      const elapsedSec = (Date.now() - startRef.current) / 1000;
      setElapsed(elapsedSec);

      const shouldReveal =
        ticksRef.current % Math.round(REVEAL_INTERVAL_MS / TICK_MS) === 0;

      if (shouldReveal && revealedCountRef.current < LINES.length) {
        const next = LINES[revealedCountRef.current];
        revealedCountRef.current += 1;
        setRevealed((prev) => [...prev, { ts: timestamp(), text: next }]);

        if (revealedCountRef.current === LINES.length) {
          setAllDone(true);
        }
      } else if (revealedCountRef.current >= LINES.length) {
        setElapsed(elapsedSec);
      }
    }, TICK_MS);

    return () => clearInterval(id);
  }, [reducedMotion]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [revealed, allDone]);

  return (
    <Panel>
      <TitleBar>
        <Dots>
          <Dot $color="#ff5f57" />
          <Dot $color="#febc2e" />
          <Dot $color="#28c840" />
        </Dots>
        <TitleLabel>jamaat — fetching times</TitleLabel>
      </TitleBar>
      <LogBody role="status" aria-live="polite" aria-label="Loading prayer times">
        {revealed.map((line, i) => {
          const isNewest = i === revealed.length - 1 && !allDone;
          return (
            <LogLine key={i}>
              <Ts>[{line.ts}]</Ts>
              <LogText>{line.text}</LogText>
              {isNewest && !reducedMotion ? (
                <Caret aria-hidden="true">▋</Caret>
              ) : (
                <Check aria-hidden="true">✓</Check>
              )}
            </LogLine>
          );
        })}
        {allDone && !reducedMotion && (
          <TailLine>
            <Ts>[{timestamp()}]</Ts>
            <LogText>waiting for response… {elapsed.toFixed(1)}s</LogText>
            <Caret aria-hidden="true">▋</Caret>
          </TailLine>
        )}
        <div ref={logEndRef} />
      </LogBody>
    </Panel>
  );
}

const Panel = styled.div`
  width: min(480px, 100%);
  background: rgba(9, 9, 43, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  overflow: hidden;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 13px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
`;

const TitleBar = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const Dots = styled.div`
  display: flex;
  gap: 6px;
  flex-shrink: 0;
`;

const Dot = styled.span<{ $color: string }>`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: ${({ $color }) => $color};
  opacity: 0.85;
`;

const TitleLabel = styled.span`
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
  letter-spacing: 0.02em;
`;

const LogBody = styled.div`
  padding: 14px 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 120px;
  max-height: 300px;
  overflow-y: auto;
`;

const LogLine = styled.div`
  display: flex;
  align-items: baseline;
  gap: 8px;
  line-height: 1.5;
`;

const TailLine = styled(LogLine)`
  color: rgba(255, 255, 255, 0.45);
`;

const Ts = styled.span`
  color: rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
  font-size: 11px;
`;

const LogText = styled.span`
  color: rgba(255, 255, 255, 0.85);
  word-break: break-all;
`;

const Check = styled.span`
  color: #28c840;
  flex-shrink: 0;
`;

const blink = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
`;

const Caret = styled.span`
  color: rgba(255, 255, 255, 0.7);
  flex-shrink: 0;
  ${css`
    animation: ${blink} 1s step-start infinite;
    @media (prefers-reduced-motion: reduce) {
      animation: none;
    }
  `}
`;
