from tools.search import search_web

results = search_web("What is Retrieval-Augmented Generation?")

for i, result in enumerate(results, start=1):
    print("=" * 80)
    print(f"Result {i}")
    print(f"Title   : {result['title']}")
    print(f"URL     : {result['url']}")
    print(f"Content : {result['content']}")