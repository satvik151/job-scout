import { useEffect, useRef } from "react";

export function DashboardBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId = 0;
    let width = 0;
    let height = 0;
    let spotX = 0;
    let spotY = 0;
    let spotVX = 0.4;
    let spotVY = 0.3;
    let purpleX = 0;
    let purpleY = 0;
    let purpleVX = 0.25;
    let purpleVY = 0.35;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;

      if (spotX === 0 && spotY === 0) {
        spotX = width * 0.65;
        spotY = height * 0.35;
      }

      if (purpleX === 0 && purpleY === 0) {
        purpleX = width * 0.25;
        purpleY = height * 0.7;
      }
    };

    const drawGrid = () => {
      ctx.strokeStyle = "rgba(99, 102, 241, 0.04)";
      ctx.lineWidth = 1;

      for (let x = 0; x <= width; x += 60) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }

      for (let y = 0; y <= height; y += 60) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }
    };

    const drawSpotlight = (x: number, y: number, radius: number, color: string) => {
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      gradient.addColorStop(0, color);
      gradient.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);
    };

    const loop = () => {
      ctx.clearRect(0, 0, width, height);

      drawGrid();

      spotX += spotVX;
      spotY += spotVY;
      purpleX += purpleVX;
      purpleY += purpleVY;

      if (spotX > width || spotX < 0) spotVX *= -1;
      if (spotY > height || spotY < 0) spotVY *= -1;
      if (purpleX > width || purpleX < 0) purpleVX *= -1;
      if (purpleY > height || purpleY < 0) purpleVY *= -1;

      drawSpotlight(spotX, spotY, 400, "rgba(99, 102, 241, 0.04)");
      drawSpotlight(purpleX, purpleY, 500, "rgba(139, 92, 246, 0.03)");

      animationFrameId = window.requestAnimationFrame(loop);
    };

    resize();
    window.addEventListener("resize", resize);
    animationFrameId = window.requestAnimationFrame(loop);

    return () => {
      window.cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <>
      <div
        aria-hidden="true"
        className="fixed -top-[100px] -left-[100px] pointer-events-none"
        style={{
          zIndex: 0,
          width: "400px",
          height: "400px",
          background:
            "radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 70%)",
        }}
      />
      <div
        aria-hidden="true"
        className="fixed -bottom-[100px] -right-[100px] pointer-events-none"
        style={{
          zIndex: 0,
          width: "500px",
          height: "500px",
          background:
            "radial-gradient(circle, rgba(139,92,246,0.05) 0%, transparent 70%)",
        }}
      />
      <canvas
        ref={canvasRef}
        aria-hidden="true"
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 0,
          pointerEvents: "none",
          width: "100vw",
          height: "100vh",
        }}
      />
    </>
  );
}
