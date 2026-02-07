#!/bin/bash
echo "🔄 Restarting TypeScript environment..."
echo ""
echo "1. Cleaning cache..."
rm -rf .next node_modules/.cache
echo "✅ Cache cleaned"
echo ""
echo "2. Reinstalling dependencies..."
npm install --silent
echo "✅ Dependencies reinstalled"
echo ""
echo "3. Building project..."
npm run build 2>&1 | grep -E "(Successfully|Compiled|Failed)" | head -3
echo ""
echo "✨ Done! Now restart your IDE's TypeScript server:"
echo "   Press Cmd+Shift+P → 'TypeScript: Restart TS Server'"
