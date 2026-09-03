---
name: auto-github-push
description: Automatically commits and pushes code changes to GitHub immediately after any file modifications.
---

# Auto GitHub Push Skill

## Use this skill when
- You (the agent) have finished making file modifications, code enhancements, refactoring, or bug fixes requested by the user.
- The project changes are stable and ready to be stored.

## Do not use this skill when
- Code changes result in build errors or failing tests.
- The user explicitly requests NOT to push changes to remote.

## Instructions
1. As soon as you complete any file modification or feature implementation, you MUST instantly stage and save the work using Git.
2. Formulate a short, descriptive commit message using the Conventional Commits format (e.g., "feat: update index.js", "fix: resolve layout crash").
3. Execute the staging and commit commands in the terminal:
   ```bash
   git add .
   git commit -m "<your_conventional_commit_message>"
   ```
4. Immediately follow up by pushing the changes directly to the remote repository branch:
   ```bash
   git push origin \$(git branch --show-current)
   ```
5. Confirm to the user that the changes have been saved and pushed automatically.
