from selenium import webdriver
from bs4 import BeautifulSoup
import time
import json
import re

def scrape_jetpunk_quiz(driver, url):
    print(f"Scraping {url}...")
    
    try:
        driver.get(url)
        
        # Get page source to find the _page variable
        page_source = driver.page_source
        
        # Use regex to find the JSON object assigned to _page
        # Pattern looks for: var _page = { ... };
        match = re.search(r'var _page = ({.*?});', page_source, re.DOTALL)
        if not match:
            # Fallback: sometimes it might not have the semicolon or slightly different spacing
            match = re.search(r'var _page = ({.*})', page_source, re.DOTALL)
            
        if match:
            json_str = match.group(1)
            try:
                data = json.loads(json_str)
                
                # Navigate to the answers: data -> quiz -> answers
                # Note: The variable is _page = {"data": ...}
                quiz_data = data.get('data', {}).get('quiz', {})
                answers_list = quiz_data.get('answers', [])
                
                results = []
                grouped_answers = {}
                
                def clean_text(text):
                    if not text: return ""
                    # Replace <br> variants with space
                    text = re.sub(r'<br\s*\\?/?\s*>', ' ', text, flags=re.IGNORECASE)
                    # Remove curly braces
                    text = text.replace('{', '').replace('}', '')
                    # BS4 for other tags/entities
                    text = BeautifulSoup(text, 'html.parser').get_text(separator=' ', strip=True)
                    # Normalize whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text

                for ans in answers_list:
                    cols = ans.get('cols', [])
                    if len(cols) >= 2:
                        question = clean_text(cols[0])
                        answer = clean_text(cols[1])
                        
                        if question not in grouped_answers:
                            grouped_answers[question] = []
                        grouped_answers[question].append(answer)
                
                # Format results
                for q, a_list in grouped_answers.items():
                    # Join multiple answers with comma
                    a_str = ", ".join(a_list)
                    results.append((q, a_str))
                    
                return results
                
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return []
        else:
            print("Could not find _page variable in source.")
            return []

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

if __name__ == "__main__":
    with open("output.txt", "w", encoding="utf-8") as f:
        for i in range(1, 5):
            print(f"Starting quiz {i}...")
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless') 
            driver = webdriver.Chrome(options=options)
            
            try:
                url = f"https://www.jetpunk.com/quizzes/general-knowledge-quiz-{i}"
                data = scrape_jetpunk_quiz(driver, url)
                
                if data:
                    for q, a in data:
                        f.write(f"{q}|{a}\n")
                    f.write("\n") # Empty line between quizzes
                    print(f"Successfully scraped {len(data)} items from quiz {i}.")
                else:
                    print(f"No data found for quiz {i}.")
            except Exception as e:
                print(f"Error scraping quiz {i}: {e}")
            finally:
                driver.quit()
            
            # Optional: small delay between quizzes
            #time.sleep(2)
