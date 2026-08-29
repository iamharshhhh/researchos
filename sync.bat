@echo off
echo ===================================================
echo 🚀 ResearchOS: Syncing local changes to GitHub...
echo ===================================================
git add .
set datetime=%date:~10,4%-%date:4,2%-%date:7,2% %time:~0,2%:%time:3,2%:%time:6,2%
git commit -m "Update: %datetime%"
git push origin main
echo ===================================================
echo ✅ Done! Changes are live on GitHub & Streamlit Cloud.
echo ===================================================
pause
