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
          DEFAULT: "#F6F6F3",
          surface: "#FFFFFF",
          creux: "#ECECE6",
        },
        encre: {
          DEFAULT: "#14161A",
          douce: "#4A4F58",
          pale: "#868D98",
        },
        cyan: {
          DEFAULT: "#0B7285",
          clair: "#E0F2F5",
        },
        magenta: {
          DEFAULT: "#B02A5B",
          clair: "#FBE7EE",
        },
        jaune: {
          DEFAULT: "#C98A0B",
          clair: "#FDF3DC",
        },
        valide: {
          DEFAULT: "#157F4A",
          clair: "#E2F4EA",
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
