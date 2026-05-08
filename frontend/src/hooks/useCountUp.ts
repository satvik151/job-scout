import { useEffect, useState } from "react";

export function useCountUp(target: number, duration = 1200) {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (target === 0) {
      setCurrent(0);
      return;
    }

    let startTime: number | null = null;
    let animationFrameId: number;

    const animate = (timestamp: number) => {
      if (startTime === null) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic: 1 - (1 - t)^3
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = target * eased;

      // Round based on whether target has decimals
      const hasDecimals = !Number.isInteger(target);
      setCurrent(hasDecimals ? parseFloat(value.toFixed(1)) : Math.round(value));

      if (progress < 1) {
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    animationFrameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrameId);
  }, [target, duration]);

  return current;
}
