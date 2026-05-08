import time
import requests
from bs4 import BeautifulSoup

def scrape_statpearls_html(article_data):
    url = article_data["url"]
    print(f"[*] Scraping Webpage: {url}")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    time.sleep(1) 
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # 1. DESTROY THE NAVIGATION MENUS
    # This strips the massive Table of Contents out of the code completely
    for toc in soup.find_all("ul", class_="toc"):
        toc.decompose()
    for sidebar in soup.find_all("div", class_="bk_noprnt"):
        sidebar.decompose()
    
    # 2. Get the genuine article title
    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else "StatPearls Article"
    
    parsed_text = f"Disease/Topic: {title}\n\n"
    content_found = False
    
    # 3. The Target Sections
    target_sections = [
        "introduction", "etiology", "epidemiology", "pathophysiology", 
        "history and physical", "evaluation", "treatment / management",
        "differential diagnosis", "prognosis", "complications"
    ]
    
    # 4. The Sibling-Walker
    # Find every header on the page
    for header in soup.find_all(['h2', 'h3']):
        header_text = header.text.strip().lower()
        
        # If the header is a medical section we want...
        if any(target in header_text for target in target_sections):
            parsed_text += f"--- {header.text.strip().upper()} ---\n"
            
            # Walk down the page element by element
            for sibling in header.find_next_siblings():
                # Stop walking if we hit a new header (meaning a new section started)
                if sibling.name in ['h1', 'h2', 'h3']:
                    break
                
                # If we find a paragraph, extract the text
                if sibling.name == 'p':
                    text = sibling.text.strip()
                    if len(text) > 40: # Ignore tiny UI fragments
                        parsed_text += text + " "
                        content_found = True
                        
                # If the text is hiding inside an invisible divider, dig it out
                elif sibling.name == 'div':
                    for p in sibling.find_all('p'):
                        text = p.text.strip()
                        if len(text) > 40:
                            parsed_text += text + " "
                            content_found = True
            
            parsed_text += "\n\n"

    if not content_found:
        return f"[-] Sibling-walker failed to extract text for {title}"
        
    return parsed_text

if __name__ == "__main__":
    test_article = {
        "url": "https://www.ncbi.nlm.nih.gov/books/NBK441916/",
        "title": "Tuberculosis"
    }
    
    print("\n" + "="*50)
    print("🔬 RUNNING SCRAPER DIAGNOSTIC")
    print("="*50 + "\n")
    
    raw_text = scrape_statpearls_html(test_article)
    
    with open("debug_scraped_output.txt", "w", encoding="utf-8") as f:
        f.write(raw_text)
        
    print("[+] Extraction complete. Check 'debug_scraped_output.txt'!")