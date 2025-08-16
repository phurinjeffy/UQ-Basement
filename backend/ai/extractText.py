import os
import sys
import time
import glob
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyPDF2 import PdfReader

BASE_URL = "https://www.library.uq.edu.au/exams/course/"

def clean_filename(course_code, original_name):
    """
    Convert 'Semester_Two_Examinations_2024_CSSE2310.pdf'
    into 'CSSE2310_Sem2_2024.txt'
    """
    name = original_name.replace(".pdf", "")
    # Extract semester
    sem_match = re.search(r"Semester[_ ](One|Two)", name, re.IGNORECASE)
    semester = "Sem1" if sem_match and sem_match.group(1).lower() == "one" else "Sem2"
    # Extract year
    year_match = re.search(r"\d{4}", name)
    year = year_match.group(0) if year_match else "UnknownYear"
    # Combine clean name
    return f"{course_code}_{semester}_{year}.txt"


def download_pdfs(course_code):
    download_dir = os.path.join(os.getcwd(), "past_papers", course_code)
    os.makedirs(download_dir, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("prefs", {
        "plugins.always_open_pdf_externally": True,
        "download.prompt_for_download": False,
        "download.default_directory": download_dir
    })

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 180)

    course_url = f"{BASE_URL}{course_code}"
    print(f"[+] Opening course page: {course_url}")
    driver.get(course_url)

    # Click login button
    try:
        login_btn = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "auth-button")))
        print("[+] Clicking login button...")
        login_btn.click()
    except:
        print("[!] Login button not found, maybe already logged in?")

    print("[i] Waiting for UQ login + Duo Mobile authentication...")

    # Wait until at least one PDF link appears
    pdf_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href$='.pdf']")))
    print(f"[✓] Login detected. Found {len(pdf_elements)} PDF links.")

    # Get PDF URLs
    pdf_urls = [el.get_attribute("href") for el in pdf_elements]

    # Download PDFs one at a time
    for i, url in enumerate(pdf_urls, start=1):
        print(f"[{i}/{len(pdf_urls)}] Downloading: {os.path.basename(url)}")
        driver.get(url)
        time.sleep(5)  # adjust if downloads are slow

    driver.quit()
    print("[+] Chrome downloads triggered. Waiting for files to finish...")

    time.sleep(5)  # wait for downloads

def extract_text_from_pdfs(course_code):
    download_dir = os.path.join(os.getcwd(), "past_papers", course_code)
    # Extract text and save with clean names
    pdf_files = glob.glob(os.path.join(download_dir, "*.pdf"))
    for pdf_file in pdf_files:
        original_name = os.path.basename(pdf_file)
        clean_name = clean_filename(course_code, original_name)
        txt_path = os.path.join(download_dir, clean_name)
        print(f"➡ Extracting {original_name} → {clean_name}")

        try:
            with open(pdf_file, "rb") as f:
                reader = PdfReader(f)
                text = "\n\n".join([page.extract_text() or "" for page in reader.pages])
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"✅ Text saved: {txt_path}")
        except Exception as e:
            print(f"⚠ Failed to extract {original_name}: {e}")

    print(f"\n[✓] All papers processed and saved in: {download_dir}")

def download_and_extract(course_code):
    download_pdfs(course_code)
    extract_text_from_pdfs(course_code)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        course = sys.argv[1].strip().upper()
    else:
        course = input("Course code (e.g., CSSE2310): ").strip().upper()

    # Optional second argument: mode
    mode = sys.argv[2] if len(sys.argv) > 2 else None
    if mode == "download":
        download_pdfs(course)
    elif mode == "extract":
        extract_text_from_pdfs(course)
    else:
        download_and_extract(course)
