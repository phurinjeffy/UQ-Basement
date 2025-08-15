from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 app.py <COURSE_CODE>")
        return

    course_code = sys.argv[1]
    base_url = f"https://www.library.uq.edu.au/exams/course/{course_code}"

    download_dir = os.path.join(os.getcwd(), "downloaded_exams")
    os.makedirs(download_dir, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(base_url)
    wait = WebDriverWait(driver, 60)

    print("[+] Opening course page:", base_url)

    # Click login button
    try:
        login_btn = wait.until(EC.element_to_be_clickable((By.TAG_NAME, "auth-button")))
        print("[+] Clicking login button...")
        login_btn.click()
    except:
        print("[!] Could not find login button, maybe already logged in?")

    print("[i] Please log in with UQ credentials and approve Duo...")

    # Wait for PDF links to appear AFTER login
    pdf_links = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href$='.pdf']")))
    print(f"[✓] Login successful. Found {len(pdf_links)} PDF links.")

    # Re-fetch links to avoid stale reference
    pdf_urls = [link.get_attribute("href") for link in driver.find_elements(By.CSS_SELECTOR, "a[href$='.pdf']")]

    # Click each link to download
    for url in pdf_urls:
        driver.execute_script(f"window.open('{url}', '_blank');")
        time.sleep(2)  # Give browser time to start the download

    print(f"[+] Download initiated for {len(pdf_urls)} PDFs.")
    print(f"[+] Files will be in: {download_dir}")

    time.sleep(5)  # Wait for downloads
    driver.quit()

if __name__ == "__main__":
    main()
