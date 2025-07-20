import requests
from bs4 import BeautifulSoup
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re

# Database configuration
DB_CONFIG = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_NRo1IkM7bQrj",
    "host": "ep-morning-wildflower-a1wn2f3t-pooler.ap-southeast-1.aws.neon.tech",
    "port": 5432,
    "sslmode": "require"
}

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ParentCircleScraper:
    def __init__(self):
        self.base_url = "https://www.parentcircle.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def create_database_table(self):
        """Create the feed_resource table if it doesn't exist"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            create_table_query = """
            CREATE TABLE IF NOT EXISTS feed_resource (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                url VARCHAR(1000) UNIQUE NOT NULL,
                content TEXT,
                summary TEXT,
                author VARCHAR(200),
                published_date DATE,
                category VARCHAR(100),
                tags TEXT[],
                source VARCHAR(100) DEFAULT 'Parent Circle',
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                word_count INTEGER,
                reading_time INTEGER
            );
            
            CREATE INDEX IF NOT EXISTS idx_feed_resource_category ON feed_resource(category);
            CREATE INDEX IF NOT EXISTS idx_feed_resource_tags ON feed_resource USING GIN(tags);
            CREATE INDEX IF NOT EXISTS idx_feed_resource_published ON feed_resource(published_date);
            """
            
            cursor.execute(create_table_query)
            conn.commit()
            logger.info("Database table 'feed_resource' created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database table: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_article_links(self, category_urls=None):
        """Extract article links from Parent Circle"""
        if category_urls is None:
            category_urls = [
                f"{self.base_url}/parenting",
                f"{self.base_url}/child-development",
                f"{self.base_url}/special-needs",
                f"{self.base_url}/health",
                f"{self.base_url}/education"
            ]
        
        all_links = set()
        
        for category_url in category_urls:
            try:
                logger.info(f"Scraping category: {category_url}")
                response = self.session.get(category_url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find article links - adjust selectors based on site structure
                article_links = soup.find_all('a', href=True)
                
                for link in article_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.base_url, href)
                        # Filter for article URLs
                        if self.is_article_url(full_url):
                            all_links.add(full_url)
                
                time.sleep(1)  # Be respectful with requests
                
            except Exception as e:
                logger.error(f"Error scraping category {category_url}: {e}")
                continue
        
        logger.info(f"Found {len(all_links)} unique article links")
        return list(all_links)
    
    def is_article_url(self, url):
        """Check if URL is likely an article"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Exclude non-article pages
        exclude_patterns = [
            '/category/', '/tag/', '/author/', '/page/', '/search/',
            '.jpg', '.png', '.gif', '.pdf', '/contact', '/about',
            '/privacy', '/terms', '#', 'javascript:'
        ]
        
        for pattern in exclude_patterns:
            if pattern in path:
                return False
        
        # Include if it looks like an article
        return len(path.split('/')) >= 2 and path != '/'
    
    def extract_article_content(self, url):
        """Extract content from a single article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract article data - adjust selectors based on actual site structure
            article_data = {
                'url': url,
                'title': self.extract_title(soup),
                'content': self.extract_content(soup),
                'summary': self.extract_summary(soup),
                'author': self.extract_author(soup),
                'published_date': self.extract_date(soup),
                'category': self.extract_category(soup, url),
                'tags': self.extract_tags(soup)
            }
            
            # Calculate word count and reading time
            if article_data['content']:
                word_count = len(article_data['content'].split())
                article_data['word_count'] = word_count
                article_data['reading_time'] = max(1, word_count // 200)  # Assume 200 words per minute
            
            return article_data
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def extract_title(self, soup):
        """Extract article title"""
        selectors = ['h1', 'title', '.post-title', '.article-title', '.entry-title']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return "No title found"
    
    def extract_content(self, soup):
        """Extract main article content"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try different content selectors
        content_selectors = [
            '.post-content', '.article-content', '.entry-content', 
            '.content', 'main', 'article'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # Get all paragraph text
                paragraphs = content_div.find_all(['p', 'div'])
                content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                if len(content) > 100:  # Ensure we got substantial content
                    return content
        
        # Fallback: get all paragraph text
        paragraphs = soup.find_all('p')
        content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        return content if content else "No content found"
    
    def extract_summary(self, soup):
        """Extract article summary/excerpt"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        # Try excerpt or summary classes
        excerpt = soup.select_one('.excerpt, .summary, .post-excerpt')
        if excerpt:
            return excerpt.get_text().strip()
        
        return None
    
    def extract_author(self, soup):
        """Extract author name"""
        author_selectors = ['.author', '.post-author', '.by-author', '[rel="author"]']
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        return None
    
    def extract_date(self, soup):
        """Extract publication date"""
        # Look for date in various formats
        date_selectors = ['time', '.date', '.post-date', '.published']
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get('datetime') or element.get_text()
                if date_text:
                    # Try to parse date
                    try:
                        # Handle various date formats
                        import dateutil.parser
                        parsed_date = dateutil.parser.parse(date_text)
                        return parsed_date.date()
                    except:
                        continue
        return None
    
    def extract_category(self, soup, url):
        """Extract article category"""
        # Try to get from breadcrumbs or category links
        category_selectors = ['.category', '.post-category', '.breadcrumb']
        
        for selector in category_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        # Extract from URL path
        path_parts = url.split('/')
        if len(path_parts) > 3:
            return path_parts[3].replace('-', ' ').title()
        
        return "General"
    
    def extract_tags(self, soup):
        """Extract article tags"""
        tags = []
        tag_selectors = ['.tags a', '.post-tags a', '.tag-links a']
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                tag = element.get_text().strip()
                if tag:
                    tags.append(tag)
        
        return tags if tags else None
    
    def save_to_database(self, article_data):
        """Save article data to database"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO feed_resource 
            (title, url, content, summary, author, published_date, category, tags, word_count, reading_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                summary = EXCLUDED.summary,
                author = EXCLUDED.author,
                published_date = EXCLUDED.published_date,
                category = EXCLUDED.category,
                tags = EXCLUDED.tags,
                word_count = EXCLUDED.word_count,
                reading_time = EXCLUDED.reading_time,
                scraped_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(insert_query, (
                article_data['title'],
                article_data['url'],
                article_data['content'],
                article_data['summary'],
                article_data['author'],
                article_data['published_date'],
                article_data['category'],
                article_data['tags'],
                article_data.get('word_count'),
                article_data.get('reading_time')
            ))
            
            conn.commit()
            logger.info(f"Saved article: {article_data['title']}")
            
        except Exception as e:
            logger.error(f"Error saving article to database: {e}")
        finally:
            if conn:
                conn.close()
    
    def scrape_all_articles(self, max_articles=50):
        """Main method to scrape articles"""
        logger.info("Starting Parent Circle scraping...")
        
        # Create database table
        self.create_database_table()
        
        # Get article links
        article_links = self.get_article_links()
        
        # Limit number of articles to scrape
        article_links = article_links[:max_articles]
        
        scraped_count = 0
        for i, url in enumerate(article_links, 1):
            logger.info(f"Processing article {i}/{len(article_links)}: {url}")
            
            article_data = self.extract_article_content(url)
            if article_data:
                self.save_to_database(article_data)
                scraped_count += 1
            
            # Be respectful with requests
            time.sleep(2)
        
        logger.info(f"Scraping completed. Successfully scraped {scraped_count} articles.")

# Usage example
if __name__ == "__main__":
    scraper = ParentCircleScraper()
    
    # Scrape up to 50 articles
    scraper.scrape_all_articles(max_articles=50)
    
    # You can also scrape specific categories
    # scraper.scrape_all_articles(category_urls=["https://www.parentcircle.com/special-needs"])