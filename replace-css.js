#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

// CONFIG: Tailwind equivalents for each CSS var
const VAR_MAP = {
  "--color-bg-dark": "bg-bg-dark",
  "--color-bg-secondary": "bg-bg-secondary",
  "--color-bg-sec": "bg-bg-sec",
  "--color-text-light": "text-text-light",
  "--color-text-muted": "text-text-muted",
  "--color-border-secondary": "border-border-secondary",
  "--divider": "border-divider",
  "--shadow": "shadow-[rgba(0,0,0,0.6)]",
  "--neon-purple": "text-neon-purple",
  "--neon-mint": "text-neon-mint",
  "--color-accent-yellow": "text-accent-yellow",
  "--color-accent-purple-hover": "hover:text-accent-purpleHover",
  "--color-accent-mint": "text-accent-mint",
  "--hover-glow": "hover:shadow-[0_0_10px_rgba(192,132,252,0.6)]",
  "--frosted-bg": "bg-frosted-bg",
  "--hover": "hover:bg-hover",
  "--color-hover-light": "hover:bg-hover-light",
  "--color-error": "text-error",
  "--font-sans": "font-sans",
};

// File extensions to scan
const VALID_EXTENSIONS = [".js", ".ts", ".jsx", ".tsx", ".html", ".vue", ".css"];

function replaceVarsInFile(filePath) {
  let content = fs.readFileSync(filePath, "utf8");
  let updated = content;

  for (const [cssVar, tailwindClass] of Object.entries(VAR_MAP)) {
    const regex = new RegExp(`var\\(${cssVar}\\)`, "g");
    updated = updated.replace(regex, tailwindClass);
  }

  if (content !== updated) {
    fs.writeFileSync(filePath, updated, "utf8");
    console.log(`✔ Updated: ${filePath}`);
  }
}

function scanDir(dir) {
  for (const file of fs.readdirSync(dir)) {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      scanDir(fullPath);
    } else if (VALID_EXTENSIONS.includes(path.extname(file))) {
      replaceVarsInFile(fullPath);
    }
  }
}

// Run the script from frontend root
const frontendPath = path.join(__dirname, "frontend");
scanDir(frontendPath);
