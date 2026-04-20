/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0f172a",
        mist: "#eef2ff",
        line: "#dbe4f0",
        canvas: "#f4f7fb",
        panel: "#ffffff"
      },
      fontFamily: {
        sans: ["'SF Pro SC'", "'PingFang SC'", "'Hiragino Sans GB'", "'Microsoft YaHei'", "system-ui", "sans-serif"],
        display: ["'SF Pro SC'", "'PingFang SC'", "'Hiragino Sans GB'", "'Microsoft YaHei'", "system-ui", "sans-serif"],
        mono: ["'SF Mono'", "'Roboto Mono'", "'IBM Plex Mono'", "ui-monospace", "monospace"]
      },
      boxShadow: {
        panel: "0 18px 50px rgba(15, 23, 42, 0.08)"
      }
    }
  },
  plugins: []
};
