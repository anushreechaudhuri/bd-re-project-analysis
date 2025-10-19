#!/usr/bin/env python3
"""
Systematic web scraping pipeline for analyzing renewable energy project opposition
Uses Gemini API and Brightdata SERP API to search for evidence of opposition or conflict
"""

import os
import json
import requests
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from unstructured.partition.auto import partition
from unstructured.cleaners.core import group_broken_paragraphs
import urllib.parse
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Gemini client
client = genai.Client()

class SearchQueries(BaseModel):
    """Pydantic model for search query generation output"""
    english_query: str = Field(..., description="Search query in English including project name, location, and keywords about land acquisition, solar, protest, farmer")
    bangla_query: str = Field(..., description="Search query in Bangla including project name, location, and keywords about কৃষক জমি দখল আন্দোলন প্রতিবাদ অভিযোগ")

class SearchResult(BaseModel):
    """Pydantic model for individual search result"""
    title: str
    link: str
    description: str
    position: int

class SearchResults(BaseModel):
    """Pydantic model for search results collection"""
    organic_results: List[SearchResult]
    total_results: int
    search_query: str
    language: str

class ContentExtraction(BaseModel):
    """Pydantic model for content extraction results"""
    url: str
    title: str
    content: str
    extraction_success: bool
    error_message: Optional[str] = None

class OppositionAnalysis(BaseModel):
    """Pydantic model for project analysis results"""
    has_opposition_evidence: bool = Field(..., description="True if evidence of opposition or conflict is found, False otherwise")
    opposition_types: List[str] = Field(..., description="List of types of opposition found (e.g., 'land acquisition protests', 'environmental concerns', 'farmer protests')")
    summary: str = Field(..., description="Detailed summary of findings including any project information, opposition evidence, or other relevant details")
    confidence_score: float = Field(..., description="Confidence score from 0.0 to 1.0 indicating how confident the analysis is")
    sources: List[str] = Field(..., description="List of URLs that contained relevant information")

class OppositionAnalyzer:
    """Main class for analyzing renewable energy project opposition"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.brightdata_api_key = os.getenv("BRIGHTDATA_SERP_API_KEY")
        
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        if not self.brightdata_api_key:
            raise ValueError("BRIGHTDATA_SERP_API_KEY not found in environment variables")
        
        # Create output directories
        self.base_dir = Path(".")
        self.search_dir = self.base_dir / "search"
        self.content_dir = self.base_dir / "content"
        self.result_dir = self.base_dir / "result"
        self.summary_dir = self.base_dir / "summary"
        
        for dir_path in [self.search_dir, self.content_dir, self.result_dir, self.summary_dir]:
            dir_path.mkdir(exist_ok=True)
        
        logger.info("OppositionAnalyzer initialized successfully")
    
    def generate_search_queries(self, project_data: Dict[str, Any]) -> SearchQueries:
        """Generate English and Bangla search queries using Gemini API"""
        logger.info(f"Generating search queries for project: {project_data.get('project_name', 'Unknown')}")
        
        # Create project context string
        project_context = f"""
        Project Name: {project_data.get('project_name', 'Unknown')}
        Location: {project_data.get('location', 'Unknown')}
        Capacity: {project_data.get('capacity', 'Unknown')}
        Agency: {project_data.get('agency', 'Unknown')}
        Status: {project_data.get('present_status', 'Unknown')}
        """
        
        prompt = f"""
        Based on the following renewable energy project information, generate two simple search queries to find any information about this project:

        {project_context}

        Generate:
        1. An English search query with just the project name, location, and conflict - keep it simple and general, NO QUOTES
        2. A Bangla search query with the project name, location, and conflict in Bangla - keep it simple and general, NO QUOTES

        The queries should be broad enough to find any information about this project including news articles, reports, EIA documents, financial information, PPA details, tariff rates, or any other project-related content. Don't make them too specific. Do not use quotes around any part of the query.

        Return the queries in JSON format with fields "english_query" and "bangla_query".
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            
            # Parse the response to extract JSON
            response_text = response.text.strip()
            
            # Try to extract JSON from the response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]
            else:
                # Fallback: create queries manually
                project_name = project_data.get('project_name', 'Unknown')
                location = project_data.get('location', 'Unknown')
                json_text = '{"english_query": "' + project_name + ' ' + location + ' conflict", "bangla_query": "' + project_name + ' ' + location + ' সংঘাত"}'
            
            queries_data = json.loads(json_text)
            queries = SearchQueries(**queries_data)
            
            logger.info(f"Generated queries - English: {queries.english_query}")
            logger.info(f"Generated queries - Bangla: {queries.bangla_query}")
            
            return queries
            
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            # Fallback queries
            project_name = project_data.get('project_name', 'Unknown')
            location = project_data.get('location', 'Unknown')
            return SearchQueries(
                english_query=f"{project_name} {location} conflict",
                bangla_query=f"{project_name} {location} সংঘাত"
            )
    
    def search_with_brightdata(self, query: str, language: str = "en") -> SearchResults:
        """Search using Brightdata SERP API"""
        logger.info(f"Searching with Brightdata for query: {query}")
        
        headers = {
            "Authorization": f"Bearer {self.brightdata_api_key}",
            "Content-Type": "application/json"
        }
        
        # URL encode the query
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        data = {
            "zone": "serp",
            "url": search_url,
            "format": "json"
        }
        
        try:
            response = requests.post(
                "https://api.brightdata.com/request",
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    search_data = response.json()
                    logger.info(f"Brightdata API response keys: {list(search_data.keys())}")
                    
                    # Parse organic results from HTML body
                    organic_results = []
                    
                    if 'body' in search_data and isinstance(search_data['body'], str):
                        # Parse HTML content
                        soup = BeautifulSoup(search_data['body'], 'html.parser')
                        
                        # Find search results using the correct selector
                        result_elements = soup.select('div.tF2Cxc')
                        logger.info(f"Found {len(result_elements)} result elements in HTML")
                        
                        for i, element in enumerate(result_elements[:10]):  # Limit to top 10 results
                            # Extract title and link from the result element
                            title = ""
                            link = ""
                            description = ""
                            
                            # Look for the main link (usually the first <a> tag)
                            main_link = element.find('a', href=True)
                            if main_link:
                                link = main_link.get('href', '')
                                # Extract title from the link text or from h3 tag
                                h3_tag = main_link.find('h3')
                                if h3_tag:
                                    title = h3_tag.get_text(strip=True)
                                else:
                                    title = main_link.get_text(strip=True)
                            
                            # Look for description/snippet (usually in a span with specific class)
                            snippet_spans = element.find_all('span')
                            for span in snippet_spans:
                                span_text = span.get_text(strip=True)
                                # Skip very short text and navigation elements
                                if len(span_text) > 20 and not any(word in span_text.lower() for word in ['web', 'images', 'videos', 'news', 'shopping']):
                                    description = span_text
                                    break
                            
                            # If no description found, get all text and clean it
                            if not description:
                                all_text = element.get_text(strip=True)
                                # Remove the title from the text to get description
                                if title and title in all_text:
                                    description = all_text.replace(title, '').strip()
                                else:
                                    description = all_text
                            
                            # Clean up the description
                            if description:
                                # Remove common Google UI elements
                                description = description.replace('Press/to jump to the search box', '')
                                description = description.replace('Accessibility help', '')
                                description = description.strip()
                            
                            if title or link:  # Only add if we have at least a title or link
                                organic_results.append(SearchResult(
                                    title=title,
                                    link=link,
                                    description=description,
                                    position=i + 1
                                ))
                                logger.info(f"Result {i+1}: {title[:50]}... -> {link}")
                    
                    search_results = SearchResults(
                        organic_results=organic_results,
                        total_results=len(organic_results),
                        search_query=query,
                        language=language
                    )
                    
                    logger.info(f"Found {len(organic_results)} organic results")
                    return search_results
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Response text: {response.text[:500]}")
                    return SearchResults(organic_results=[], total_results=0, search_query=query, language=language)
                
            else:
                logger.error(f"Brightdata API error: {response.status_code} - {response.text}")
                return SearchResults(organic_results=[], total_results=0, search_query=query, language=language)
                
        except Exception as e:
            logger.error(f"Error searching with Brightdata: {e}")
            return SearchResults(organic_results=[], total_results=0, search_query=query, language=language)
    
    def extract_content_from_urls(self, search_results: SearchResults, project_id: str) -> List[ContentExtraction]:
        """Extract content from URLs using r.jina.ai and unstructured, save raw HTML"""
        logger.info(f"Extracting content from {len(search_results.organic_results)} URLs")
        
        content_extractions = []
        
        for i, result in enumerate(search_results.organic_results):
            logger.info(f"Extracting content from {i+1}/{len(search_results.organic_results)}: {result.link}")
            
            try:
                # Use r.jina.ai for content extraction
                jina_url = f"https://r.jina.ai/{result.link}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
                    'Accept': 'text/plain,text/markdown,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
                
                # Try r.jina.ai first
                try:
                    jina_response = requests.get(jina_url, headers=headers, timeout=30)
                    if jina_response.status_code == 200:
                        content = jina_response.text
                        logger.info(f"Successfully extracted content via r.jina.ai from {result.link}")
                    else:
                        raise Exception(f"r.jina.ai returned status {jina_response.status_code}")
                except Exception as jina_error:
                    logger.warning(f"r.jina.ai failed for {result.link}: {jina_error}, trying unstructured")
                    
                    # Fallback to unstructured
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive',
                    }
                    
                    elements = partition(url=result.link, headers=headers, timeout=30)
                    content = "\n".join([element.text for element in elements if element.text])
                
                # Clean and group broken paragraphs
                cleaned_content = group_broken_paragraphs(content)
                
                # Truncate if too long (keep first 15000 characters for better analysis)
                if len(cleaned_content) > 15000:
                    cleaned_content = cleaned_content[:15000] + "... [Content truncated]"
                
                # Save r.jina.ai output as .md file
                md_filename = f"{project_id}_{i+1}.md"
                md_path = self.content_dir / md_filename
                
                try:
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Saved r.jina.ai output to {md_path}")
                except Exception as md_error:
                    logger.warning(f"Could not save .md file for {result.link}: {md_error}")
                
                content_extractions.append(ContentExtraction(
                    url=result.link,
                    title=result.title,
                    content=cleaned_content,
                    extraction_success=True
                ))
                
                logger.info(f"Successfully extracted {len(cleaned_content)} characters from {result.link}")
                
            except Exception as e:
                logger.error(f"Error extracting content from {result.link}: {e}")
                content_extractions.append(ContentExtraction(
                    url=result.link,
                    title=result.title,
                    content="",
                    extraction_success=False,
                    error_message=str(e)
                ))
            
            # Add delay between requests
            time.sleep(2)
        
        return content_extractions
    
    def analyze_opposition(self, project_data: Dict[str, Any], content_extractions: List[ContentExtraction]) -> OppositionAnalysis:
        """Analyze extracted content for evidence of opposition using Gemini"""
        logger.info("Analyzing content for evidence of opposition")
        
        # Create project context
        project_context = f"""
        Project Name: {project_data.get('project_name', 'Unknown')}
        Location: {project_data.get('location', 'Unknown')}
        Capacity: {project_data.get('capacity', 'Unknown')}
        Agency: {project_data.get('agency', 'Unknown')}
        Status: {project_data.get('present_status', 'Unknown')}
        """
        
        # Combine all extracted content
        all_content = ""
        sources_with_content = []
        
        for extraction in content_extractions:
            if extraction.extraction_success and extraction.content:
                all_content += f"\n\n--- Content from {extraction.url} ---\n"
                all_content += f"Title: {extraction.title}\n"
                all_content += f"Content: {extraction.content}\n"
                sources_with_content.append(extraction.url)
        
        if not all_content.strip():
            return OppositionAnalysis(
                has_opposition_evidence=False,
                opposition_types=[],
                summary="No content could be extracted from search results to analyze.",
                confidence_score=0.0,
                sources=[]
            )
        
        prompt = f"""
        Analyze the following content for any information related to this renewable energy project, including opposition, conflict, or any other project details:

        PROJECT INFORMATION:
        {project_context}

        EXTRACTED CONTENT:
        {all_content}

        Please analyze this content and determine:
        1. Is there evidence of opposition or conflict related to this specific project?
        2. What types of opposition are mentioned (e.g., land acquisition protests, environmental concerns, farmer protests, etc.)?
        3. What other project information is available (EIA reports, financial details, tariff rates, PPA information, etc.)?
        4. Provide a detailed summary of all findings
        5. Rate your confidence in this analysis (0.0 to 1.0)
        6. List the specific URLs that contained evidence

        Return your analysis in JSON format with these fields:
        - has_opposition_evidence: boolean
        - opposition_types: array of strings
        - summary: detailed string
        - confidence_score: number between 0.0 and 1.0
        - sources: array of URLs that contained evidence

        Be specific about the project name and location when making your analysis. Include any relevant project information found, not just opposition.
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            
            response_text = response.text.strip()
            
            # Try to extract JSON from the response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end]
            else:
                # Fallback analysis
                json_text = '{"has_opposition_evidence": false, "opposition_types": [], "summary": "Could not parse analysis results", "confidence_score": 0.0, "sources": []}'
            
            analysis_data = json.loads(json_text)
            analysis = OppositionAnalysis(**analysis_data)
            
            logger.info(f"Analysis complete - Opposition found: {analysis.has_opposition_evidence}")
            logger.info(f"Confidence score: {analysis.confidence_score}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing opposition: {e}")
            return OppositionAnalysis(
                has_opposition_evidence=False,
                opposition_types=[],
                summary=f"Error during analysis: {str(e)}",
                confidence_score=0.0,
                sources=[]
            )
    
    def save_data(self, project_id: str, step: str, data: Any):
        """Save data to JSON file in appropriate directory"""
        if step == "search":
            file_path = self.search_dir / f"{project_id}.json"
        elif step == "content":
            file_path = self.content_dir / f"{project_id}.json"
        elif step == "result":
            file_path = self.result_dir / f"{project_id}.json"
        elif step == "summary":
            file_path = self.summary_dir / f"{project_id}.json"
        else:
            raise ValueError(f"Invalid step: {step}")
        
        # Convert Pydantic models to dict for JSON serialization
        if hasattr(data, 'model_dump'):
            data_dict = data.model_dump()
        elif hasattr(data, 'dict'):
            data_dict = data.dict()
        else:
            data_dict = data
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {step} data to {file_path}")
    
    def analyze_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete analysis pipeline for a single project"""
        project_id = project_data.get('project_id', 'unknown')
        logger.info(f"Starting analysis for project {project_id}: {project_data.get('project_name', 'Unknown')}")
        
        try:
            # Step 1: Generate search queries
            queries = self.generate_search_queries(project_data)
            self.save_data(project_id, "search", queries)
            
            # Step 2: Search with both queries separately
            english_results = self.search_with_brightdata(queries.english_query, "en")
            bangla_results = self.search_with_brightdata(queries.bangla_query, "bn")
            
            # Convert Pydantic models to dictionaries for JSON serialization
            english_results_dict = {
                "organic_results": [result.model_dump() if hasattr(result, 'model_dump') else result.__dict__ for result in english_results.organic_results],
                "total_results": english_results.total_results,
                "search_query": english_results.search_query,
                "language": english_results.language
            }
            
            bangla_results_dict = {
                "organic_results": [result.model_dump() if hasattr(result, 'model_dump') else result.__dict__ for result in bangla_results.organic_results],
                "total_results": bangla_results.total_results,
                "search_query": bangla_results.search_query,
                "language": bangla_results.language
            }
            
            # Save results separately
            self.save_data(project_id, "result", {
                "english_search": english_results_dict,
                "bangla_search": bangla_results_dict,
                "combined_results": {
                    "organic_results": english_results_dict["organic_results"] + bangla_results_dict["organic_results"],
                    "total_results": english_results_dict["total_results"] + bangla_results_dict["total_results"],
                    "search_query": f"English: {queries.english_query} | Bangla: {queries.bangla_query}",
                    "language": "mixed"
                }
            })
            
            # Use combined results for content extraction
            all_results = SearchResults(
                organic_results=english_results.organic_results + bangla_results.organic_results,
                total_results=english_results.total_results + bangla_results.total_results,
                search_query=f"English: {queries.english_query} | Bangla: {queries.bangla_query}",
                language="mixed"
            )
            
            # Step 3: Extract content from URLs
            content_extractions = self.extract_content_from_urls(all_results, project_id)
            
            # Convert ContentExtraction objects to dictionaries for JSON serialization
            content_extractions_dict = []
            for extraction in content_extractions:
                if hasattr(extraction, 'model_dump'):
                    content_extractions_dict.append(extraction.model_dump())
                else:
                    content_extractions_dict.append({
                        'url': extraction.url,
                        'title': extraction.title,
                        'content': extraction.content,
                        'extraction_success': extraction.extraction_success,
                        'error_message': extraction.error_message
                    })
            
            self.save_data(project_id, "content", content_extractions_dict)
            
            # Step 4: Check content before analysis
            logger.info("Checking extracted content before analysis...")
            successful_extractions = [ext for ext in content_extractions if ext.extraction_success and ext.content]
            logger.info(f"Found {len(successful_extractions)} successful content extractions")
            
            if successful_extractions:
                # Log first few characters of each successful extraction
                for i, ext in enumerate(successful_extractions[:3]):  # Show first 3
                    logger.info(f"Content {i+1} preview: {ext.content[:200]}...")
            
            # Step 5: Analyze for opposition
            analysis = self.analyze_opposition(project_data, content_extractions)
            self.save_data(project_id, "summary", analysis)
            
            logger.info(f"Analysis complete for project {project_id}")
            
            return {
                "project_id": project_id,
                "project_name": project_data.get('project_name', 'Unknown'),
                "analysis": analysis,
                "total_urls_found": len(all_results.organic_results),
                "content_extracted": len([c for c in content_extractions if c.extraction_success])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing project {project_id}: {e}")
            return {
                "project_id": project_id,
                "project_name": project_data.get('project_name', 'Unknown'),
                "error": str(e)
            }

def main():
    """Main function for testing with a single project"""
    analyzer = OppositionAnalyzer()
    
    # Test with the first project from the CSV
    test_project = {
        "project_id": "351",
        "project_name": "100 MW Solar Park by Dynamic Sun Energy Private Limited",
        "location": "Pabna Sadar Upazila, Pabna",
        "capacity": "140 kWp",
        "agency": "BPDB",
        "present_status": "Completed & Running"
    }
    
    result = analyzer.analyze_project(test_project)
    print(f"\nAnalysis Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
