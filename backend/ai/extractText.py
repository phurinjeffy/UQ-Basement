import os
import sys
import time
import glob
import re
import tempfile
import shutil
import boto3
from botocore.client import Config
from urllib.parse import urlparse
from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyPDF2 import PdfReader

import sys

sys.stdout.reconfigure(encoding="utf-8")

# Always use project root for past_papers dir (not used for downloads anymore)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# S3/Supabase config
S3_ENDPOINT_URL = "https://hwcaroqjyelhfiqvuskq.storage.supabase.co/storage/v1/s3"
S3_ACCESS_KEY_ID = os.environ.get("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.environ.get("S3_SECRET_ACCESS_KEY")
S3_BUCKET = "pdfs"  # Change to your bucket name if different

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


def s3_client():
    session = boto3.session.Session()
    return session.client(
        service_name="s3",
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        endpoint_url=S3_ENDPOINT_URL,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def s3_file_exists(s3, s3_key):
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=s3_key)
        return True
    except Exception:
        return False


def upload_to_s3(file_path, s3_key):
    s3 = s3_client()
    with open(file_path, "rb") as f:
        s3.upload_fileobj(f, S3_BUCKET, s3_key)
    print(f"[S3] Uploaded {file_path} to {S3_BUCKET}/{s3_key}")


def download_pdfs(course_code):
    # Use a temporary directory for downloads
    download_dir = tempfile.mkdtemp(prefix=f"{course_code}_pdfs_")

    # 1. Launch visible browser for login
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "plugins.always_open_pdf_externally": True,
            "download.prompt_for_download": False,
            "download.default_directory": download_dir,
        },
    )
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

    # Wait until at least one PDF link appears (login complete)
    pdf_elements = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href$='.pdf']"))
    )
    print(f"[✓] Login detected. Found {len(pdf_elements)} PDF links.")

    # Get PDF URLs
    pdf_urls = [el.get_attribute("href") for el in pdf_elements]

    # Extract cookies from the visible browser
    cookies = driver.get_cookies()
    driver.quit()
    print("[+] Login complete. Switching to headless mode for background downloads...")

    # 2. Launch headless browser for background downloads
    headless_options = Options()
    headless_options.add_argument("--headless=new")
    headless_options.add_argument("--window-size=1920,1080")
    headless_options.add_experimental_option(
        "prefs",
        {
            "plugins.always_open_pdf_externally": True,
            "download.prompt_for_download": False,
            "download.default_directory": download_dir,
        },
    )
    headless_driver = webdriver.Chrome(options=headless_options)
    headless_driver.get(course_url)
    # Set cookies in headless browser
    for cookie in cookies:
        cookie_dict = cookie.copy()
        # Remove 'sameSite' if present (not accepted by Selenium add_cookie)
        cookie_dict.pop("sameSite", None)
        try:
            headless_driver.add_cookie(cookie_dict)
        except Exception as e:
            print(f"[!] Failed to add cookie: {cookie_dict.get('name')}: {e}")
    headless_driver.refresh()

    # Wait for PDF links to appear again (should be instant)
    wait2 = WebDriverWait(headless_driver, 30)
    pdf_elements2 = wait2.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href$='.pdf']"))
    )
    print(f"[✓] Headless mode: Found {len(pdf_elements2)} PDF links.")

    s3 = s3_client()
    # Download PDFs one at a time, skip if already in S3
    for i, url in enumerate(pdf_urls, start=1):
        pdf_name = os.path.basename(url)
        s3_key = f"{course_code}/{pdf_name}"
        if s3_file_exists(s3, s3_key):
            print(f"[S3] Skipping {pdf_name}, already exists in S3.")
            continue
        print(f"[{i}/{len(pdf_urls)}] Downloading: {pdf_name}")
        headless_driver.get(url)
        time.sleep(5)  # adjust if downloads are slow
        # After download, upload to S3, then delete local file
        local_pdf = os.path.join(download_dir, pdf_name)
        if os.path.exists(local_pdf):
            try:
                upload_to_s3(local_pdf, s3_key)
                os.remove(local_pdf)
                print(f"[Local] Deleted {local_pdf}")
            except Exception as e:
                print(f"[S3] Upload failed for {local_pdf}: {e}")

    # Clean up temp directory
    shutil.rmtree(download_dir, ignore_errors=True)
    print(f"[Temp] Removed temp download dir {download_dir}")

    headless_driver.quit()
    print("[+] Background downloads complete.")
    time.sleep(2)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        course = sys.argv[1].strip().upper()
    else:
        course = input("Course code (e.g., CSSE2310): ").strip().upper()

    # Only support download mode now
    download_pdfs(course)
