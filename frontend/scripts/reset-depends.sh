#!/bin/bash
echo "🧹 Removing node_modules and lockfile..."
rm -rf node_modules package-lock.json

echo "🧼 Cleaning npm cache..."
npm cache clean --force

echo "📦 Installing clean dependencies..."
npm install

echo "✅ Done. You're running fresh!"
