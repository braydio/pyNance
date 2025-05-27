#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const glob = require('glob');

// CLI: node move_component.js BaseCard.vue --to base
const [, , componentName, ...args] = process.argv;
const toGroup = args.includes('--to') ? args[args.indexOf('--to') + 1] : null;

if (!componentName || !toGroup) {
  console.error('Usage: node move_component.js <ComponentName.vue> --to <group>');
  process.exit(1);
}

const SRC_ROOT = path.resolve(__dirname, '../frontend/src');
const COMPONENTS_ROOT = path.join(SRC_ROOT, 'components');
const DEST_DIR = path.join(COMPONENTS_ROOT, toGroup);
if (!fs.existsSync(DEST_DIR)) fs.mkdirSync(DEST_DIR, { recursive: true });

// Find the file
const matches = glob.sync(`**/${componentName}`, { cwd: COMPONENTS_ROOT, absolute: true });
if (matches.length === 0) {
  console.error(`Component "${componentName}" not found in components/`);
  process.exit(1);
}

const srcPath = matches[0];
const destPath = path.join(DEST_DIR, componentName);
const newImportPath = `@/components/${toGroup}/${componentName}`;

// Move it
fs.renameSync(srcPath, destPath);
console.log(`✅ Moved ${componentName} → ${path.relative(SRC_ROOT, destPath)}`);

// Update aliased imports
const filesToUpdate = glob.sync(`${SRC_ROOT}/**/*.{js,ts,vue}`, { absolute: true });
for (const file of filesToUpdate) {
  let contents = fs.readFileSync(file, 'utf-8');
  const aliasPattern = new RegExp(`@/components/${componentName.replace(/\.vue$/, '')}`, 'g');
  const importStatement = `@/components/${toGroup}/${componentName.replace(/\.vue$/, '')}`;
  const updated = contents.replace(aliasPattern, importStatement);
  if (updated !== contents) {
    fs.writeFileSync(file, updated, 'utf-8');
    console.log(`↻ Updated import in ${path.relative(SRC_ROOT, file)}`);
  }
}

