import sqlite3
import re
import json
from typing import List, Dict, Any

class DocumentCleaner:
    def __init__(self, db_path: str = "microsoft_docs.db"):
        self.db_path = db_path
        self.conn = None
        
        # Patterns to remove from content
        self.removal_patterns = [
            # Navigation and UI elements
            r'Table of contents\s*',
            r'Exit focus mode\s*',
            r'Read in English\s*',
            r'Add to Collections\s*',
            r'Add to plan\s*',
            r'Edit\s*',
            r'Print\s*',
            r'Ask Learn\s*',
            r'In this article\s*',
            
            # Social media and sharing
            r'Share via\s*',
            r'Facebook\s*',
            r'x\.com\s*',
            r'LinkedIn\s*',
            r'Email\s*',
            
            # Feedback sections
            r'Feedback\s*',
            r'Was this page helpful\?\s*',
            r'Yes\s*No\s*',
            r'Provide product feedback\s*',
            r'Additional resources\s*',
            
            # Metadata and timestamps
            r'\d{2}/\d{2}/\d{4}\s*',
            r'File metadata column\s*',
            
            # Authorization messages
            r'Access to this page requires authorization.*?directories\.\s*',
            r'Note\s*Access to this page.*?directories\.\s*',
            
            # Code block artifacts
            r"'''\s*Result:\s*",
            r"/\*\s*Result:\s*",
            r"'''\s*",
            r"\*/\s*",
            
            # Expand table elements
            r'Expand table\s*',
            
            # Navigation breadcrumbs (when they appear as separate elements)
            r'Learn\s*Azure.*?documentation\s*',
            r'Learn\s*Microsoft.*?documentation\s*',
        ]
        
        # Section headers that indicate content we want to keep
        self.content_indicators = [
            'Overview', 'Introduction', 'Getting started', 'Tutorial', 'How to',
            'Examples', 'Code', 'Syntax', 'Parameters', 'Return', 'Remarks',
            'See also', 'Next steps', 'Prerequisites', 'Requirements',
            'Description', 'Usage', 'Configuration', 'Installation',
            'Troubleshooting', 'Best practices', 'Security', 'Performance'
        ]

    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def disconnect(self):
        """Disconnect from the database."""
        if self.conn:
            self.conn.close()

    def clean_text(self, text: str) -> str:
        """Clean the text content by removing unwanted patterns."""
        if not text:
            return ""
        
        # Remove specific patterns
        for pattern in self.removal_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove excessive whitespace including tabs and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove repeated punctuation
        text = re.sub(r'[.,;:!?]{2,}', '.', text)
        
        # Remove standalone single characters (likely formatting artifacts)
        text = re.sub(r'\s+[a-zA-Z]\s+', ' ', text)
        
        # Remove lines with only special characters
        text = re.sub(r'^[^\w\s]*$', '', text, flags=re.MULTILINE)
        
        # Clean up code blocks and examples
        text = self.clean_code_blocks(text)
        
        # Remove excessive spacing around punctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])\s+', r'\1 ', text)
        
        # Final cleanup
        text = text.strip()
        
        return text

    def clean_code_blocks(self, text: str) -> str:
        """Clean up code blocks and examples while preserving their structure."""
        # Fix common code block issues
        text = re.sub(r'Python\s+(.+?)\s+Scala', r'Python:\n\1\n\nScala:', text, flags=re.DOTALL)
        text = re.sub(r'Scala\s+(.+?)(?=\n\n|\Z)', r'Scala:\n\1', text, flags=re.DOTALL)
        
        # Clean up result blocks
        text = re.sub(r'Result:\s*\+[-=+]+\+', 'Result:', text)
        text = re.sub(r'\+[-=+]*\+', '', text)
        text = re.sub(r'\|[^|]*\|', lambda m: m.group(0).strip(), text)
        
        return text

    def extract_main_content(self, text: str) -> str:
        """Extract the main content by identifying content sections."""
        if not text:
            return ""
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        # Filter out paragraphs that are likely navigation or UI elements
        content_paragraphs = []
        skip_next = False
        
        for i, paragraph in enumerate(paragraphs):
            if skip_next:
                skip_next = False
                continue
                
            # Skip very short paragraphs that are likely UI elements
            if len(paragraph) < 10:
                continue
                
            # Skip paragraphs that are just numbers or single words
            if re.match(r'^\d+$', paragraph) or len(paragraph.split()) == 1:
                continue
                
            # Keep paragraphs that contain actual content
            if (len(paragraph) > 50 or 
                any(indicator.lower() in paragraph.lower() for indicator in self.content_indicators) or
                ':' in paragraph or
                '.' in paragraph):
                content_paragraphs.append(paragraph)
        
        return '\n\n'.join(content_paragraphs)

    def is_quality_content(self, content: str) -> bool:
        """Check if the content meets quality standards."""
        if not content or len(content.strip()) < 100:
            return False
        
        # Check if content has meaningful sentences
        sentences = re.split(r'[.!?]+', content)
        meaningful_sentences = [s for s in sentences if len(s.strip()) > 20]
        
        if len(meaningful_sentences) < 2:
            return False
        
        # Check for code examples or technical content
        has_technical_content = any([
            'def ' in content, 'class ' in content, 'import ' in content,
            'SELECT' in content, 'FROM' in content,
            'public ' in content, 'private ' in content,
            'example' in content.lower(), 'code' in content.lower(),
            'syntax' in content.lower(), 'parameter' in content.lower()
        ])
        
        # Content should be either long enough or have technical content
        return len(content) > 200 or has_technical_content

    def clean_documents(self, batch_size: int = 100) -> Dict[str, int]:
        """Clean all documents in the database."""
        if not self.conn:
            self.connect()
        
        # Get total count
        total_count = self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        print(f"📄 Processing {total_count} documents...")
        
        stats = {
            'processed': 0,
            'cleaned': 0,
            'removed': 0,
            'improved': 0
        }
        
        # Process in batches
        offset = 0
        while offset < total_count:
            cursor = self.conn.execute(
                "SELECT id, url, title, content, word_count FROM documents LIMIT ? OFFSET ?",
                (batch_size, offset)
            )
            
            documents = cursor.fetchall()
            
            for doc in documents:
                stats['processed'] += 1
                
                # Clean the content
                original_content = doc['content']
                cleaned_content = self.clean_text(original_content)
                main_content = self.extract_main_content(cleaned_content)
                
                # Check content quality
                if not self.is_quality_content(main_content):
                    # Remove low-quality documents
                    self.conn.execute("DELETE FROM documents WHERE id = ?", (doc['id'],))
                    stats['removed'] += 1
                    print(f"Removed low-quality document: {doc['title']}")
                    continue
                
                # Update if content was improved
                if main_content != original_content:
                    new_word_count = len(main_content.split())
                    
                    self.conn.execute(
                        """UPDATE documents 
                           SET content = ?, word_count = ?, content_type = 'cleaned'
                           WHERE id = ?""",
                        (main_content, new_word_count, doc['id'])
                    )
                    
                    stats['improved'] += 1
                    improvement = len(original_content) - len(main_content)
                    print(f"Cleaned: {doc['title'][:50]}... (reduced by {improvement} chars)")
                else:
                    stats['cleaned'] += 1
            
            # Commit batch
            self.conn.commit()
            offset += batch_size
            
            # Progress update
            progress = (offset / total_count) * 100
            print(f"Progress: {progress:.1f}% ({offset}/{total_count})")
        
        return stats

    def export_cleaned_data(self, output_file: str = "cleaned_documents.json"):
        """Export cleaned documents to JSON file."""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.execute(
            """SELECT url, title, content, category, subcategory, word_count, scraped_at
               FROM documents 
               WHERE content_type = 'cleaned' OR content_type = 'documentation'
               ORDER BY category, subcategory, title"""
        )
        
        documents = []
        for row in cursor:
            documents.append({
                'url': row['url'],
                'title': row['title'],
                'content': row['content'],
                'category': row['category'],
                'subcategory': row['subcategory'],
                'word_count': row['word_count'],
                'scraped_at': row['scraped_at']
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(documents)} cleaned documents to {output_file}")
        return len(documents)

    def get_cleaning_stats(self) -> Dict[str, Any]:
        """Get statistics about the cleaned data."""
        if not self.conn:
            self.connect()
        
        stats = self.conn.execute("""
            SELECT 
                COUNT(*) as total_docs,
                SUM(word_count) as total_words,
                AVG(word_count) as avg_words_per_doc,
                COUNT(DISTINCT category) as categories,
                MIN(word_count) as min_words,
                MAX(word_count) as max_words
            FROM documents
        """).fetchone()
        
        return dict(stats)

def main():
    cleaner = DocumentCleaner()
    
    try:
        # Clean the documents
        print("Starting document cleaning process...")
        cleaning_stats = cleaner.clean_documents()
        
        print("\nCleaning Results:")
        for key, value in cleaning_stats.items():
            print(f"  {key.title()}: {value}")
        
        # Export cleaned data
        print("\nExporting cleaned documents...")
        exported_count = cleaner.export_cleaned_data()
        
        # Show final stats
        print("\nFinal Statistics:")
        final_stats = cleaner.get_cleaning_stats()
        for key, value in final_stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"Error during cleaning: {e}")
    finally:
        cleaner.disconnect()

if __name__ == "__main__":
    main()
