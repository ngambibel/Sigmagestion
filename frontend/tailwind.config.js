/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    // Échelle typographique du cahier des charges (ratio 1,25)
    fontSize: {
      xs: ["12px", { lineHeight: "1.4" }],
      sm: ["14px", { lineHeight: "1.45" }],
      base: ["16px", { lineHeight: "1.55" }],
      lg: ["20px", { lineHeight: "1.4" }],
      xl: ["25px", { lineHeight: "1.3" }],
      "2xl": ["31px", { lineHeight: "1.2" }],
      "3xl": ["39px", { lineHeight: "1.1" }],
      "4xl": ["49px", { lineHeight: "1.05" }],
    },
    extend: {
      colors: {
        papier: {
          DEFAULT: "rgb(var(--papier) / <alpha-value>)",
          surface: "rgb(var(--papier-surface) / <alpha-value>)",
          creux: "rgb(var(--papier-creux) / <alpha-value>)",
        },
        encre: {
          DEFAULT: "rgb(var(--encre) / <alpha-value>)",
          douce: "rgb(var(--encre-douce) / <alpha-value>)",
          pale: "rgb(var(--encre-pale) / <alpha-value>)",
        },
        cyan: {
          DEFAULT: "rgb(var(--cyan) / <alpha-value>)",
          clair: "rgb(var(--cyan-clair) / <alpha-value>)",
        },
        magenta: {
          DEFAULT: "rgb(var(--magenta) / <alpha-value>)",
          clair: "rgb(var(--magenta-clair) / <alpha-value>)",
        },
        jaune: {
          DEFAULT: "rgb(var(--jaune) / <alpha-value>)",
          clair: "rgb(var(--jaune-clair) / <alpha-value>)",
        },
        valide: {
          DEFAULT: "rgb(var(--valide) / <alpha-value>)",
          clair: "rgb(var(--valide-clair) / <alpha-value>)",
        },
      },
      fontFamily: {
        display: ['"Bricolage Grotesque Variable"', "system-ui", "sans-serif"],
        sans: ['"Public Sans Variable"', "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
