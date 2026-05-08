import requests

url = "https://www.ncbi.nlm.nih.gov/books/NBK430685/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

response = requests.get(url, headers=headers)

# Save the raw HTML to a file so we can inspect it
with open("raw_page.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print("Saved raw HTML to raw_page.html. Please open it in your editor.")