#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

// Reverse of VAR_MAP
const TAILWIND_TO_VAR = {
  "bg-bg-dark": "var(--color-bg-dark)",
  "bg-bg-secondary": "var(--color-bg-secondary)",
  "bg-bg-sec": "var(--color-bg-sec)",
  "text-text-light": "var(--color-text-light)",
  "text-text-muted": "var(--color-text-muted)",
  "border-border-secondary": "var(--color-border-secondary)",
  "border-divider": "var(--divider)",
  "shadow-[rgba(0,0,0,0.6)]": "var(--shadow)",
  "text-neon-purple": "var(--neon-purple)",
  "text-neon-mint": "var(--neon-mint)",
  "text-accent-yellow": "var(--color-accent-yellow)",
  "hover:text-accent-purpleHover": "var(--color-accent-purple-hover)",
  "text-accent-mint": "var(--color-accent-mint)",
  "hover:shadow-[0_0_10px_rgba(192,132,252,0.6)]": "var(--hover-glow)",
  "bg-frosted-bg": "var(--frosted-bg)",
  "hover:bg-hover": "var(--hover)",
  "hover:bg-hover-light": "var(--color-hover-light)",
  "text-error": "var(--color-error)",
  "font-sans": "var(--font-sans)",
};

const VALID_EXTENSIONS = [".js", ".ts", ".jsx", ".tsx", ".html", ".vue", ".css"];

function restoreVarsInFile(filePath) {
  let content = fs.readFileSync(filePath, "utf8");
  let updated = content;

  for (const [twClass, cssVar] of Object.entries(TAILWIND_TO_VAR)) {
    const regex = new RegExp(twClass.replace(/[-[\]/{}()*+?.\\^$|]/g, "\\$&"), "g");
    updated = updated.replace(regex, cssVar);
  }

  if (content !== updated) {
    fs.writeFileSync(filePath, updated, "utf8");
    console.log(`⏪ Reverted: ${filePath}`);
  }
}

function scanDir(dir) {
  for (const file of fs.readdirSync(dir)) {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      scanDir(fullPath);
    } else if (VALID_EXTENSIONS.includes(path.extname(file))) {
      restoreVarsInFile(fullPath);
    }
  }
}

// Run from frontend root
const frontendPath = path.join(__dirname, "frontend");
scanDir(frontendPath);
