from agent.utils.states import InputState, GraphState, OutputState
from agent.utils.firecrawl import firecrawl_app
from agent.utils.llm import llm
from agent.utils.helpers import is_valid_url, try_except_decorator
from agent.utils.constants import CRAWL, SCRAP, FORMAT, SAVE
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()

def initialize(state: InputState) -> GraphState:
    return GraphState(
        url=state.get("url", ""),
        url_batches=[],
        scraped_data=[],
        formatted_data=[],
        error="",
        retry_count=0,
        failed_node="",
    )

@try_except_decorator(identifier=CRAWL)
def crawl(state: GraphState):
    input_url = state['url']
    print(f"\n🔍 CRAWL - Starting for: {input_url}")
    
    # crawl() returns a CrawlJob object
    response = firecrawl_app.crawl(
        url=input_url,
        limit=1,
        scrape_options={
            'formats': ['links']
        }
    )
    
    print(f"   Response type: {type(response)}")
    
    # Access the data attribute directly from CrawlJob object
    data = response.data if hasattr(response, 'data') else []
    print(f"   Data length: {len(data)}")
    
    if data:
        # data is a list of Document objects, access links attribute
        first_doc = data[0]
        print(f"   First doc type: {type(first_doc)}")
        
        scraped_urls = first_doc.links if hasattr(first_doc, 'links') else []
        print(f"   Total links found: {len(scraped_urls)}")
        print(f"   Links: {scraped_urls[:5]}")  # Show first 5 links
        
        valid_urls = [url for url in scraped_urls if is_valid_url(url, input_url)]
        print(f"   Valid links after filtering: {len(valid_urls)}")
        print(f"   Valid URLs: {valid_urls[:5]}")  # Show first 5 valid
        
        limited_urls = valid_urls[:int(os.getenv("URL_LIMIT"))]
        print(f"   After URL_LIMIT ({os.getenv('URL_LIMIT')}): {len(limited_urls)}")
        
        state["url_batches"] = [limited_urls[i:i + int(os.getenv("BATCH_LIMIT"))] for i in range(0, len(limited_urls), int(os.getenv("BATCH_LIMIT")))]
        print(f"   Created {len(state['url_batches'])} batches")
    else:
        print("   ⚠️  No data returned from crawl")
        state["url_batches"] = []

    print(f"✅ CRAWL - Complete\n")
    return state

@try_except_decorator(identifier=SCRAP)
def scrap(state: GraphState):
    scraped_data_result = []
    if state["url_batches"]:
        current_batch = state["url_batches"][0]
        # batch_scrape returns a BatchScrapeJob object
        batch_scrap_result = firecrawl_app.batch_scrape(
            urls=current_batch,
            formats=['markdown']
        )

        # Access data attribute directly
        data = batch_scrap_result.data if hasattr(batch_scrap_result, 'data') else []
        if data:
            scraped_data_result = data
            state["url_batches"].pop(0)
            
    state["scraped_data"] = scraped_data_result

    return state

@try_except_decorator(identifier=FORMAT)
def format(state: GraphState):
    scraped_data = state.get("scraped_data", [])
    formatted_data = []
    if scraped_data:
        for content in scraped_data:
            # content is a Document object, access attributes directly
            metadata = content.metadata if hasattr(content, 'metadata') else None
            if not metadata:
                continue

            url = metadata.url if hasattr(metadata, 'url') else ""
            markdown = content.markdown if hasattr(content, 'markdown') else ""
            if not markdown:
                continue

            markdown = markdown[:2000] if markdown and len(markdown) > 2000 else markdown
            response = llm.invoke(
                f"""
                    Analyze the provided information and generate a summarized output using the specified structure. 
        
                    ### Content:
                    {markdown}
                    
                    ### Structured JSON Output (MUST be valid JSON):
                    {{
                        "title": "A short title summarizing the topic",
                        "description": "A 2/3 lines summary of the first couple of paragraphs of the markdown."
                    }}
                    
                    Return ONLY the JSON object, nothing else.
                """
            )

            if not response or not response.content:
                print(f"Warning: Empty response from LLM for URL: {url}")
                continue

            try:
                # Clean the response content
                content_str = response.content.strip()
                
                # Try to extract JSON if it's wrapped in markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content_str, re.DOTALL)
                if json_match:
                    content_str = json_match.group(1)
                
                # Parse the JSON
                parsed_response = json.loads(content_str)
                
                formatted_data.append({
                    "url": url,
                    "response": parsed_response
                })
            except json.JSONDecodeError as e:
                print(f"Warning: Failed to parse JSON for URL {url}: {e}")
                print(f"LLM Response: {response.content[:200]}")
                # Fallback: create a basic entry
                formatted_data.append({
                    "url": url,
                    "response": {
                        "title": "Error parsing content",
                        "description": markdown[:200]
                    }
                })
        
    state["formatted_data"] = formatted_data
    return state

@try_except_decorator(identifier=SAVE)
def save(state: GraphState) -> OutputState:
    source_url = state.get("url", "")
    formatted_data = state.get("formatted_data", [])
    
    if source_url and formatted_data:
        output = {
            "source_url": source_url,
            "data": formatted_data
        }

        with open("scraped_data.json", "w") as f:
            json.dump(output, f, indent=4)
        
        print("Scrapping completed, data saved in scraped_data.json")
        return { "result": output }

    return state

def error_handler(state: GraphState):
    state["retry_count"] += 1
    state["error"] = ""

    return state