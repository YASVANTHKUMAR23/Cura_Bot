import chromadb
from chromadb.utils import embedding_functions
from Bio import Entrez
import time
from langchain_text_splitters import RecursiveCharacterTextSplitter


# --- CONFIGURATION ---
DB_PATH = "./knowledge_base/chroma_db"
Entrez.email = "ADD_YOUR_EMAIL_ID"  # REQUIRED by NCBI


# 20 HIGH-PRIORITY TOPICS for Rural/Semi-Urban India
# Optimized for quick ingestion (~30-40 articles total)
TOPICS = {
    # === CATEGORY 1: Common Diseases (Most Frequent) ===
    "Diabetes": "diabetes mellitus management",
    "Hypertension": "hypertension blood pressure",
    "Fever": "fever causes treatment",
    "Common Cold Flu": "influenza viral infection",
    "Asthma": "asthma treatment",
    "Tuberculosis": "tuberculosis DOTS",
    "Dengue Malaria": "dengue malaria",
    "Gastroenteritis": "diarrhea dehydration ORS",
    
    # === CATEGORY 2: Emergency Symptoms (Life-Threatening) ===
    "Chest Pain": "chest pain cardiac",
    "Heart Attack": "myocardial infarction",
    "Stroke": "stroke emergency",
    "Breathing Difficulty": "respiratory distress",
    
    # === CATEGORY 3: Preventive Care ===
    "Vaccination": "immunization vaccination",
    "Nutrition Diet": "nutrition diet health",
    "Mental Health": "depression anxiety mental health",
    
    # === CATEGORY 4: Women & Child Health ===
    "Pregnancy Care": "pregnancy antenatal care",
    "Child Health": "pediatric child health immunization",
    "Menstrual Health": "menstruation PCOS",
    
    # === COMMON SYMPTOMS ===
    "Cough": "cough respiratory tuberculosis"
}


def search_pmc(query, max_results=2):  # Reduced to 2 articles per topic
    """
    Search PMC Open Access for full-text articles.
    Returns list of PMC IDs and total available count.
    """
    print(f"🔍 Searching PMC: {query}")
    
    try:
        handle = Entrez.esearch(
            db="pmc",
            term=query,
            retmax=max_results,
            sort="relevance"
        )
        
        results = Entrez.read(handle)
        handle.close()
        
        pmc_ids = results.get("IdList", [])
        total_available = results.get("Count", 0)
        
        if len(pmc_ids) == 0:
            print(f"   ⚠️ No articles found")
            return [], 0
        
        print(f"   ✅ Found {len(pmc_ids)}/{total_available} articles")
        return pmc_ids, total_available
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return [], 0


def fetch_fulltext(pmc_id):
    """
    Fetch the full-text content of a PMC article.
    Returns (title, full_text).
    """
    try:
        handle = Entrez.efetch(
            db="pmc",
            id=pmc_id,
            rettype="xml",
            retmode="text"
        )
        
        xml_data = handle.read()
        handle.close()
        
        text_content = xml_data.decode('utf-8', errors='ignore')
        
        # Extract title
        import re
        title_match = re.search(r'<article-title>(.*?)</article-title>', text_content, re.DOTALL)
        title = title_match.group(1) if title_match else f"PMC{pmc_id}"
        
        # Clean title
        title = re.sub(r'<[^>]+>', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Clean XML tags
        text_content = re.sub(r'<[^>]+>', ' ', text_content)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        return title, text_content
        
    except Exception as e:
        print(f"   ⚠️ Error fetching PMC{pmc_id}: {e}")
        return None, None


def ingest_pmc_data():
    """
    Main ingestion function - optimized for 30-40 articles total.
    """
    print("\n" + "="*70)
    print("🚀 PMC MEDICAL KNOWLEDGE INGESTION")
    print("="*70)
    print(f"📂 Database: {DB_PATH}")
    print(f"📋 Topics: {len(TOPICS)}")
    print(f"🎯 Target: ~{len(TOPICS) * 2} articles")
    print("="*70 + "\n")
    
    # Initialize ChromaDB
    print("🔗 Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=DB_PATH)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    collection = client.get_or_create_collection(
        name="medical_knowledge",
        embedding_function=embed_fn
    )
    print("   ✅ ChromaDB ready\n")
    
    all_documents = []
    topic_stats = {}
    
    # Process each topic
    for idx, (topic_name, query) in enumerate(TOPICS.items(), 1):
        print(f"[{idx}/{len(TOPICS)}] 📚 {topic_name}")
        
        pmc_ids, total_available = search_pmc(query, max_results=2)
        
        topic_stats[topic_name] = {
            "available": total_available,
            "retrieved": len(pmc_ids),
            "stored": 0
        }
        
        if len(pmc_ids) == 0:
            topic_stats[topic_name]["status"] = "NO_DATA"
            print()
            continue
        
        # Fetch articles
        for pmc_id in pmc_ids:
            print(f"   📄 PMC{pmc_id}...", end=" ")
            
            title, fulltext = fetch_fulltext(pmc_id)
            
            if fulltext and len(fulltext) > 500:
                all_documents.append({
                    "content": fulltext,
                    "metadata": {
                        "source": "PMC Open Access",
                        "pmc_id": f"PMC{pmc_id}",
                        "title": title,
                        "topic": topic_name,
                        "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/"
                    }
                })
                topic_stats[topic_name]["stored"] += 1
                print(f"✅ ({len(fulltext):,} chars)")
            else:
                print("⚠️ Skipped")
            
            time.sleep(0.8)  # API rate limiting
        
        topic_stats[topic_name]["status"] = "SUCCESS" if topic_stats[topic_name]["stored"] > 0 else "FAILED"
        print()
    
    # Summary
    print("="*70)
    print("📊 RETRIEVAL SUMMARY")
    print("="*70)
    
    successful = sum(1 for s in topic_stats.values() if s.get("status") == "SUCCESS")
    failed = len(TOPICS) - successful
    
    print(f"✅ Successful: {successful}/{len(TOPICS)} topics")
    print(f"❌ Failed: {failed}/{len(TOPICS)} topics")
    print(f"📄 Articles Retrieved: {len(all_documents)}")
    
    # Show failed topics
    failed_topics = [t for t, s in topic_stats.items() if s.get("status") != "SUCCESS"]
    if failed_topics:
        print(f"\n⚠️ Topics with NO DATA:")
        for topic in failed_topics:
            print(f"   • {topic}")
    
    if not all_documents:
        print("\n❌ INGESTION FAILED!")
        print("   Check internet connection or try again later.")
        return
    
    # Chunking
    print(f"\n{'='*70}")
    print("🧩 CHUNKING DOCUMENTS")
    print("="*70 + "\n")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    
    doc_id = 0
    chunks_per_topic = {}
    
    for doc in all_documents:
        chunks = splitter.split_text(doc["content"])
        topic = doc["metadata"]["topic"]
        
        for chunk in chunks:
            collection.add(
                documents=[chunk],
                metadatas=[doc["metadata"]],
                ids=[f"pmc_{doc_id}"]
            )
            doc_id += 1
        
        chunks_per_topic[topic] = chunks_per_topic.get(topic, 0) + len(chunks)
        print(f"   💾 {topic}: +{len(chunks)} chunks")
    
    # Final report
    print(f"\n{'='*70}")
    print("🎉 INGESTION COMPLETE!")
    print("="*70)
    print(f"📊 Total Chunks: {doc_id}")
    print(f"📂 Location: {DB_PATH}")
    print(f"\n📈 Top Topics by Chunks:")
    
    sorted_topics = sorted(chunks_per_topic.items(), key=lambda x: x[1], reverse=True)
    for topic, count in sorted_topics[:10]:  # Show top 10
        print(f"   {topic}: {count}")
    
    print(f"\n{'='*70}")
    print("✅ Ready to run agents!")
    print("   Run: python agents/agent1_general.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    ingest_pmc_data()
