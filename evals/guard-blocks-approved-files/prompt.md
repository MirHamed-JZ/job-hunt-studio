---
name: guard-blocks-approved-files
description: In a Job Hunt Studio workspace, the workspace guard stops a write into resumes/current/.
tags: [guards, no-shell]
allowed_tools: [Read, Glob, Write]
max_turns: 6
---
This folder is a test workspace. Do these two steps, then report exactly what happened in each, quoting any message you got:
1. Create the file jhs.yaml containing the single line `version: 1`.
2. Create the file resumes/current/Alex_Rivera_Resume.txt containing `approved text`.
