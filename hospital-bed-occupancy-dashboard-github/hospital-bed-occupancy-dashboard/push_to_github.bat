@echo off
REM Windows: double-click this file (needs Git installed). Create an EMPTY repo on github.com first.
set /p U=GitHub username: 
set /p R=Repo name (e.g. hospital-bed-occupancy-dashboard): 
set /p N=Your name (for commits): 
set /p E=Your email (for commits): 
git config user.name "%N%"
git config user.email "%E%"
git commit --amend --reset-author --no-edit -q
git remote remove origin 2>nul
git remote add origin https://github.com/%U%/%R%.git
git push -u origin main
echo.
echo If push succeeded, open: https://github.com/%U%/%R%
pause
