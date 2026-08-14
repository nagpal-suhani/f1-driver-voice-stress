/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        void: "#08090b",
        charcoal: "#101215",
        surface: "#15171b",
        "surface-2": "#1b1e23",
        line: "#2a2d33",
        accent: "#e10600",
        "accent-dim": "#7a0603",
        muted: "#8a8f98",
        offwhite: "#f4f4f2",
      },
      fontFamily: {
        display: ["'Oswald'", "'Barlow Condensed'", "system-ui", "sans-serif"],
        body: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "'IBM Plex Mono'", "monospace"],
      },
      boxShadow: {
        "glow-red": "0 0 24px rgba(225,6,0,0.35)",
      },
      clipPath: {
        panel: "polygon(0 0, 100% 0, 100% calc(100% - 14px), calc(100% - 14px) 100%, 0 100%)",
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "40px 40px",
      },
    },
  },
  plugins: [],
};
