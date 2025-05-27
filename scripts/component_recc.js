// scripts/classify_components.js

import fs from 'fs';
import path from 'path';
import glob from 'glob';

const COMPONENTS_DIR = path.resolve('frontend/src/components');

const GROUPS = {
  base: ['Base', 'Input', 'Button'],
  charts: ['Chart', 'Breakdown', 'Graph'],
  tables: ['Table', 'Grid'],
  forms: ['Upload', 'CSV', 'Form', 'Input', 'Selector', 'Token'],
  layout: ['Layout', 'Navbar', 'Shell'],
  widgets: ['Refresh', 'Embed', 'Calendar', 'Settings'],
  forecast: ['Forecast'],
  recurring: ['Recurring'],
};

function suggestGroup(filename) {
  for (const [group, keywords] of Object.entries(GROUPS)) {
    if (keywords.some(k => filename.includes(k))) {
      return group;
    }
  }
  return 'unclassified';
}

function classifyComponents() {
  const files = glob.sync(`${COMPONENTS_DIR}/**/*.vue`);
  const report = {};

  files.forEach(file => {
    const name = path.basename(file);
    const suggested = suggestGroup(name);
    if (!report[suggested]) report[suggested] = [];
    report[suggested].push(path.relative(COMPONENTS_DIR, file));
  });

  console.log('🧠 Suggested Component Groupings:\n');
  for (const [group, items] of Object.entries(report)) {
    console.log(`📁 ${group}/`);
    items.forEach(f => console.log(`   - ${f}`));
  }
}

classifyComponents();
