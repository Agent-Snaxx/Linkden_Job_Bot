# Notes – Architecture & Behavior

This bot is built for maximum stability, minimal breakage, and zero babysitting.  
Below is an overview of important internal behaviors and design decisions.

---

## 1. Login Flow
- Logs into LinkedIn **only on first run**
- Saves cookies to `linkedin_cookies.json`
- All future runs open authenticated immediately
- If cookies expire → automatically triggers login again

---

## 2. Resume Handling
When a job uses LinkedIn’s saved resume:
- Bot checks for “Use this resume / Saved / On File”
- If available → it selects that
- Otherwise → bot uploads the file at `RESUME_PATH`

---

## 3. Human-Assist Mode
Whenever LinkedIn asks:
- “Tell us why you are a fit”
- “Cover letter”
- “Describe your experience”
- “Why do you want this role”

The bot **pauses** and asks you:
