# 🚀 Quick Start Guide - RGPV Result Fetcher

## Installation & Setup

### Step 1: Install Python (if not already installed)
- Download Python 3.8 or higher from [python.org](https://www.python.org/downloads/)
- **Important**: Check "Add Python to PATH" during installation

### Step 2: Install Tesseract OCR

#### Windows:
1. Download the installer: [tesseract-ocr-w64-setup-5.5.0.exe](https://github.com/tesseract-ocr/tesseract/releases)
2. Run the installer
3. Keep the default installation path: `C:\Program Files\Tesseract-OCR`
4. Complete the installation

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install tesseract-ocr
```

#### macOS:
```bash
brew install tesseract
```

### Step 3: Install Python Dependencies

Navigate to the project folder in terminal/command prompt:

```bash
pip install -r requirements.txt
```

This will install:
- `streamlit` - Web interface
- `selenium` - Browser automation
- `pillow` - Image processing
- `pytesseract` - OCR for CAPTCHA
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `openpyxl` - Excel handling
- `pandas` - Data manipulation

### Step 4: Run the Application

#### On Windows:
Simply double-click `run_app.bat` in the project folder

OR use command prompt:
```bash
streamlit run app.py
```

#### On Linux/macOS:
```bash
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`

---

## 📖 How to Use the App

### 🎯 Main Dashboard

1. **Configure Settings (Left Sidebar)**
   - Select Program (B.Tech, M.Tech, or Diploma)
   - Select Semester (1-8)
   - Choose Grading Type (Grading System or Marks System)

### 📋 Tab 1: Single Result
- Enter the enrollment number
- Click "🔍 Fetch Result"
- The app will automatically:
  - Fetch the CAPTCHA from RGPV website
  - Solve it using OCR
  - Extract student information
  - Save to Excel
- View results immediately on screen

### 📚 Tab 2: Batch Results
- Enter enrollment prefix (e.g., "1901")
- Set start and end range
- Click "🚀 Fetch Batch Results"
- The app will fetch multiple results with progress tracking
- View success/failure statistics

### 📊 Tab 3: View Results
- See all saved results in a table
- Search by student name or roll number
- Download the Excel file with one click

---

## ⚠️ Troubleshooting

### Issue: "Module not found" error
**Solution**: Make sure all requirements are installed:
```bash
pip install -r requirements.txt --upgrade
```

### Issue: CAPTCHA not being solved
**Solution**: 
- Check if Tesseract is installed in the correct path
- Verify the path in the error message matches your installation

### Issue: Selenium WebDriver error
**Solution**:
- The app should auto-download Chrome WebDriver
- If it fails, manually download from: https://chromedriver.chromium.org/

### Issue: "Server already in use" error
**Solution**: Change the port number:
```bash
streamlit run app.py --server.port 8502
```

### Issue: Results not saving to Excel
**Solution**:
- Make sure the Excel file isn't already open
- Check that you have write permissions in the project folder

---

## 📁 Project Structure

```
RGPV-Result-main/
├── app.py                 # Streamlit web application
├── nitin.py               # Original script (can still be used)
├── requirements.txt       # Python dependencies
├── run_app.bat           # Quick launch script (Windows)
├── README.md             # Project documentation
├── QUICKSTART.md         # This file
└── RGPV_Result.xlsx      # Generated output file
```

---

## 🎓 Enrollment Number Format

Different programs use different enrollment formats:

- **B.Tech**: 19010XXXXX (10 digits)
- **M.Tech**: 20010XXXXX (10 digits)
- **Diploma**: 19010XXXXX (varies)

Replace X with actual numbers, e.g., `1901000001`

---

## 💡 Tips & Tricks

1. **Batch Processing**: For fetching multiple results, use the Batch tab with a smaller range (10-20) to avoid timeouts

2. **Search**: Use the search function in Tab 3 to quickly find specific students

3. **Download**: You can download the Excel file anytime from Tab 3

4. **Multiple Semesters**: Run separate batches for different semesters

5. **Scheduling**: You can set up Windows Task Scheduler to run the script at specific times

---

## 🆘 Getting Help

- Check the terminal for error messages
- Visit the project GitHub page for issues
- Contact the developer: [Moh Technology](https://www.youtube.com/@mohtechnology)

---

## 🎉 You're all set!

Enjoy using RGPV Result Fetcher! Happy fetching! 🎓
