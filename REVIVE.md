# How to revive after Codespace sleeps

## Step 1 - PowerShell
Set-Alias gh "C:\Program Files\GitHub CLI\gh.exe"
gh codespace ssh --codespace animated-giggle-qvp6r6v59r7jh997w

## Step 2 - Inside the Codespace
cd /workspaces/legal-demo && bash start.sh

## Step 3 - New PowerShell window
gh codespace code --codespace animated-giggle-qvp6r6v59r7jh997w --web

## Step 4 - In browser PORTS tab
Right-click 8501 -> Port Visibility -> Public
Click globe icon

## Verify
curl http://localhost:8000/health   # should say {"status":"ok"}
