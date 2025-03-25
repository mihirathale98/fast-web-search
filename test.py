import asyncio
import os
from fastwebsearch import FastWebSearch, BraveSearchEngine
from datetime import datetime

async def main():
    # Initialize the Brave search engine with your API key
    brave_engine = BraveSearchEngine(api_key=os.getenv("BRAVE_API_KEY"))
    
    try:
        # Initialize FastWebSearch with optimizations
        fws = FastWebSearch(
            search_engine=brave_engine,
            max_concurrent_searches=5,
            rate_limit=10,
            cache_ttl=3600
        )
        
        # Test queries
        queries = [
            "Python scraping",
            "Python aio scraping",
            "Python concurrent scraping",
            "Python async scraping"
        ]
        
        # Measure execution time
        start_time = datetime.now()
        
        # Perform concurrent searches
        results = await fws.multi_search(
            queries=queries,
            max_results=10
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Print results
        print(f"\nExecution time: {execution_time:.2f} seconds")
        print("\nSearch Results:")
        print("-" * 50)
        
        for query, search_results in results.items():
            print(f"\nResults for '{query}':")
            for result in search_results:
                print(f"\nTitle: {result.title}")
                print(f"URL: {result.url}")
                print(f"Snippet: {result.snippet[:200]}...")
                print(f"Source: {result.source}")
                print(f"Timestamp: {result.timestamp}")
                if result.metadata:
                    print(f"Metadata: {result.metadata}")
                print("-" * 30)
    finally:
        # Clean up the session
        await brave_engine.close()

if __name__ == "__main__":
    asyncio.run(main())


