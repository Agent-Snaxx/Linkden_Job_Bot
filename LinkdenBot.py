# local_job_bot.py — FINAL 2025 UNBREAKABLE (CHEVRON FIXED)
import os
import csv
import random
import asyncio
import re
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

SEARCH_TERM = os.getenv("SEARCH_TERM", "DevOps Engineer")
RESUME_PATH = os.getenv("RESUME_PATH", "eric_wilson_resume.pdf")
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
COOKIES_FILE = "linkedin_cookies.json"
LOG_FILE = "applied_jobs.csv"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Platform", "Search Term", "Job Title", "Company", "Location", "Status", "Notes"])

async def ask_human(question: str) -> str:
    print(f"\n[PAUSE] {question}")
    return input("→ Your answer: ").strip()

async def save_cookies(context):
    await context.storage_state(path=COOKIES_FILE)
    print(f"Cookies saved → {COOKIES_FILE}")

async def load_cookies(browser):
    if os.path.exists(COOKIES_FILE):
        context = await browser.new_context(storage_state=COOKIES_FILE)
        print(f"Loaded cookies from {COOKIES_FILE}")
        return context
    return None

async def login_linkedin(page):
    await page.goto("https://www.linkedin.com/login")
    await page.fill('input[name="session_key"]', os.getenv("LINKEDIN_EMAIL"))
    await page.fill('input[name="session_password"]', os.getenv("LINKEDIN_PASS"))
    await page.click('button[type="submit"]')
    await page.wait_for_url("https://www.linkedin.com/feed/**", timeout=15000)
    print("Logged in to LinkedIn")

async def handle_resume_upload(page):
    file_input = await page.query_selector("input[type='file']")
    if not file_input or not await file_input.is_visible():
        return
    saved_btn = await page.query_selector("button, div, span", has_text=re.compile("use.*resume|saved|on file", re.I))
    if saved_btn and await saved_btn.is_visible():
        await saved_btn.click()
        print("Using LinkedIn saved resume")
        return
    await file_input.set_input_files(RESUME_PATH)
    print("Uploaded resume from file")

async def apply_linkedin():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=HEADLESS,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await load_cookies(browser) or await browser.new_context()
        page = await context.new_page()

        if not os.path.exists(COOKIES_FILE):
            await login_linkedin(page)
            await save_cookies(context)
            page = await context.new_page()

        search_url = f"https://www.linkedin.com/jobs/search/?keywords={SEARCH_TERM.replace(' ', '%20')}&f_TPR=r604800"
        await page.goto(search_url)

        try:
            await page.wait_for_selector("li[data-occludable-job-id]", timeout=30000)
            print("Job list loaded — job cards detected")
        except Exception as e:
            print(f"Failed to load search page: {e}")
            await page.screenshot(path="debug_search_failed.png", full_page=True)
            await browser.close()
            return

        applied_count = 0
        seen_jobs = set()
        page_num = 1

        while True:
            print(f"\n--- PAGE {page_num} ---")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

            job_cards = await page.query_selector_all("li[data-occludable-job-id]")
            print(f"Found {len(job_cards)} job cards")

            if not job_cards:
                print("No jobs found. Stopping.")
                break

            for card in job_cards:
                try:
                    job_id = await card.get_attribute("data-occludable-job-id")
                    if job_id in seen_jobs:
                        continue
                    seen_jobs.add(job_id)

                    await card.scroll_into_view_if_needed()
                    await card.click()
                    await page.wait_for_timeout(5000)

                    title = "Unknown"
                    company = "Unknown"
                    location = "Unknown"
                    title_elem = await page.query_selector("h1.top-card-layout__title, h1")
                    if title_elem:
                        title = await title_elem.inner_text()
                    company_elem = await page.query_selector("a.topcard__org-name-link, span.topcard__org-name")
                    if company_elem:
                        company = await company_elem.inner_text()
                    location_elem = await page.query_selector("span.topcard__location")
                    if location_elem:
                        location = await location_elem.inner_text()
                    title = title.strip()
                    company = company.strip()
                    location = location.strip()

                    easy_apply_span = await page.query_selector("span.artdeco-button__text:has-text('Easy Apply')")
                    easy_apply_btn = None
                    if easy_apply_span:
                        easy_apply_btn = await easy_apply_span.evaluate_handle("node => node.closest('button')")
                    if not easy_apply_btn:
                        easy_apply_btn = await page.query_selector("button.jobs-apply-button--top-card, button:has-text('Easy Apply')")

                    if not easy_apply_btn or not await easy_apply_btn.is_visible():
                        print(f"Skipped (No Easy Apply): {title} @ {company}")
                        continue

                    await easy_apply_btn.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)
                    await easy_apply_btn.click()
                    await page.wait_for_timeout(4000)

                    step = 1
                    while True:
                        await handle_resume_upload(page)
                        textareas = await page.query_selector_all("textarea")
                        for ta in textareas:
                            if not await ta.is_visible():
                                continue
                            label = await ta.get_attribute("aria-label") or ""
                            placeholder = await ta.get_attribute("placeholder") or ""
                            full_text = f"{label} {placeholder}".lower()
                            if any(k in full_text for k in ["why", "tell us", "cover", "motivation", "experience"]):
                                answer = await ask_human(f"Q{step}: {label or placeholder}")
                                await ta.fill(answer)

                        submit_btn = await page.query_selector("button[aria-label*='Submit']")
                        review_btn = await page.query_selector("button[aria-label*='Review']")
                        next_btn = await page.query_selector("button[aria-label*='Continue'], button[aria-label*='Next']")

                        if submit_btn and await submit_btn.is_enabled():
                            await submit_btn.click()
                            await page.wait_for_timeout(3000)
                            print(f"APPLIED: {title} @ {company} ({location})")
                            with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
                                writer = csv.writer(f)
                                writer.writerow(["LinkedIn", SEARCH_TERM, title, company, location, "Applied", ""])
                            applied_count += 1
                            close_modal = await page.query_selector("button[aria-label='Dismiss'], button.msg-overlay-bubble-header__close-button, button:has(svg[data-test-icon='close-small'])")
                            if close_modal and await close_modal.is_visible():
                                await close_modal.click()
                                await page.wait_for_timeout(1500)
                                print("Closed success modal")
                            break
                        elif review_btn and await review_btn.is_enabled():
                            await review_btn.click()
                            await page.wait_for_timeout(2000)
                        elif next_btn and await next_btn.is_enabled():
                            await next_btn.click()
                            await page.wait_for_timeout(2000)
                            step += 1
                        else:
                            print(f"Form stuck. Dismissing: {title}")
                            dismiss = await page.query_selector("button[aria-label='Dismiss']")
                            if dismiss:
                                await dismiss.click()
                            break

                    await asyncio.sleep(random.uniform(25, 45))

                except Exception as e:
                    print(f"Error on job: {e}")
                    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow(["LinkedIn", SEARCH_TERM, "ERROR", "", "", "Failed", str(e)])

            # === PAGINATION: CHEVRON + TEXT + BULLETPROOF ===
            next_btn = None
            next_btn = await page.query_selector("button[aria-label='Next']")
            if not next_btn:
                next_btn = await page.query_selector("button:has(svg use[href='#chevron-right-small'])")
            if not next_btn:
                next_btn = await page.query_selector("button:has(svg[data-test-icon='chevron-right-small'])")
            if not next_btn:
                next_btn = await page.query_selector("button:has-text('Next')")

            if next_btn and await next_btn.is_enabled():
                print(f"\nADVANCING TO PAGE {page_num + 1}...")
                await next_btn.scroll_into_view_if_needed()
                await next_btn.click(force=True)
                await page.wait_for_timeout(8000)
                await page.wait_for_selector("li[data-occludable-job-id]", timeout=15000)
                page_num += 1
            else:
                print("NO MORE PAGES — BOT COMPLETE")
                break

        await browser.close()
        print(f"\nDONE. Applied to {applied_count} jobs. → {LOG_FILE}")

if __name__ == "__main__":
    asyncio.run(apply_linkedin())
