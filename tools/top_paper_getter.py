"""
A simple script to get the top ArXiv paper by upvotes for the current day and return its PDF URL.
This can be used as a function tool in the OpenAI Agent SDK.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from datasets import load_dataset
from agents import function_tool  # Import the function_tool decorator

# Constants
ARXIV_PDF_URL_PATTERN = "https://arxiv.org/pdf/{paper_id}"
DATE_FORMAT = "%Y-%m-%d"

# Apply the function_tool decorator directly to the function
@function_tool
async def get_top_paper_pdf_url(date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the top ArXiv paper by upvotes for a specific date and return its PDF URL.
    
    Args:
        date: Optional date string in YYYY-MM-DD format. If not provided, today's date will be used.
        
    Returns:
        A dictionary containing information about the top paper, including:
        - paper_id: The ArXiv ID of the paper
        - title: The title of the paper
        - authors: List of authors
        - upvotes: Number of upvotes
        - date: Date of the paper
        - pdf_url: URL to the PDF of the paper
    """
    # Use today's date if not provided
    if not date:
        date = datetime.now().strftime(DATE_FORMAT)
    
    # Validate date format
    try:
        datetime.strptime(date, DATE_FORMAT)
    except ValueError:
        raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD.")
    
    # Get top paper for the date
    top_paper = _get_top_paper_by_date(date)
    
    # Extract paper ID
    paper_id = top_paper.get("paper_id", top_paper.get("arxiv_id", ""))
    
    # Ensure paper_id is clean (without version)
    if "v" in paper_id:
        paper_id = paper_id.split("v")[0]
    
    # Generate PDF URL
    pdf_url = ARXIV_PDF_URL_PATTERN.format(paper_id=paper_id)
    
    return {
        "paper_id": paper_id,
        "title": top_paper.get("title", ""),
        "authors": top_paper.get("authors", []),
        "upvotes": top_paper.get("upvotes", 0),
        "date": top_paper.get("date", ""),
        "pdf_url": pdf_url
    }

def _get_top_paper_by_date(target_date: str, max_days_to_look_back: int = 7) -> Dict[str, Any]:
    """
    Helper function to get the top paper by upvotes for a specific date.
    
    Args:
        target_date: Target date in YYYY-MM-DD format.
        max_days_to_look_back: Maximum number of days to look back if no papers found on target date.
    
    Returns:
        Dictionary containing the top paper's data.
        
    Raises:
        ValueError: If no papers are found within the look-back period.
    """
    # Parse the target date
    target_date_obj = datetime.strptime(target_date, DATE_FORMAT)
    
    # Load the datasets
    try:
        daily_papers = load_dataset("hysts-bot-data/daily-papers", split="train")
        daily_papers_stats = load_dataset("hysts-bot-data/daily-papers-stats", split="train")
    except Exception as e:
        # Fallback to legacy dataset
        try:
            return _get_top_paper_from_legacy_dataset(target_date, max_days_to_look_back)
        except Exception as e2:
            raise ValueError(f"Failed to load datasets: {str(e2)}")
    
    # Convert to pandas DataFrames for easier merging
    papers_df = pd.DataFrame(daily_papers)
    stats_df = pd.DataFrame(daily_papers_stats)
    
    # Merge on arxiv_id
    merged_df = pd.merge(papers_df, stats_df, on="arxiv_id", how="inner")
    
    # Sort by upvotes in descending order
    merged_df = merged_df.sort_values(by="upvotes", ascending=False)
    
    # Look for papers starting from the target date and going back up to max_days_to_look_back
    for days_back in range(max_days_to_look_back + 1):
        check_date = target_date_obj - timedelta(days=days_back)
        check_date_str = check_date.strftime(DATE_FORMAT)
        
        # Filter for papers on this date
        date_papers = None
        
        # Check if we have a 'date' field
        if "date" in merged_df.columns:
            # Convert date column to string to ensure proper comparison
            date_papers = merged_df[merged_df["date"].astype(str).str.startswith(check_date_str)]
        
        # If not found, check 'created' field
        if (date_papers is None or len(date_papers) == 0) and "created" in merged_df.columns:
            # Extract date part from created field (could be in ISO format)
            created_date_mask = merged_df["created"].astype(str).apply(
                lambda x: x.split("T")[0] if "T" in x else x
            ) == check_date_str
            date_papers = merged_df[created_date_mask]
        
        if date_papers is not None and len(date_papers) > 0:
            # Return the top paper (already sorted by upvotes)
            top_paper = date_papers.iloc[0].to_dict()
            
            # Ensure we have a consistent format
            # If authors is a string, try to convert it to a list
            if "authors" in top_paper and isinstance(top_paper["authors"], str):
                import json
                try:
                    top_paper["authors"] = json.loads(top_paper["authors"].replace("'", "\""))
                except:
                    top_paper["authors"] = [a.strip() for a in top_paper["authors"].split(",")]
            
            return top_paper
    
    # If we get here, we didn't find any papers
    raise ValueError(f"No papers found within {max_days_to_look_back} days of {target_date}")

def _get_top_paper_from_legacy_dataset(target_date: str, max_days_to_look_back: int = 7) -> Dict[str, Any]:
    """
    Fallback function to get the top paper from the legacy dataset.
    
    Args:
        target_date: Target date in YYYY-MM-DD format.
        max_days_to_look_back: Maximum number of days to look back if no papers found on target date.
    
    Returns:
        Dictionary containing the top paper's data.
        
    Raises:
        ValueError: If no papers are found within the look-back period.
    """
    # Parse the target date
    target_date_obj = datetime.strptime(target_date, DATE_FORMAT)
    
    # Load the legacy dataset
    dataset = load_dataset("justinxzhao/hf_daily_papers", split="train")
    
    # Convert to DataFrame
    df = pd.DataFrame(dataset)
    
    # Sort by upvotes/score
    score_column = "upvotes" if "upvotes" in df.columns else "score"
    if score_column in df.columns:
        df = df.sort_values(by=score_column, ascending=False)
    
    # Look for papers starting from the target date and going back
    for days_back in range(max_days_to_look_back + 1):
        check_date = target_date_obj - timedelta(days=days_back)
        check_date_str = check_date.strftime(DATE_FORMAT)
        
        # Filter for papers on this date
        date_papers = None
        
        # Check if we have a 'date' field
        if "date" in df.columns:
            date_papers = df[df["date"].astype(str).str.startswith(check_date_str)]
        
        # If not found, check 'created' field
        if (date_papers is None or len(date_papers) == 0) and "created" in df.columns:
            created_date_mask = df["created"].astype(str).apply(
                lambda x: x.split("T")[0] if "T" in x else x
            ) == check_date_str
            date_papers = df[created_date_mask]
        
        if date_papers is not None and len(date_papers) > 0:
            # Return the top paper
            top_paper = date_papers.iloc[0].to_dict()
            
            # Ensure we have a consistent format
            if "authors" in top_paper and isinstance(top_paper["authors"], str):
                import json
                try:
                    top_paper["authors"] = json.loads(top_paper["authors"].replace("'", "\""))
                except:
                    top_paper["authors"] = [a.strip() for a in top_paper["authors"].split(",")]
            
            return top_paper
    
    # If we get here, we didn't find any papers
    raise ValueError(f"No papers found within {max_days_to_look_back} days of {target_date}")

# Example usage when running as a standalone script
if __name__ == "__main__":
    import asyncio
    
    async def main():
        try:
            # Get today's top paper
            today = datetime.now().strftime(DATE_FORMAT)
            result = await get_top_paper_pdf_url(today)
            print(f"Top paper for {today}:")
            print(f"Title: {result['title']}")
            print(f"Authors: {', '.join(result['authors'])}")
            print(f"Upvotes: {result['upvotes']}")
            print(f"PDF URL: {result['pdf_url']}")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(main())