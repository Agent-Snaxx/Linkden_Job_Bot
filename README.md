# Linkden_Job_Bot
Automated Linkden Job Bot
# Local Job Bot (2025 Edition)
Automated LinkedIn Easy-Apply job submission bot using **Python**, **Playwright**, and **dotenv**.  
This version is the **2025 Unbreakable Release** featuring full LinkedIn CAPTCHA-safe flows, persistent cookies, human-prompted text answers, resume auto-upload, pagination chevron-fix, and robust error handling.

---

## Features
- 🔐 **Login once** → bot reuses cookies (linkedin_cookies.json)
- 📄 **Auto-upload resume** or use LinkedIn’s saved resume
- 🧠 **Human-assist prompts** for text questions (cover letters, explain-this, etc.)
- 🔍 **Search filter by keyword** (from `.env`)
- 📜 **CSV logging** of every submission (`applied_jobs.csv`)
- 🛰️ **Unbreakable pagination** (Next button, Chevron-right, fallback-scan)
- 🚫 **Skip non-Easy-Apply jobs** automatically
- 🎯 **Weekly jobs only** (past 7 days)
- 💾 **Full crash-resilience** (screenshots saved on errors)
- ✔️ **Production-ready async Playwright**

---

## Requirements
Install these before running:

```bash
pip install playwright python-dotenv
playwright install chromium

