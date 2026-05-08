import requests
from bs4 import BeautifulSoup
import json

url = "https://www.ncbi.nlm.nih.gov/books/NBK430685/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print(f"Fetching {url}...")
response = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(response.content, "html.parser")

# Find all potential content containers
print("\n=== POTENTIAL CONTENT CONTAINERS ===")
potential_ids = ["article-content", "maincontent", "bookContent", "book-body", "contentbox", "main"]
for id_name in potential_ids:
    elem = soup.find("div", id=id_name)
    if elem:
        print(f"✓ Found div with id='{id_name}'")

print("\n=== POTENTIAL CONTENT CLASSES ===")
potential_classes = ["bk_article", "article-body", "content", "book", "section", "sec"]
for class_name in potential_classes:
    elements = soup.find_all("div", class_=class_name)
    if elements:
        print(f"✓ Found {len(elements)} div(s) with class='{class_name}'")

# Look at the main structure
print("\n=== MAIN BODY STRUCTURE ===")
body = soup.find("body")
if body:
    print("Body children tags:")
    for i, child in enumerate(body.find_all(recursive=False)):
        if child.name:
            print(f"  {i}: <{child.name}> id='{child.get('id', '')}' class='{child.get('class', [])}'")

# Check for article-specific tags
print("\n=== ARTICLE TAG ===")
article = soup.find("article")
if article:
    print("✓ Found <article> tag")
    print(f"  id: {article.get('id', 'none')}")
    print(f"  class: {article.get('class', [])}")
else:
    print("✗ No <article> tag found")

# Look for heading structure
print("\n=== HEADING HIERARCHY ===")
h1 = soup.find("h1")
if h1:
    print(f"H1: {h1.text.strip()[:50]}")
    print(f"  id: {h1.get('id', 'none')}")
    print(f"  class: {h1.get('class', [])}")

# Sample first few paragraphs
print("\n=== FIRST 5 PARAGRAPHS ===")
paragraphs = soup.find_all("p")[:5]
for i, p in enumerate(paragraphs):
    text = p.text.strip()[:80]
    print(f"{i+1}: {text}...")
