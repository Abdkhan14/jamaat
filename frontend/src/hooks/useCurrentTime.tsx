import { useEffect, useState } from "react";

export function useCurrentTime(interval: number = 60 * 1000) {
  const [currentTime, setCurrentTime] = useState(() => new Date());

  useEffect(() => {
    const timeoutId = setInterval(() => {
      setCurrentTime(new Date());
    }, interval);

    return () => clearInterval(timeoutId);
  }, []);

  return currentTime;
}
