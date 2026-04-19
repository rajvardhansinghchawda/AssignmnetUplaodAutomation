"""
PIEMR Assignment Upload Automation  v3  (patched for web backend)
=================================================================
Changes from original:
  1. Added --config <json>  flag — reads CONFIG overrides from a JSON file.
     The backend uses this to pass credentials without exposing them on the
     command line.
  2. The blocking  input("Press ENTER...")  prompt is skipped when --config
     is provided (the backend manages the browser lifecycle automatically).

Requirements:
    pip install selenium webdriver-manager

Usage (manual):
    python piemr_assignment_upload.py

Usage (via backend):
    python piemr_assignment_upload.py --config /tmp/piemr_abc123.json
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    UnexpectedAlertPresentException, NoAlertPresentException
)

# ─────────────────────────────────────────────────────
#  CONFIG  ← only edit this block for manual use
#           (backend overwrites these via --config JSON)
# ─────────────────────────────────────────────────────
CONFIG = {
    "login_url":  "https://accsoft.piemr.edu.in/Accsoft_PIEMR/studentLogin.aspx",
    "assign_url": "https://accsoft.piemr.edu.in/accsoft_piemr/Parents/Assignment.aspx",
    "username":   "",
    "password":   "",
    "file":       "",
    "headless":   False,
    "wait":       15,
}
# ─────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════
#  DRIVER SETUP
# ══════════════════════════════════════════════════════
def build_driver(cfg) -> webdriver.Chrome:
    opts = Options()
    if cfg.get("headless"):
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,900")
    opts.add_argument("--disable-notifications")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    # Allow optional hard-coded chromedriver path (set via backend config)
    chromedriver_path = cfg.get("chromedriver_path", "").strip()

    try:
        if chromedriver_path:
            service = Service(chromedriver_path)
        else:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
    except Exception:
        service = Service("chromedriver")

    driver = webdriver.Chrome(service=service, options=opts)
    driver.implicitly_wait(3)
    return driver


# ══════════════════════════════════════════════════════
#  UTILITIES
# ══════════════════════════════════════════════════════
def wait_click(driver, by, value, timeout=15):
    """Wait until clickable then JS-click (avoids ElementNotInteractable)."""
    el = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.2)
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)
    return el


def js_click(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.1)
    driver.execute_script("arguments[0].click();", el)


def dismiss_alert(driver, timeout=3):
    """Accept any open alert/confirm dialog. Returns alert text or None."""
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        txt = alert.text
        print(f"         [Alert] '{txt}' -> OK", flush=True)
        alert.accept()
        return txt
    except (TimeoutException, NoAlertPresentException):
        return None


# ══════════════════════════════════════════════════════
#  STEP 1  LOGIN
# ══════════════════════════════════════════════════════
def login(driver, cfg):
    print("\n[1] Logging in ...", flush=True)
    driver.get(cfg["login_url"])
    time.sleep(2)

    # --- username ---
    for uid in [
        "ctl00_ContentPlaceHolder1_txtUserName",
        "ctl00_ContentPlaceHolder1_txtEnrollNo",
        "txtUserName", "txtEnrollNo", "txtUsername",
    ]:
        try:
            f = driver.find_element(By.ID, uid)
            f.clear(); f.send_keys(cfg["username"]); break
        except NoSuchElementException:
            continue
    else:
        driver.find_element(By.XPATH, "(//input[@type='text'])[1]").send_keys(cfg["username"])

    # --- password ---
    for pid in [
        "ctl00_ContentPlaceHolder1_txtPassword",
        "txtPassword", "txtPass",
    ]:
        try:
            f = driver.find_element(By.ID, pid)
            f.clear(); f.send_keys(cfg["password"]); break
        except NoSuchElementException:
            continue
    else:
        driver.find_element(By.XPATH, "//input[@type='password']").send_keys(cfg["password"])

    # --- submit ---
    for bid in [
        "ctl00_ContentPlaceHolder1_btnLogin",
        "btnLogin", "btnSubmit",
    ]:
        try:
            driver.find_element(By.ID, bid).click(); break
        except NoSuchElementException:
            continue
    else:
        driver.find_element(
            By.XPATH, "//input[@type='submit'] | //button[@type='submit']"
        ).click()

    time.sleep(3)
    dismiss_alert(driver, timeout=2)
    print("    [OK] Logged in  ->  " + driver.title, flush=True)


# ══════════════════════════════════════════════════════
#  STEP 2  NAVIGATE DIRECTLY TO ASSIGNMENTS PAGE
# ══════════════════════════════════════════════════════
def open_assignments_page(driver, cfg):
    driver.get(cfg["assign_url"])
    time.sleep(2)
    dismiss_alert(driver, timeout=2)
    WebDriverWait(driver, cfg["wait"]).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.dlTable"))
    )
    print("    [OK] Assignments page loaded", flush=True)


# ══════════════════════════════════════════════════════
#  STEP 3  SCAN — find subjects with new assignments
# ══════════════════════════════════════════════════════
def scan_subjects(driver):
    results = []
    rows = driver.find_elements(By.CSS_SELECTOR, "table.dlTable tr.GreenPage2")

    for row in rows:
        try:
            subject = row.find_element(
                By.XPATH, ".//span[contains(@id,'Label2')]"
            ).text.strip()

            new_count = int(
                row.find_element(
                    By.XPATH, ".//input[contains(@id,'hdnNewACount')]"
                ).get_attribute("value") or "0"
            )

            if new_count > 0:
                link = row.find_element(
                    By.XPATH, ".//a[contains(@id,'lnkViewNewAssign')]"
                )
                link_id = link.get_attribute("id")
                href    = link.get_attribute("href")

                results.append({
                    "subject":   subject,
                    "new_count": new_count,
                    "link_id":   link_id,
                    "href":      href,
                })
                print(f"    [*]  {subject}  ->  {new_count} new", flush=True)

        except Exception as e:
            print(f"    [!]  Row parse error: {e}", flush=True)

    return results


# ══════════════════════════════════════════════════════
#  STEP 4  UPLOAD  — one assignment row at a time
# ══════════════════════════════════════════════════════
def do_upload(driver, upload_anchor, file_path):
    try:
        js_click(driver, upload_anchor)
        time.sleep(2)
        dismiss_alert(driver, timeout=1)

        file_input = None
        for _ in range(4):
            inputs = driver.find_elements(By.XPATH, "//input[@type='file']")
            if inputs:
                file_input = inputs[0]
                break
            time.sleep(1)

        if not file_input:
            print("         ✗ No file <input> appeared.", flush=True)
            return False

        file_input.send_keys(os.path.abspath(file_path))
        time.sleep(1)

        SUBMIT_XPATHS = [
            "//div[contains(@class,'modal-footer')]//button[not(contains(@class,'close') or contains(@class,'cancel'))]",
            "//div[contains(@class,'modal') and contains(@style,'block')]//input[@type='submit']",
            "//input[@type='submit' and contains(translate(@value,"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'upload')]",
            "//input[@type='submit' and contains(translate(@value,"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'submit')]",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),'upload')]",
            "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ',"
            "'abcdefghijklmnopqrstuvwxyz'),'submit')]",
            "//a[contains(@class,'btn') and (contains(text(),'Upload')"
            " or contains(text(),'Submit') or contains(text(),'Save'))]",
        ]

        clicked = False
        for xp in SUBMIT_XPATHS:
            btns = driver.find_elements(By.XPATH, xp)
            if btns:
                js_click(driver, btns[0])
                clicked = True
                break

        if not clicked:
            print("         ✗ Could not find submit button.", flush=True)
            return False

        time.sleep(2)
        alert_text = dismiss_alert(driver, timeout=4)
        if alert_text and ("success" in alert_text.lower() or "upload" in alert_text.lower()):
            print("         [OK] Upload confirmed by alert.", flush=True)
        else:
            print("         [OK] Upload submitted (no confirmation alert).", flush=True)

        time.sleep(1)
        return True

    except Exception as e:
        print(f"         [X] Upload error: {e}", flush=True)
        dismiss_alert(driver, timeout=2)
        return False


# ══════════════════════════════════════════════════════
#  STEP 4  PROCESS one subject
# ══════════════════════════════════════════════════════
def process_subject(driver, subj, file_path, cfg):
    subject  = subj["subject"]
    link_id  = subj["link_id"]

    print(f"\n   +-- {subject}", flush=True)

    def open_subject():
        driver.get(cfg["assign_url"])
        time.sleep(2)
        dismiss_alert(driver, timeout=2)
        WebDriverWait(driver, cfg["wait"]).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.dlTable"))
        )
        link = WebDriverWait(driver, cfg["wait"]).until(
            EC.presence_of_element_located((By.ID, link_id))
        )
        js_click(driver, link)
        time.sleep(2)
        dismiss_alert(driver, timeout=2)
        WebDriverWait(driver, cfg["wait"]).until(
            EC.presence_of_element_located((By.XPATH, "//tr[contains(@class,'GreenPage2')]"))
        )

    try:
        open_subject()
    except Exception as e:
        print(f"   +-- [X] Could not open subject: {e}", flush=True)
        return 0

    rows_info = []
    rows = driver.find_elements(By.XPATH, "//tr[contains(@class,'GreenPage2')]")
    for row in rows:
        try:
            assig_no = row.find_element(
                By.XPATH, ".//span[contains(@id,'Label4')]"
            ).text.strip()
            due_date = row.find_element(
                By.XPATH, ".//span[contains(@id,'Label5')]"
            ).text.strip()
            btn = row.find_element(
                By.XPATH, ".//a[contains(@id,'btnUpload')]"
            )
            if "re-upload" in btn.text.strip().lower():
                print(f"   |  >> Assignment #{assig_no} already uploaded -- skipping", flush=True)
                continue

            rows_info.append({
                "assig_no": assig_no,
                "due_date": due_date,
                "btn_id":   btn.get_attribute("id"),
            })
        except NoSuchElementException:
            continue

    if not rows_info:
        print(f"   +-- No upload buttons found.", flush=True)
        return 0

    print(f"   |  Found {len(rows_info)} assignment(s)", flush=True)

    uploaded = 0

    for idx, info in enumerate(rows_info, 1):
        print(f"   |  [{idx}/{len(rows_info)}] Assignment #{info['assig_no']}  due {info['due_date']}", flush=True)

        if idx > 1:
            print(f"   |  <- Returning to subject page for next assignment...", flush=True)
            try:
                open_subject()
            except Exception as e:
                print(f"   |  [X] Could not re-open subject: {e}", flush=True)
                continue

        try:
            btn = WebDriverWait(driver, cfg["wait"]).until(
                EC.presence_of_element_located((By.ID, info["btn_id"]))
            )
        except TimeoutException:
            print(f"   |  [!] Button {info['btn_id']} not found -- may already be uploaded, skipping.", flush=True)
            continue

        ok = do_upload(driver, btn, file_path)
        if ok:
            uploaded += 1
            print(f"   |  [OK] Uploaded ({uploaded}/{len(rows_info)}) -- portal redirected to AssignmentView", flush=True)
            time.sleep(1.5)
        else:
            print(f"   |  [X] Failed for #{info['assig_no']}, continuing...", flush=True)

    print(f"   +-- Done: {uploaded}/{len(rows_info)} uploaded for '{subject}'", flush=True)
    return uploaded


# ══════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════
def run(cfg, headless_mode: bool = False):
    if not cfg.get("file"):
        print("ERROR: Set CONFIG['file'] to your file path.")
        return
    if not os.path.exists(cfg["file"]):
        print(f"ERROR: File not found → {cfg['file']}")
        return

    print("=" * 58, flush=True)
    print("  PIEMR Assignment Auto-Uploader  v3", flush=True)
    print("=" * 58, flush=True)
    print(f"  User : {cfg['username']}", flush=True)
    print(f"  File : {cfg['file']}", flush=True)
    print("=" * 58, flush=True)

    driver = build_driver(cfg)
    total  = 0

    try:
        login(driver, cfg)

        print("\n[2] Opening Assignments page ...", flush=True)
        open_assignments_page(driver, cfg)

        print("\n[3] Scanning for new assignments ...", flush=True)
        subjects = scan_subjects(driver)

        if not subjects:
            print("\n  [OK]  No new assignments found -- nothing to do!", flush=True)
        else:
            print(f"\n[4] Uploading to {len(subjects)} subject(s) ...", flush=True)

            for idx, subj in enumerate(subjects, 1):
                print(f"\n  -- Subject {idx}/{len(subjects)} " + "-" * 30, flush=True)
                open_assignments_page(driver, cfg)
                time.sleep(0.5)
                n = process_subject(driver, subj, cfg["file"], cfg)
                total += n

        print(f"\n{'=' * 58}", flush=True)
        print(f"  COMPLETE  —  Total uploads: {total}", flush=True)
        print(f"{'=' * 58}", flush=True)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}", flush=True)
        import traceback; traceback.print_exc()

    finally:
        driver.quit()
        # Only pause for manual runs (not when called by the backend via --config)
        if not headless_mode:
            input("\nPress ENTER to close browser ...")


if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser()
    p.add_argument("--file",     help="Path to file to upload")
    p.add_argument("--username", help="Enrollment number")
    p.add_argument("--password", help="Password")
    p.add_argument("--headless", action="store_true")
    # ── PATCH: backend passes credentials via a temp JSON file ──
    p.add_argument("--config",   help="Path to JSON config file (used by backend)")
    args = p.parse_args()

    # ── PATCH: load config overrides from JSON if --config is given ──
    backend_mode = False
    if args.config:
        backend_mode = True
        with open(args.config) as f:
            file_cfg = json.load(f)
        CONFIG.update(file_cfg)

    # CLI args override JSON (for manual use)
    if args.file:     CONFIG["file"]     = args.file
    if args.username: CONFIG["username"] = args.username
    if args.password: CONFIG["password"] = args.password
    if args.headless: CONFIG["headless"] = True

    run(CONFIG, headless_mode=backend_mode)
