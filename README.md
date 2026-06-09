# 🎓 RGPV Result Fetcher 🔍

A Python automation tool to fetch and store RGPV B.Tech student results in an Excel sheet using **Selenium**, **OCR (Tesseract)**, and **BeautifulSoup**.

## 🆕 NEW FEATURE: Streamlit Web UI

Now includes a beautiful **Streamlit web interface** with the following capabilities:
- ✨ Modern, user-friendly dashboard
- 📋 Fetch single student results
- 📚 Batch fetch multiple results
- 📊 View and search saved results
- 📥 Download results as Excel
- 🎯 Real-time progress tracking

---

## 👨‍💻 Designed By: [Nitin Sen]www.linkedin.com/in/
nitin-sen-972a7130a


---

## 📦 Features

- Automatically fills RGPV result form
- Captures and decodes CAPTCHA using OCR
- Extracts student grades and stores in an Excel file
- Skips invalid entries with blank or zero-filled rows
- Output formatted cleanly in `.xlsx`
- **NEW:** Web-based UI with Streamlit for easy access

---

## 🛠️ Installation Guide

### 1. 📥 Clone or Download
```bash
git clone https://github.com/Nitinsen001/result_finder.git
cd result_finder
````

### 2. 📦 Install Python Requirements

```bash
pip install -r requirements.txt
```

**requirements.txt**

```
beautifulsoup4
selenium
pillow
pytesseract
requests
openpyxl
streamlit
pandas
```

### 3. 📷 Install Tesseract OCR

#### For Windows

* Download from: [tesseract-ocr-w64-setup-5.5.0.20241111.exe](https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe)
* Install and note the path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`)
* Add the path in your code:

```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

#### For Linux

```bash
sudo apt update
sudo apt install tesseract-ocr
```

### 4. 🌐 Install Chrome WebDriver (Optional)

* Download: [https://chromedriver.chromium.org/downloads](https://chromedriver.chromium.org/downloads)
* Match the version with your Chrome browser.
* Add it to your system PATH or specify the path in the code:

```python
driver = webdriver.Chrome(executable_path='path/to/chromedriver')
```

---

## 🚀 How to Use

### Option 1: Streamlit Web UI (Recommended) ⭐

1. Install all dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit app:
```bash
streamlit run app.py
```

3. Open your browser to `http://localhost:8501`

4. Use the interface to:
   - **📋 Single Result Tab**: Fetch a single student's result by enrollment number
   - **📚 Batch Results Tab**: Fetch multiple students' results by setting a range
   - **📊 View Results Tab**: View all saved results and download Excel file

### Option 2: Command-line Script

1. Add enrollment numbers in the script.
2. Run the script:

```bash
python app.py
```

3. Results will be saved in `RGPV_Result.xlsx` it also support 'csv,json,txt'.

---

## 🎯 Streamlit Features

### 📋 Single Result Fetching
- Enter enrollment number
- Automatically detects and solves CAPTCHA
- Displays student information including grades
- Saves to Excel

### 📚 Batch Processing
- Set enrollment prefix (e.g., 1901)
- Define start and end range
- Fetch multiple results with progress tracking
- Shows success/failure statistics

### 📊 Results Dashboard
- View all saved results in a table
- Search by name or roll number
- Download Excel file with one click
- Paginated view for large datasets

---

## 📁 Output Format

The Excel sheet will look like:

| S.No | Enrollment | Name         | Semester | BT101 | BT102 | ... | SGPA | CGPA | Result              |
| ---- | ---------- | ------------ | -------- | ----- | ----- | --- | ---- | ---- | ------------------- |
| 1    | 0403AL2310 | XYZ          | 1        | C     | C     | ... | 5.57 | 5.57 | Fail in BT104,BT105 |
| 2    | 0403AL2310 |              |          | 0     | 0     | ... | 0    | 0    |                     |

---

## 🧠 Notes

* Run using a stable internet connection.
* Make sure your browser & WebDriver versions match.
* Use real enrollment numbers for accurate testing.


---

## 📞 Contact

For support or queries, visit [Moh Technology](https://www.youtube.com/@mohtechnology)
