#!/bin/bash
# Mac/Linux: run  ./push_to_github.sh   (needs git installed). Create an EMPTY repo on github.com first.
read -p "GitHub username: " U; read -p "Repo name [hospital-bed-occupancy-dashboard]: " R; R=${R:-hospital-bed-occupancy-dashboard}
read -p "Your name (for commits): " N; read -p "Your email (for commits): " E
git config user.name "$N"; git config user.email "$E"; git commit --amend --reset-author --no-edit -q
git remote remove origin 2>/dev/null; git remote add origin "https://github.com/$U/$R.git"
git push -u origin main && echo "DONE: https://github.com/$U/$R"
