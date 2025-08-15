import os
import requests
from io import BytesIO
from PyPDF2 import PdfReader
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.library.uq.edu.au/exams/course/"

def download_past_papers_text(course_code):
    # Save into past_papers/<COURSE_CODE>/
    download_dir = os.path.join(os.getcwd(), "past_papers", course_code)
    os.makedirs(download_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{BASE_URL}{course_code}")
        page.wait_for_load_state("networkidle")

        links = page.locator(f"a:has-text('{course_code}')").all()
        if not links:
            print("No past papers found.")
            browser.close()
            return

        print(f"Found {len(links)} past papers.")
        print("🔑 Please log in to UQ SSO in the browser window that opened.")

        # Open first link to trigger login
        first_link = links[0]
        first_link.click()
        input("After logging in and seeing the PDF viewer, press ENTER...")

        # Get authenticated cookies
        cookies = context.cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}

        # Download and extract text from each paper
        for link in links:
            link_text = link.text_content().strip().replace(" ", "_")
            print(f"\n➡ Processing {link_text}...")

            # Open the link in a new tab to get the PDF URL from iframe
            temp_page = context.new_page()
            temp_page.goto(link.get_attribute("href"))
            temp_page.wait_for_load_state("networkidle")

            iframe = temp_page.query_selector("iframe")
            pdf_url = iframe.get_attribute("src") if iframe else temp_page.url

            # Download PDF
            resp = requests.get(pdf_url, cookies=cookie_dict)
            if resp.status_code == 200 and resp.headers.get("Content-Type", "").startswith("application/pdf"):
                pdf_bytes = BytesIO(resp.content)
                reader = PdfReader(pdf_bytes)
                text = "\n\n".join([page.extract_text() or "" for page in reader.pages])

                # Save text
                save_path = os.path.join(download_dir, f"{link_text}.txt")
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"✅ Text saved: {save_path}")
            else:
                print(f"⚠ Failed to download {link_text} (status {resp.status_code})")

            temp_page.close()

        browser.close()
        print(f"\nAll papers saved as text in: {download_dir}")

if __name__ == "__main__":
    course = input("Course code (e.g., CSSE2310): ").strip().upper()
    download_past_papers_text(course)
