import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from chains import Chain
from portfolio import Portfolio
from utils import clean_text, extract_deadline, debug_deadline_search
from web_scraper import WebScraper

def get_page_content(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        # Wait for job content to load
        time.sleep(5)  # Give the page some time to load dynamic content
        
        # Get the page content
        content = driver.page_source
        return content
    finally:
        driver.quit()


def create_streamlit_app(llm, portfolio, clean_text):
    st.title("📧 Cold Mail Generator")
    # start with an empty value and show a helpful placeholder so users must enter a URL
    url_input = st.text_input("Enter a URL:", value="", placeholder="Please enter a valid job posting URL")
    submit_button = st.button("Submit")

    if submit_button:
        try:
            st.info("Loading job data...")
            raw_content = WebScraper.scrape_url(url_input)
            data = clean_text(raw_content)
            st.info("Loading portfolio...")
            portfolio.load_portfolio()
            st.info("Extracting job information...")
            jobs = llm.extract_jobs(data)
            if not jobs:
                st.warning("No job information could be extracted. Please check the URL.")
                return
            
            st.success(f"Found {len(jobs)} job posting(s)")
            # Attempt to detect an application deadline from the raw page content
            deadline = extract_deadline(raw_content)
            debug_snippets = None
            if not deadline:
                # collect debug snippets to show why extraction failed
                debug_snippets = debug_deadline_search(raw_content, context_chars=300)
            for i, job in enumerate(jobs, 1):
                st.write(f"Processing job {i}...")
                skills = job.get('skills', [])
                if not skills:
                    st.warning(f"No skills found for job {i}")
                    continue
                    
                st.write(f"Found skills: {', '.join(skills)}")
                # show deadline (if any) alongside the skills
                if deadline:
                    st.write(f"Apply by: {deadline}")
                else:
                    st.write("Apply by: No deadline available")
                    # show debug snippets so user can see where date text appears (if any)
                    if debug_snippets:
                        st.info("Deadline debug snippets - showing nearby text where anchors/dates were found:")
                        for s in debug_snippets[:5]:
                            anchor = s['anchor'] or 'date'
                            date_match = s['date_match'] or 'no date match'
                            st.code(f"anchor={anchor} | date_match={date_match}\n{ s['context'][:400].replace('\n',' ') }\n...")
                links = portfolio.query_links(skills)
                st.info("Generating email...")
                email = llm.write_mail(job, links)
                st.code(email, language='markdown')
                st.success(f"Email {i} generated successfully!")
        except Exception as e:
            st.error(f"An Error Occurred: {e}")
            import traceback
            st.error(f"Detailed error: {traceback.format_exc()}")


if __name__ == "__main__":
    chain = Chain()
    portfolio = Portfolio()
    st.set_page_config(layout="wide", page_title="Cold Email Generator", page_icon="📧")
    create_streamlit_app(chain, portfolio, clean_text)


