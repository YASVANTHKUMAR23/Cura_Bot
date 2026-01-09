import requests
import logging
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import db
from database.models import RiskLevel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PMCDiseaseIngestion:
    """
    Ingest disease information from PMC articles
    """
    
    def __init__(self):
        self.db = db
        self.base_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        logger.info('PMC Disease Ingestion initialized')
    
    def search_pmc(self, disease_name: str, max_results: int = 5) -> List[str]:
        """
        Search PMC for articles about a disease
        
        Args:
            disease_name: Disease to search
            max_results: Max articles to return
        
        Returns:
            List of PMC IDs
        """
        
        try:
            search_url = f'{self.base_url}/esearch.fcgi'
            params = {
                'db': 'pmc',
                'term': f'{disease_name}[Title/Abstract]',
                'retmax': max_results,
                'retmode': 'json'
            }
            
            response = requests.get(search_url, params=params)
            data = response.json()
            
            pmc_ids = data.get('esearchresult', {}).get('idlist', [])
            
            logger.info(f'Found {len(pmc_ids)} PMC articles for {disease_name}')
            
            return pmc_ids
        
        except Exception as e:
            logger.error(f'PMC search error: {e}')
            return []
    
    def fetch_article(self, pmc_id: str) -> Dict:
        """
        Fetch article content from PMC
        
        Args:
            pmc_id: PMC article ID
        
        Returns:
            Dict with title, abstract, content
        """
        
        try:
            fetch_url = f'{self.base_url}/efetch.fcgi'
            params = {
                'db': 'pmc',
                'id': pmc_id,
                'retmode': 'xml'
            }
            
            response = requests.get(fetch_url, params=params)
            
            # Simple XML parsing (for demo purposes)
            content = response.text
            
            # Extract title and abstract
            title = self._extract_between(content, '<article-title>', '</article-title>')
            abstract = self._extract_between(content, '<abstract>', '</abstract>')
            
            return {
                'pmc_id': pmc_id,
                'title': title,
                'abstract': abstract,
                'content': content[:5000]
            }
        
        except Exception as e:
            logger.error(f'Fetch article error: {e}')
            return {}
    
    def _extract_between(self, text: str, start: str, end: str) -> str:
        """Extract text between tags"""
        
        try:
            start_idx = text.find(start)
            if start_idx == -1:
                return ''
            
            start_idx += len(start)
            end_idx = text.find(end, start_idx)
            
            if end_idx == -1:
                return ''
            
            return text[start_idx:end_idx].strip()
        
        except Exception:
            return ''
    
    def extract_disease_info(self, article: Dict) -> Dict:
        """
        Extract disease information from article
        
        Args:
            article: Article dict
        
        Returns:
            Disease information dict
        """
        
        # Simple extraction (in production, use NLP/LLM)
        text = f"{article.get('title', '')} {article.get('abstract', '')}"
        
        symptoms = []
        if 'fever' in text.lower():
            symptoms.append('fever')
        if 'cough' in text.lower():
            symptoms.append('cough')
        if 'pain' in text.lower():
            symptoms.append('pain')
        
        return {
            'symptoms': symptoms,
            'description': article.get('abstract', '')[:500]
        }
    
    def ingest_disease(self, disease_name: str, risk_level: RiskLevel):
        """
        Ingest disease data from PMC
        
        Args:
            disease_name: Disease name
            risk_level: Risk level enum
        """
        
        logger.info(f'Ingesting disease: {disease_name}')
        
        pmc_ids = self.search_pmc(disease_name)
        
        if not pmc_ids:
            logger.warning(f'No PMC articles found for {disease_name}')
            return
        
        all_symptoms = set()
        descriptions = []
        
        for pmc_id in pmc_ids[:3]:
            article = self.fetch_article(pmc_id)
            
            if article:
                info = self.extract_disease_info(article)
                all_symptoms.update(info['symptoms'])
                descriptions.append(info['description'])
        
        disease_data = {
            'disease_name': disease_name,
            'common_symptoms': list(all_symptoms),
            'risk_level': risk_level.value,
            'description': ' '.join(descriptions)[:1000]
        }
        
        try:
            self.db.client.table('diseases').insert(disease_data).execute()
            logger.info(f'Successfully ingested {disease_name}')
        
        except Exception as e:
            logger.error(f'Database insert error: {e}')


def main():
    """Main ingestion script"""
    
    ingestion = PMCDiseaseIngestion()
    
    diseases_to_ingest = [
        ('Heart Attack', RiskLevel.CRITICAL_RISK),
        ('Dengue', RiskLevel.HIGH_RISK),
        ('Malaria', RiskLevel.HIGH_RISK),
        ('Tuberculosis', RiskLevel.HIGH_RISK),
        ('Common Cold', RiskLevel.LOW_RISK)
    ]
    
    for disease_name, risk_level in diseases_to_ingest:
        ingestion.ingest_disease(disease_name, risk_level)


if __name__ == '__main__':
    main()

