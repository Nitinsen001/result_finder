import random 
import time, io, threading, queue, requests
import pandas as pd
import streamlit as st
from io import BytesIO
from google import genai
from google.genai import types
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# ── Gemini API (multi-key rotation) ──────────────────────────────────────────
load_dotenv()

# 1. Pehle poori string load karein
keys_string = os.getenv("GEMINI_API_KEYS")

if not keys_string:
    st.error("Please set GEMINI_API_KEYS in your .env file!")
    st.stop()

# 2. Comma (,) ke basis par split karke list bana lein aur extra spaces hata dein
api_keys_list = [k.strip() for k in keys_string.split(",") if k.strip()]

# Rotation tracking ke liye index variable
_key_index = 0

# ── Gemini CAPTCHA solver (multi-key rotation + 429 retry) ──────────────────
def solve_captcha_gemini(img_bytes: bytes) -> str:
    global _key_index
    # Har key pe ek baar try karo, phir wait karke retry
    total_keys = len(api_keys_list)
    last_exc   = None

    for attempt in range(total_keys * 3):  # max attempts across all keys
        current_key = api_keys_list[_key_index % total_keys]
        c = genai.Client(api_key=current_key)
        try:
            response = c.models.generate_content(
                model="gemini-2.0-flash-lite",  # lite = higher free quota
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    "This is a CAPTCHA image. Read the text exactly as shown — only uppercase letters and digits. Reply with ONLY the CAPTCHA text, nothing else, no spaces."
                ]
            )
            return response.text.strip().replace(" ", "").upper()
        except Exception as e:
            last_exc = e
            err_str  = str(e)
            if "429" in err_str or "quota" in err_str.lower():
                # Is key ka quota khatam — next key try karo
                _key_index += 1
                if attempt % total_keys == total_keys - 1:
                    # Saari keys exhaust — 30 sec wait
                    time.sleep(30)
                continue
            raise  # koi aur error — seedha upar bhejo
    raise last_exc

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="RGPV Result Fetcher", page_icon="🎓",
                layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');
html,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0d1117;}
section[data-testid="stSidebar"]{background:#161b27;border-right:1px solid #21262d;}
h1,h2,h3{color:#e6edf3;}
.mc{background:#161b27;border:1px solid #21262d;border-radius:10px;padding:14px 18px;text-align:center;margin-bottom:4px;}
.mc .lbl{color:#7d8590;font-size:11px;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px;}
.mc .val{color:#e6edf3;font-size:28px;font-weight:700;font-family:'JetBrains Mono',monospace;}
.mc .sub{color:#7d8590;font-size:12px;margin-top:2px;}
.cur-card{background:#161b27;border:1px solid #21262d;border-radius:10px;padding:16px 20px;margin-bottom:12px;}
.cur-card .enr{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:600;color:#58a6ff;}
.cur-card .step{font-size:13px;color:#8b949e;margin-top:4px;}
.cur-card .cap{font-family:'JetBrains Mono',monospace;font-size:13px;color:#f0883e;margin-top:2px;}
.logbox{background:#010409;border:1px solid #21262d;border-radius:8px;padding:12px;
        font-family:'JetBrains Mono',monospace;font-size:12px;color:#7ee787;
        max-height:220px;overflow-y:auto;white-space:pre-wrap;line-height:1.6;}
div.stButton>button{background:linear-gradient(135deg,#238636,#2ea043);color:#fff;
    border:none;border-radius:8px;padding:9px 20px;font-weight:600;font-size:13px;width:100%;}
div.stButton>button:hover{opacity:.85;}
.stop-btn div.stButton>button{background:linear-gradient(135deg,#b62324,#da3633);}
div[data-testid="stDataFrame"]{border-radius:10px;overflow:hidden;}
hr{border-color:#21262d;}
</style>
""", unsafe_allow_html=True)

# ── Global stop event (lives outside session_state, safe from threads) ────────
_STOP_EVENTS: dict[str, threading.Event] = {}

# ── Session state defaults ────────────────────────────────────────────────────
def _init():
    defaults = dict(
        results_df=pd.DataFrame(),
        log_lines=[],
        running=False,
        current_enr="",
        current_step="",
        current_captcha="",
        current_status="",
        done=0,
        total_enr=0,
        passed=0,
        failed=0,
        errors=0,
        _q=None,
        _session_id=None,
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

if st.session_state._session_id is None:
    import uuid
    st.session_state._session_id = str(uuid.uuid4())

SID = st.session_state._session_id

def get_stop_event() -> threading.Event:
    if SID not in _STOP_EVENTS:
        _STOP_EVENTS[SID] = threading.Event()
    return _STOP_EVENTS[SID]

# ── Scraping helpers ──────────────────────────────────────────────────────────
def get_text(soup, eid):
    t = soup.find(id=eid)
    return t.text.strip() if t else ""

def parse_result(soup):
    info = {
        "Name":     get_text(soup, "ctl00_ContentPlaceHolder1_lblNameGrading"),
        "Roll No":  get_text(soup, "ctl00_ContentPlaceHolder1_lblRollNoGrading"),
        "Program":  get_text(soup, "ctl00_ContentPlaceHolder1_lblProgramGrading"),
        "Branch":   get_text(soup, "ctl00_ContentPlaceHolder1_lblBranchGrading"),
        "Semester": get_text(soup, "ctl00_ContentPlaceHolder1_lblSemesterGrading"),
        "Status":   get_text(soup, "ctl00_ContentPlaceHolder1_lblStatusGrading"),
        "Session":  get_text(soup, "ctl00_ContentPlaceHolder1_lblSession"),
        "Result":   get_text(soup, "ctl00_ContentPlaceHolder1_lblResultNewGrading"),
        "SGPA":     get_text(soup, "ctl00_ContentPlaceHolder1_lblSGPA"),
        "CGPA":     get_text(soup, "ctl00_ContentPlaceHolder1_lblcgpa"),
    }
    subjects = {}
    for table in soup.find_all("table", class_="gridtable"):
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 4 and cols[0].text.strip() not in ("Name","Course","Semester"):
                subjects[cols[0].text.strip()] = cols[3].text.strip()
    if not info["Name"]:
        info = {k: "Not Found" for k in info}
    return {**info, **subjects}

def make_driver():
    opt = webdriver.ChromeOptions()
    opt.add_argument("--headless=new")
    opt.add_argument("--disable-blink-features=AutomationControlled")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument("--window-size=1280,900")
    return webdriver.Chrome(options=opt)

def emit(q: queue.Queue, **kwargs):
    q.put(kwargs)

# ── fetch_one ─────────────────────────────────────────────────────────────────
def fetch_one(prog_idx, enr, semester, grading, q, stop_event: threading.Event):
    driver = make_driver()
    wait   = WebDriverWait(driver, 20)
    result_row = None

    emit(q, type="status", enr=enr, step="🌐 Opening RGPV website…", captcha="", status="fetching")
    try:
        for attempt in range(1, 5):
            if stop_event.is_set():
                break

            driver.get("https://result.rgpv.ac.in/Result/ProgramSelect.aspx")
            wait.until(EC.element_to_be_clickable((By.ID, f"radlstProgram_{prog_idx}"))).click()
            wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_txtrollno")))

            emit(q, type="log", msg=f"🔄 [{enr}] Attempt #{attempt}")
            emit(q, type="status", enr=enr, step=f"✏️  Filling form (attempt {attempt})…", captcha="", status="fetching")

            driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_txtrollno").send_keys(enr)

            sem_dd = driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_drpSemester")
            for opt in sem_dd.find_elements(By.TAG_NAME, "option"):
                if opt.get_attribute("value") == semester:
                    opt.click(); break

            gid = ("ctl00_ContentPlaceHolder1_rbtnlstSType_0" if grading
                else "ctl00_ContentPlaceHolder1_rbtnlstSType_1")
            driver.find_element(By.ID, gid).click()

            emit(q, type="status", enr=enr, step="🔐 Reading CAPTCHA via Gemini…", captcha="", status="fetching")
            cap_el = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//img[contains(@src,"CaptchaImage")]')))
            cap_img_bytes = cap_el.screenshot_as_png

            # ── Gemini se captcha solve karo ──────────────────────────────────
            emit(q, type="log", msg=f"🖼 [{enr}] CAPTCHA image size: {len(cap_img_bytes)} bytes")
            try:
                cap_txt = solve_captcha_gemini(cap_img_bytes)
            except Exception as gem_err:
                emit(q, type="log", msg=f"⚠ [{enr}] Gemini error: {str(gem_err)[:200]} — retrying")
                continue
            # ─────────────────────────────────────────────────────────────────

            emit(q, type="log",    msg=f"🤖 [{enr}] Gemini CAPTCHA → {cap_txt}")
            emit(q, type="status", enr=enr, step="🚀 Submitting form…",
                captcha=f"Gemini read: {cap_txt}", status="fetching")

            driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_TextBox1").send_keys(cap_txt)
            time.sleep(2)
            driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_btnviewresult").click()
            time.sleep(0.8)

            try:
                alert = driver.switch_to.alert
                emit(q, type="log", msg=f"⚠ [{enr}] Alert: {alert.text} — retrying")
                alert.accept()
                continue
            except Exception:
                soup       = BeautifulSoup(driver.page_source, "html.parser")
                result_row = parse_result(soup)
                found      = result_row.get("Name", "") not in ("", "Not Found")
                emit(q, type="log", msg=f"{'✅' if found else '❌'} [{enr}] {'Data found' if found else 'No data on page'}")
                emit(q, type="status", enr=enr,
                    step="✅ Result saved" if found else "❌ No result found",
                    captcha=f"Gemini read: {cap_txt}",
                    status="found" if found else "not_found")
                break

    except TimeoutException as e:
        emit(q, type="log",    msg=f"⛔ [{enr}] Timeout")
        emit(q, type="status", enr=enr, step="⛔ Timeout — site too slow", captcha="", status="error")
    except Exception as e:
        emit(q, type="log",    msg=f"❌ [{enr}] Error: {str(e)[:80]}")
        emit(q, type="status", enr=enr, step=f"❌ {str(e)[:60]}", captcha="", status="error")
    finally:
        driver.quit()

    return result_row

# ── run_batch ─────────────────────────────────────────────────────────────────
def run_batch(prog_idx, enrollments, semester, grading, q, stop_event: threading.Event):
    for enr in enrollments:
        if stop_event.is_set():
            emit(q, type="log", msg="🛑 Stopped by user.")
            break
        emit(q, type="log", msg=f"\n📘 Starting: {enr}")
        row = fetch_one(prog_idx, enr, semester, grading, q, stop_event)
        emit(q, type="result", enr=enr, row=row)
    emit(q, type="done")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 RGPV Fetcher")
    st.markdown("<hr>", unsafe_allow_html=True)

    PROGRAMS = {"B.E.":1,"B.Tech":2,"M.Tech":3,"MCA":4,"MBA":5,"B.Pharma":6}
    prog_name = st.selectbox("Program", list(PROGRAMS.keys()), index=1)
    prog_idx  = PROGRAMS[prog_name] - 1

    semester = st.selectbox("Semester", [str(i) for i in range(1, 9)])
    grading  = st.radio("Result Type", ["Grading","Marks"], horizontal=True) == "Grading"

    st.markdown("<hr>", unsafe_allow_html=True)
    mode = st.radio("Fetch Mode", ["Single Student","Range (Full Class)"])

    if mode == "Single Student":
        enr_in = st.text_input("Enrollment No.", placeholder="0805CS241001")
        enrollments = [enr_in.strip().upper()] if enr_in.strip() else []
    else:
        prefix = st.text_input("Prefix", value="0805CS24")
        c1, c2 = st.columns(2)
        start  = c1.number_input("Start", min_value=1, value=1001, step=1)
        end    = c2.number_input("End",   min_value=1, value=1010, step=1)
        enrollments = [f"{prefix.strip()}{str(n).zfill(3)}"
                    for n in range(int(start), int(end)+1)]

    if enrollments:
        st.caption(f"📋 {len(enrollments)} enrollment(s) queued")

    st.markdown("<hr>", unsafe_allow_html=True)
    fetch_btn = st.button("▶  Fetch Results", disabled=st.session_state.running)
    st.markdown('<div class="stop-btn">', unsafe_allow_html=True)
    stop_btn  = st.button("⏹  Stop",         disabled=not st.session_state.running)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Stop button handler ───────────────────────────────────────────────────────
if stop_btn:
    get_stop_event().set()

# ── Start batch ───────────────────────────────────────────────────────────────
if fetch_btn and enrollments and not st.session_state.running:
    ev = get_stop_event()
    ev.clear()

    st.session_state.results_df   = pd.DataFrame()
    st.session_state.log_lines    = []
    st.session_state.running      = True
    st.session_state.done         = 0
    st.session_state.total_enr    = len(enrollments)
    st.session_state.passed       = 0
    st.session_state.failed       = 0
    st.session_state.errors       = 0
    st.session_state.current_enr  = ""
    st.session_state.current_step = "Starting…"
    st.session_state.current_captcha = ""
    st.session_state.current_status  = "fetching"

    q = queue.Queue()
    st.session_state._q = q

    threading.Thread(
        target=run_batch,
        args=(prog_idx, enrollments, semester, grading, q, ev),
        daemon=True,
    ).start()

# ── Drain queue every rerun ───────────────────────────────────────────────────
q: queue.Queue = st.session_state._q
if q is not None and st.session_state.running:
    try:
        while True:
            msg = q.get_nowait()
            t   = msg["type"]

            if t == "log":
                st.session_state.log_lines.append(msg["msg"])

            elif t == "status":
                st.session_state.current_enr     = msg["enr"]
                st.session_state.current_step    = msg["step"]
                st.session_state.current_captcha = msg["captcha"]
                st.session_state.current_status  = msg["status"]

            elif t == "result":
                row = msg["row"]
                st.session_state.done += 1
                if row and row.get("Name","") not in ("","Not Found"):
                    status = row.get("Status","").lower()
                    if "pass" in status:
                        st.session_state.passed += 1
                    else:
                        st.session_state.failed += 1
                    new_df = pd.DataFrame([row])
                    st.session_state.results_df = pd.concat(
                        [st.session_state.results_df, new_df], ignore_index=True)
                else:
                    st.session_state.errors += 1

            elif t == "done":
                st.session_state.running      = False
                st.session_state.current_step = "🏁 All done!"
                st.session_state.current_status = "found"

    except queue.Empty:
        pass

# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown("# RGPV Result Dashboard")

df = st.session_state.results_df

avg_sgpa, avg_cgpa = "—", "—"
if not df.empty:
    s = pd.to_numeric(df.get("SGPA", pd.Series()), errors="coerce")
    c = pd.to_numeric(df.get("CGPA", pd.Series()), errors="coerce")
    if s.notna().any(): avg_sgpa = f"{s.mean():.2f}"
    if c.notna().any(): avg_cgpa = f"{c.mean():.2f}"

mc1,mc2,mc3,mc4,mc5 = st.columns(5)
for col, lbl, val, sub in [
    (mc1,"Fetched",  f"{st.session_state.done}/{st.session_state.total_enr or '—'}","students"),
    (mc2,"Found",    st.session_state.passed,  "passed"),
    (mc3,"Failed",   st.session_state.failed,  "failed / not found"),
    (mc4,"Avg SGPA", avg_sgpa, "semester GPA"),
    (mc5,"Avg CGPA", avg_cgpa, "cumulative GPA"),
]:
    col.markdown(f"""
    <div class="mc"><div class="lbl">{lbl}</div>
    <div class="val">{val}</div><div class="sub">{sub}</div></div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

total_enr = st.session_state.total_enr
done      = st.session_state.done
if total_enr:
    frac  = min(done / total_enr, 1.0)
    label = f"{'🔄 Running' if st.session_state.running else '✅ Done'} — {done} / {total_enr} students"
    st.progress(frac, text=label)

enr     = st.session_state.current_enr
step    = st.session_state.current_step
cap     = st.session_state.current_captcha
cstatus = st.session_state.current_status

status_html = {
    "fetching":  '<span style="color:#f0883e;font-weight:600;">⏳ In progress…</span>',
    "found":     '<span style="color:#3fb950;font-weight:600;">✅ Data found</span>',
    "not_found": '<span style="color:#f85149;font-weight:600;">❌ Not found</span>',
    "error":     '<span style="color:#d2a8ff;font-weight:600;">⛔ Error</span>',
}.get(cstatus, "")

if enr:
    st.markdown(f"""
    <div class="cur-card">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div class="enr">🎓 {enr}</div>{status_html}
    </div>
    <div class="step">{step}</div>
    {"<div class='cap'>" + cap + "</div>" if cap else ""}
    </div>""", unsafe_allow_html=True)

with st.expander("📟 Live Log", expanded=st.session_state.running):
    lines = st.session_state.log_lines[-60:]
    st.markdown('<div class="logbox">' + "\n".join(lines) + '</div>',
                unsafe_allow_html=True)

if st.session_state.running:
    time.sleep(0.5)
    st.rerun()

# ── Results table ─────────────────────────────────────────────────────────────
if not df.empty:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("### 📊 Results")

    sort_opts = [c for c in ["Name","Roll No","SGPA","CGPA","Status"] if c in df.columns]
    f1,f2,f3 = st.columns([2,1,2])
    sort_col = f1.selectbox("Sort by", sort_opts)
    asc      = f2.radio("Order", ["↑ Asc","↓ Desc"], horizontal=True) == "↑ Asc"
    search   = f3.text_input("🔍 Search name / roll / branch")

    display = df.copy()
    if search:
        display = display[display.apply(lambda r: search.lower() in str(r).lower(), axis=1)]
    if sort_col in display.columns:
        if sort_col in ("SGPA","CGPA"):
            display[sort_col] = pd.to_numeric(display[sort_col], errors="coerce")
        display = display.sort_values(sort_col, ascending=asc)

    st.dataframe(display, use_container_width=True, height=420)
    st.caption(f"Showing {len(display)} of {len(df)} records")

    st.markdown("### ⬇ Download")
    d1,d2,d3 = st.columns([2,2,1])
    fmt_label = d1.selectbox("Format", ["CSV (.csv)","Excel (.xlsx)","TSV (.tsv)","JSON (.json)"])
    stem      = d2.text_input("Filename (no extension)", value="RGPV_Results")
    fmt_map   = {"CSV (.csv)":"csv","Excel (.xlsx)":"xlsx","TSV (.tsv)":"tsv","JSON (.json)":"json"}
    fmt       = fmt_map[fmt_label]

    if fmt == "csv":
        data,mime,ext = display.to_csv(index=False).encode(),"text/csv","csv"
    elif fmt == "xlsx":
        buf = io.BytesIO(); display.to_excel(buf, index=False)
        data,mime,ext = buf.getvalue(),"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","xlsx"
    elif fmt == "tsv":
        data,mime,ext = display.to_csv(index=False,sep="\t").encode(),"text/tab-separated-values","tsv"
    else:
        data,mime,ext = display.to_json(orient="records",indent=2).encode(),"application/json","json"

    d3.download_button(f"⬇ .{ext}", data=data,
                    file_name=f"{stem.strip() or 'RGPV_Results'}.{ext}", mime=mime)

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🗑 Clear All Data"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()