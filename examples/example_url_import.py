"""
Example: URL Ingestion

Demonstrates how to import web pages into the knowledge base.
"""

import httpx
import json

BASE_URL = "http://localhost:8000"


def main():
    client = httpx.Client(base_url=BASE_URL, timeout=60)

    print("=" * 60)
    print("  URL Ingestion Examples")
    print("=" * 60)

    # =========================================================================
    # 1. Import a single URL
    # =========================================================================
    print("\n--- 1. Import Single URL ---")
    response = client.post("/knowledge/ingest/url", json={
        "urls": ["https://www.zstack.io/help/product_manerta/"],
        "document_type": "product_doc",
        "force_refresh": False,
    })
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    # =========================================================================
    # 2. Import multiple URLs
    # =========================================================================
    print("\n--- 2. Import Multiple URLs ---")
    response = client.post("/knowledge/ingest/url", json={
        "urls": [
            "https://www.zstack.io/help/tutorials/",
            "https://www.zstack.io/product/zstack_cloud/",
        ],
        "document_type": "web",
        "force_refresh": False,
    })
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    # =========================================================================
    # 3. Force refresh a URL (re-fetch)
    # =========================================================================
    print("\n--- 3. Force Refresh URL ---")
    response = client.post("/knowledge/refresh/url", json={
        "urls": ["https://www.zstack.io/help/product_manerta/"],
        "document_type": "product_doc",
    })
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    # =========================================================================
    # 4. Search imported content
    # =========================================================================
    print("\n--- 4. Search Imported Content ---")
    response = client.get("/knowledge/search", params={
        "query": "ZStack产品功能",
        "top_k": 3,
        "source_type": "url",
    })
    print(f"Status: {response.status_code}")
    data = response.json()
    for r in data.get("results", []):
        print(f"\n  Score: {r['score']}")
        print(f"  Source: {r['metadata'].get('source', 'N/A')}")
        print(f"  Content: {r['content'][:200]}...")

    # =========================================================================
    # 5. List all documents
    # =========================================================================
    print("\n--- 5. List All Documents ---")
    response = client.get("/knowledge/documents")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total sources: {data['total']}")
    for doc in data.get("documents", [])[:10]:
        print(f"  - [{doc['source_type']}] {doc['source']} ({doc['chunk_count']} chunks)")

    print("\n" + "=" * 60)
    print("  URL ingestion examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
