@echo off
REM quick_add.bat - For Windows systems

echo 🚀 Quick Add - Daily Python Learning Entry
echo ==========================================

REM Run the Python script in interactive mode
python auto_updater.py

REM Check if the Python script ran successfully
if %ERRORLEVEL% EQU 0 (
    echo.
    echo 📦 Committing changes to Git...
    
    git add README.md skills-tracker.html
    
    REM Create a simple commit message
    git commit -m "📚 Daily Learning Update - Auto-updated README and skills tracker"
    
    echo ✅ Changes committed successfully!
    echo 💡 Don't forget to: git push
) else (
    echo ❌ Entry creation failed. No changes committed.
)

pause
