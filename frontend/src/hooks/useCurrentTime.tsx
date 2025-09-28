import { useEffect, useState } from "react";

export function useCurrentTime() {
  const [currentTime, setCurrentTime] = useState(() => new Date());

  useEffect(() => {
    // Update immediately every minute
    const tick = () => setCurrentTime(new Date());

    // Run once on mount
    tick();

    // Calculate time until the next minute starts
    const msUntilNextMinute = (60 - new Date().getSeconds()) * 1000;

    // Set a timeout to align with the next minute
    const timeoutId = setTimeout(() => {
      tick();
      // After aligning, update every 60 seconds
      const intervalId = setInterval(tick, 60 * 1000);
      return () => clearInterval(intervalId);
    }, msUntilNextMinute);

    return () => clearTimeout(timeoutId);
  }, []);

  return currentTime;
}
