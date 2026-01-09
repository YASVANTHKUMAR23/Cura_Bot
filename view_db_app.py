import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
import pandas as pd

DB_PATH = "./knowledge_base/chroma_db"

st.set_page_config(page_title="DB Viewer", layout="wide")
st.title("🔍 ChromaDB Viewer")

try:  # <-- Make sure this has matching except
    client = chromadb.PersistentClient(path=DB_PATH)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    collection = client.get_collection("medical_knowledge", embedding_function=embed_fn)
    
    total = collection.count()
    st.success(f"✅ Total chunks: {total}")
    
    if total > 0:
        data = collection.get(limit=20)
        
        # Show table
        df = pd.DataFrame({
            "ID": data['ids'],
            "Topic": [m.get('topic', 'N/A') for m in data['metadatas']],
            "Content": [d[:100] + "..." for d in data['documents']]
        })
        
        st.dataframe(df, use_container_width=True)
        
        # Detailed view
        idx = st.selectbox("Select chunk to view", range(len(data['ids'])))
        
        if idx is not None:
            st.subheader("Full Content")
            st.text_area("", data['documents'][idx], height=300)
            st.write(f"**URL:** {data['metadatas'][idx].get('url', 'N/A')}")
    
    else:
        st.warning("Database is empty")

except Exception as e:  # <-- This except matches the try above
    st.error(f"❌ Error: {e}")
