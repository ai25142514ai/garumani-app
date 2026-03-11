import os

log_path = r'C:\Users\zyuri\.gemini\antigravity\brain\91a827f1-5640-4896-9661-41cb511eb7bf\.system_generated\logs\overview.txt'

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

scraper_start = -1
scraper_end = -1
index_start = -1
index_end = -1

for i, line in enumerate(lines):
    if "Garumani Trend — DLsite Girls-Touch" in line and "互換版" in line:
        scraper_start = i
    elif scraper_start != -1 and line.strip() == '9. index.html':
        scraper_end = i
    elif line.strip() == '<!DOCTYPE html>' and scraper_end != -1:
        index_start = i
    elif index_start != -1 and '</html>' in line:
        index_end = i

print(scraper_start, scraper_end, index_start, index_end)

if scraper_start != -1 and scraper_end != -1:
    with open('scraper.py', 'w', encoding='utf-8') as f:
        # Find the actual start of scraper.py since the marker could be preceded by text
        # The user pasted `'''\nGarumani Trend ...` or similar
        # Let's write everything from the import block
        content = "".join(lines[scraper_start:scraper_end])
        # Find first import
        import_idx = content.find("import requests")
        if import_idx == -1: import_idx = content.find("from bs4")
        if import_idx != -1:
            f.write(content[import_idx:])
        else:
            f.write(content)

if index_start != -1 and index_end != -1:
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write("".join(lines[index_start:index_end+1]))

print("Recovery done.")
