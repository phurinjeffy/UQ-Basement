import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.library.uq.edu.au/exams/course/"

def download_past_papers(course_code):
    # Create folder for downloads
    download_dir = os.path.join(os.getcwd(), course_code)
    os.makedirs(download_dir, exist_ok=True)

    # Configure Chrome options
    options = Options()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)

    # Optional: make it headless if you don't want browser to appear
    # options.add_argument("--headless=new")

    # Launch Chrome with temporary profile (no conflicts)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        url = f"{BASE_URL}{course_code}"
        driver.get(url)
        time.sleep(5)  # wait for page to load fully (adjust if slow)

        # Find all links for this course code
        links = driver.find_elements(By.XPATH, f"//a[contains(text(), '{course_code}')]")
        if not links:
            print("No past papers found.")
            return

        print(f"Found {len(links)} past papers. Downloading...")

        for link in links:
            paper_name = link.text.strip().replace(" ", "_")
            print(f"Downloading {paper_name}...")
            driver.execute_script("arguments[0].click();", link)
            time.sleep(20)  # wait for download to finish (adjust if needed)

        print(f"All papers saved to: {download_dir}")

    finally:
        driver.quit()

if __name__ == "__main__":
    course = input("Course code (e.g., CSSE2310): ").strip().upper()
    download_past_papers(course)
