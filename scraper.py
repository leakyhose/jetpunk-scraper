from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json
import re
import sys
import warnings

# Suppress BeautifulSoup filename warning
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

def scrape_jetpunk_quiz(driver, url, quiz_number):
    print(f"Scraping {url}...")
    
    try:
        driver.get(url)
        
        # Wait for page to fully load - give it more time
        print("Waiting for page to load...")
        time.sleep(3)  # Initial wait for page load
        
        # Wait for body to be present
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except:
            print("Warning: Timeout waiting for body element")
        
        # Additional wait to ensure JavaScript has executed
        time.sleep(2)
        
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
            # CRITICAL ERROR: Could not find _page variable
            print("=" * 80)
            print(f"CRITICAL ERROR: Could not find 'var _page' in quiz {quiz_number}!")
            print(f"URL: {url}")
            print("=" * 80)
            
            # Save the HTML for debugging
            error_filename = f"error_quiz_{quiz_number}.html"
            with open(error_filename, "w", encoding="utf-8") as error_file:
                error_file.write(page_source)
            print(f"Page HTML saved to: {error_filename}")
            print("Program will now terminate.")
            print("=" * 80)
            
            # Return None to signal critical error
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return []

if __name__ == "__main__":
    with open("output.txt", "w", encoding="utf-8") as f:
        for i in range(227, 234):
            print(f"Starting quiz {i}...")
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless') 
            driver = webdriver.Chrome(options=options)
            
            try:
                url = f"https://www.jetpunk.com/quizzes/general-knowledge-quiz-{i}"
                data = scrape_jetpunk_quiz(driver, url, i)
                
                if data is None:
                    # Critical error occurred - shut down
                    driver.quit()
                    sys.exit(1)
                elif data:
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
