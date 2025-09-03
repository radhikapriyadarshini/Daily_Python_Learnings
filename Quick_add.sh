# quick_add.sh - For Unix/Linux/Mac systems
#!/bin/bash

echo "🚀 Quick Add - Daily Python Learning Entry"
echo "=========================================="

# Run the Python script in interactive mode
python3 auto_updater.py

# If successful, add and commit changes to git
if [ $? -eq 0 ]; then
    echo ""
    echo "📦 Committing changes to Git..."
    
    git add README.md skills-tracker.html
    
    # Get the latest day number for commit message
    LATEST_DAY=$(grep -o "| [0-9]\+ |" README.md | grep -o "[0-9]\+" | tail -1)
    PROJECT_TITLE=$(grep "| ${LATEST_DAY} |" README.md | cut -d'|' -f3 | xargs)
    
    git commit -m "📚 Day ${LATEST_DAY}: ${PROJECT_TITLE}

Auto-updated README.md and skills-tracker.html
- Added new learning entry for Day ${LATEST_DAY}
- Updated progress stats and skill levels
- Maintained consistent formatting"

    echo "✅ Changes committed successfully!"
    echo "💡 Don't forget to: git push"
else
    echo "❌ Entry creation failed. No changes committed."
fi
