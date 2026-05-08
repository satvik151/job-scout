export function AuthBackground() {
  return (
    <div
      className="absolute inset-0 overflow-hidden"
      style={{
        background:
          "radial-gradient(ellipse at top left, #1e1b4b 0%, #0a0a0a 55%)",
      }}
    >
      <div
        className="orb"
        style={{
          top: "-100px",
          left: "-100px",
          background: "#6366f1",
        }}
      />
      <div
        className="orb"
        style={{
          bottom: "-150px",
          right: "-100px",
          background: "#a855f7",
          animationDelay: "2s",
        }}
      />
      {/* noise overlay */}
      <div
        className="absolute inset-0 opacity-[0.04] mix-blend-overlay"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
        }}
      />
    </div>
  );
}