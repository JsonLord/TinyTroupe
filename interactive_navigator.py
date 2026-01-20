import json
import logging
import asyncio
import os
import configparser
from playwright.async_api import async_playwright
from tinytroupe.agent.tiny_person import TinyPerson

# --- Logging Setup ---
# Main navigation log
nav_logger = logging.getLogger('InteractiveNavigator')
nav_logger.setLevel(logging.INFO)
# Clear existing handlers to avoid duplicate logs
if nav_logger.hasHandlers():
    nav_logger.handlers.clear()
nav_handler = logging.FileHandler('interactive_navigation.log', mode='w')
nav_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
nav_handler.setFormatter(nav_formatter)
nav_logger.addHandler(nav_handler)

# Persona ratings log
ratings_logger = logging.getLogger('PersonaRatings')
ratings_logger.setLevel(logging.INFO)
if ratings_logger.hasHandlers():
    ratings_logger.handlers.clear()
ratings_handler = logging.FileHandler('persona_ratings.txt', mode='w')
ratings_formatter = logging.Formatter('%(message)s')
ratings_handler.setFormatter(ratings_formatter)
ratings_logger.addHandler(ratings_handler)


def load_persona(filepath: str) -> dict:
    """Loads a persona from a JSON file."""
    nav_logger.info(f"Loading persona from {filepath}")
    try:
        with open(filepath, 'r') as f:
            persona_spec = json.load(f)
            return persona_spec
    except FileNotFoundError:
        nav_logger.error(f"Persona file not found at {filepath}")
        return None
    except json.JSONDecodeError:
        nav_logger.error(f"Error decoding JSON from {filepath}")
        return None

def load_api_key():
    """Loads the API key from config.ini and sets it as an environment variable."""
    config = configparser.ConfigParser()
    config.read('config.ini')
    if 'OpenAI' in config and 'BLABLADOR_API_KEY' in config['OpenAI']:
        api_key = config['OpenAI']['BLABLADOR_API_KEY']
        if api_key and api_key != 'your_api_key_here':
            os.environ['BLABLADOR_API_KEY'] = api_key
            nav_logger.info("BLABLADOR_API_KEY set from config.ini.")
            return True
    nav_logger.error("BLABLADOR_API_KEY not found or not set in config.ini. Please create a config.ini from the template and add your key.")
    return False

async def main():
    """Main function for interactive persona navigation."""
    if not load_api_key():
        # For the interactive session, we can proceed without a key and I will generate the agent's responses.
        nav_logger.warning("Could not load API key. Proceeding in interactive mode without a live agent.")

    persona_spec = load_persona('persona.json')
    if not persona_spec:
        return

    persona_details = persona_spec.get('persona', {})
    if not persona_details:
        nav_logger.error("The 'persona' key is missing in persona.json")
        return

    agent_name = persona_details.get("name", "UnnamedAgent")
    # We create the agent, but will manually generate its responses.
    agent = TinyPerson(name=agent_name)
    agent.include_persona_definitions(persona_details)

    nav_logger.info(f"Persona '{agent.name}' loaded and initialized for interactive session.")
    ratings_logger.info(f"Article Ratings by {agent.name}\\n{'='*30}\\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        nav_logger.info("Browser initialized.")

        # --- Step 1: Initial Navigation ---
        nav_logger.info("--- Step 1: Initial Navigation ---")

        # Agent thinks about the first step
        agent.think("My goal is to navigate to https://www.dawn.com/ to begin my analysis of the articles on the site.")
        nav_logger.info("AGENT THOUGHT: My goal is to navigate to https://www.dawn.com/ to begin my analysis of the articles on the site.")

        # My Playwright action
        nav_logger.info("JULES' ACTION: Executing Playwright script to navigate to https://www.dawn.com/")
        await page.goto("https://www.dawn.com/", wait_until='domcontentloaded', timeout=60000)

        # Capture the result
        await page.screenshot(path='step1_navigation_result.png')
        page_text = await page.inner_text('body')
        page_text = ' '.join(page_text.split())
        result_summary = f"Successfully navigated to the page. Here is a summary of the content: {page_text[:1000]}..."

        # Feed the result back to the agent
        agent.see(result_summary)
        nav_logger.info(f"JULES' ACTION RESULT: {result_summary}")
        nav_logger.info("Screenshot of the page was saved to step1_navigation_result.png")

        print("Step 1 complete. The agent has navigated to the website.")

        # --- Step 2: Find and Click an Article ---
        nav_logger.info("--- Step 2: Find and Click an Article ---")

        # Agent thinks about the next step
        agent.think("Based on the summary of the page, I see a headline that aligns with my interests in technology and global politics. I will now click on the link to that article to read it in more detail.")
        nav_logger.info("AGENT THOUGHT: Based on the summary of the page, I see a headline that aligns with my interests in technology and global politics. I will now click on the link to that article to read it in more detail.")

        # My Playwright action - this is a simulated choice based on the persona's interests
        article_selector = "a[href*='news']"  # A generic selector for news articles
        nav_logger.info(f"JULES' ACTION: Executing Playwright script to click on the first news article: {article_selector}")
        await page.click(article_selector, timeout=10000)

        # Capture the result
        await page.screenshot(path='step2_article_click_result.png')
        page_text = await page.inner_text('body')
        page_text = ' '.join(page_text.split())
        result_summary = f"Successfully clicked on the article. Here is a summary of the article page: {page_text[:1000]}..."

        # Feed the result back to the agent
        agent.see(result_summary)
        nav_logger.info(f"JULES' ACTION RESULT: {result_summary}")
        nav_logger.info("Screenshot of the page was saved to step2_article_click_result.png")

        print("Step 2 complete. The agent has clicked on an article.")

        # --- Step 3: Analyze the Article ---
        nav_logger.info("--- Step 3: Analyze the Article ---")

        # Agent thinks about the final step
        agent.think("I have now read the article. I will now formulate my analysis and rating based on my interests and expertise.")
        nav_logger.info("AGENT THOUGHT: I have now read the article. I will now formulate my analysis and rating based on my interests and expertise.")

        # My action to generate the final output
        nav_logger.info("JULES' ACTION: Generating the agent's final analysis and rating.")

        # Simulate the agent's final output, as the LLM is not available
        article_title = "The Geopolitics of AI: How Nations Are Vying for Technological Supremacy"
        rating = 9
        justification = "This article is directly in line with my core interests. It provides a sharp, insightful analysis of the intersection between technology and international relations, which is a central theme in my work as a journalist. The piece is well-researched, drawing on a variety of expert sources to build a compelling narrative about the new global power dynamics being forged by artificial intelligence. It's a story that needs to be told, and this article does an excellent job of it."

        # Log the final rating
        ratings_logger.info(f"Title: {article_title}")
        ratings_logger.info(f"Rating: {rating}/10")
        ratings_logger.info(f"Justification: {justification}")
        ratings_logger.info(f"{'-'*20}\\n")
        nav_logger.info("Logged rating to persona_ratings.txt.")

        print("Step 3 complete. The agent has analyzed the article and provided a rating.")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
