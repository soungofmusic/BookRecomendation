from flask import Flask, request, jsonify
import requests
import time
from typing import List, Dict, Any, Tuple, Optional
from collections import Counter
from datetime import datetime, timedelta
import os
from threading import Lock
from dotenv import load_dotenv
from groq import Groq
from flask_cors import CORS
import math
import re

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://lemon-water-065707a1e.4.azurestaticapps.net"],
        "methods": ["GET", "POST", "OPTIONS"],  # Added GET and OPTIONS
        "allow_headers": ["Content-Type", "Accept", "Authorization"],  # Added Authorization
        "expose_headers": ["Content-Type"],
        "supports_credentials": True,
        "max_age": 600  # Cache preflight requests for 10 minutes
    }
})

if not os.environ.get("GROQ_API_KEY"):
    print("Warning: GROQ_API_KEY not found in environment variables")

OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_WORKS = "https://openlibrary.org/works/"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Timeout configurations
GROQ_TIMEOUT = 900  # 15 minutes
OPENLIB_TIMEOUT = 240  # 6 minutes
MAX_RETRIES = 5


@app.route('/')
def home():
    return "Book Recommendation API is running!"

@app.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({"message": "hello"})


class RateLimiter:
    def __init__(self, requests_per_day: int, tokens_per_minute: int):
        self.daily_limit = requests_per_day
        self.minute_limit = tokens_per_minute
        self.daily_requests = 0
        self.minute_tokens = 0
        self.last_reset = datetime.now()
        self.minute_reset = datetime.now()
        self.lock = Lock()

    def can_make_request(self, estimated_tokens: int) -> bool:
        with self.lock:
            current_time = datetime.now()
            if current_time - self.last_reset > timedelta(days=1):
                self.daily_requests = 0
                self.last_reset = current_time
            if current_time - self.minute_reset > timedelta(minutes=1):
                self.minute_tokens = 0
                self.minute_reset = current_time

            if (self.daily_requests < self.daily_limit and
                    self.minute_tokens + estimated_tokens <= self.minute_limit):
                self.daily_requests += 1
                self.minute_tokens += estimated_tokens
                return True
            return False

def apply_filters(recommendations: List[Dict], filters: Dict) -> List[Dict]:
    if not filters or not recommendations:
        return recommendations

    filtered_books = []
    for book in recommendations:
        if not book:
            continue

        if filters.get('genre'):
            if not book.get('genres') or filters['genre'] not in book['genres']:
                continue

        if filters.get('yearRange'):
            min_year, max_year = filters['yearRange']
            if not book.get('year') or book['year'] < min_year or book['year'] > max_year:
                continue

        if filters.get('minScore') is not None:
            if not book.get('similarity_score') or book['similarity_score'] < filters['minScore']:
                continue

        filtered_books.append(book)

    return filtered_books

class LightweightBookRecommender:
    """A memory-efficient book recommendation engine without ML dependencies"""
    
    def __init__(self):
        # Define weights for different features
        self.weights = {
            'subject_match': 0.40,    # Genre/subject overlap
            'subject_depth': 0.15,    # How specifically the genres match
            'year_relevance': 0.15,   # Publication year proximity
            'author_relation': 0.15,  # Related authors/similar books
            'popularity': 0.15,       # Book popularity (editions, etc.)
        }
        
        # Stopwords to remove from subjects for better matching
        self.common_words = set(['fiction', 'novel', 'book', 'literature', 'story', 'stories', 'the', 'and', 'of', 'in'])
        
        print("Lightweight Book Recommender initialized successfully")
    
    def extract_year(self, date_str: str) -> Optional[int]:
        """Extract publication year from date string"""
        if not date_str:
            return None
        try:
            return int(str(date_str)[:4])
        except (ValueError, TypeError):
            import re
            year_match = re.search(r'\d{4}', str(date_str).strip())
            if year_match:
                return int(year_match.group())
            return None
    
    def normalize_subject(self, subject: str) -> str:
        """Clean and normalize a subject/genre string"""
        if not subject:
            return ""
        
        # Lowercase and remove special characters
        subject = subject.lower()
        subject = re.sub(r'[^\w\s]', '', subject)
        
        # Remove common words
        words = [w for w in subject.split() if w not in self.common_words]
        
        return " ".join(words).strip()
    
    def calculate_subject_match(self, book_subjects: List[str], input_subjects: List[str]) -> float:
        """Calculate improved subject/genre matching score"""
        if not book_subjects or not input_subjects:
            return 0.0
        
        # Clean and normalize subjects
        book_subj_clean = [self.normalize_subject(s) for s in book_subjects if s]
        input_subj_clean = [self.normalize_subject(s) for s in input_subjects if s]
        
        book_subj_clean = [s for s in book_subj_clean if s]  # Remove empty strings
        input_subj_clean = [s for s in input_subj_clean if s]
        
        if not book_subj_clean or not input_subj_clean:
            return 0.0
        
        # Calculate weighted Jaccard similarity
        # - Primary subjects (first 3) get higher weight
        primary_weight = 0.7
        secondary_weight = 0.3
        
        primary_book = set(book_subj_clean[:3])
        primary_input = set(input_subj_clean[:3])
        secondary_book = set(book_subj_clean[3:])
        secondary_input = set(input_subj_clean[3:])
        
        # Calculate similarities
        primary_intersection = len(primary_book.intersection(primary_input))
        primary_union = len(primary_book.union(primary_input))
        
        all_book = primary_book.union(secondary_book)
        all_input = primary_input.union(secondary_input)
        all_intersection = len(all_book.intersection(all_input))
        all_union = len(all_book.union(all_input))
        
        # Calculate scores
        primary_score = primary_intersection / primary_union if primary_union > 0 else 0
        all_score = all_intersection / all_union if all_union > 0 else 0
        
        # Combine scores with weights
        final_score = (primary_weight * primary_score) + (secondary_weight * all_score)
        
        return final_score
    
    def calculate_subject_depth(self, book_subjects: List[str], input_subjects: List[str]) -> float:
        """Assess how specifically the genres match beyond basic overlap"""
        if not book_subjects or not input_subjects:
            return 0.0
        
        # Count term frequencies across both sets
        book_terms = Counter()
        input_terms = Counter()
        
        for subject in book_subjects:
            for word in self.normalize_subject(subject).split():
                if word:
                    book_terms[word] += 1
                    
        for subject in input_subjects:
            for word in self.normalize_subject(subject).split():
                if word:
                    input_terms[word] += 1
        
        # Find shared terms that are relatively uncommon
        shared_terms = set(book_terms.keys()).intersection(set(input_terms.keys()))
        
        if not shared_terms:
            return 0.0
            
        # Score based on specificity - terms appearing in fewer subjects are weighted more
        specificity_score = 0
        for term in shared_terms:
            # Lower frequency terms get higher weight
            term_weight = 1.0 / (book_terms[term] + input_terms[term])
            specificity_score += term_weight
            
        # Normalize
        max_possible = len(shared_terms)  # Maximum if all terms appeared exactly once
        normalized_score = min(specificity_score / max_possible, 1.0) if max_possible > 0 else 0
        
        return normalized_score
    
    def calculate_year_relevance(self, book_year: Optional[int], input_years: List[int]) -> float:
        """Calculate similarity based on publication year proximity"""
        if not book_year or not input_years:
            return 0.5  # Neutral score if years unknown
            
        avg_year = sum(input_years) / len(input_years)
        
        # Implement a sigmoid-like function for year difference
        # This gives more weight to books from similar time periods
        year_diff = abs(book_year - avg_year)
        
        if year_diff <= 5:
            return 1.0  # Very close years
        elif year_diff <= 20:
            return 0.8  # Same generation
        elif year_diff <= 50:
            return 0.6  # Within living memory
        elif year_diff <= 100:
            return 0.4  # Historical but not ancient
        else:
            return 0.2  # Different historical era
    
    def calculate_author_relation(self, book: Dict[str, Any], input_books: List[Dict[str, Any]]) -> float:
        """Calculate similarity based on author relationships"""
        # Extract author info
        book_author = None
        if book.get('author_name'):
            book_author = book['author_name'][0] if isinstance(book['author_name'], list) else book['author_name']
            
        if not book_author:
            return 0.0
            
        # Check for exact author match - strong signal
        for input_book in input_books:
            input_author = None
            if input_book.get('author_name'):
                input_author = input_book['author_name'][0] if isinstance(input_book['author_name'], list) else input_book['author_name']
                
            if input_author and input_author.lower() == book_author.lower():
                return 1.0  # Same author
        
        # Check for partial author name match (e.g., last name)
        book_author_parts = re.split(r'[\s,]+', book_author.lower())
        for input_book in input_books:
            input_author = None
            if input_book.get('author_name'):
                input_author = input_book['author_name'][0] if isinstance(input_book['author_name'], list) else input_book['author_name']
                
            if input_author:
                input_author_parts = re.split(r'[\s,]+', input_author.lower())
                # Check for last name match
                if book_author_parts and input_author_parts and book_author_parts[-1] == input_author_parts[-1]:
                    return 0.5  # Same last name
        
        # Default modest score - could be improved with more data
        return 0.1
    
    def calculate_popularity(self, book: Dict[str, Any]) -> float:
        """Calculate normalized popularity score"""
        # Use editions count or other metrics if available
        popularity_signals = [
            book.get('edition_count', 0),
            len(book.get('publisher', [])) if isinstance(book.get('publisher', []), list) else 0,
            book.get('number_of_pages_median', 0) > 0  # Boolean value based on whether page count exists
        ]
        
        # Simple score based on available signals
        score = sum(1 for signal in popularity_signals if signal > 0) / len(popularity_signals)
        
        return score
    
    def calculate_enhanced_similarity(self, book: Dict[str, Any], input_books: List[Dict[str, Any]]) -> Tuple[float, Dict[str, float]]:
        """Calculate enhanced similarity score between candidate book and input books"""
        # Calculate individual feature scores
        scores = {}
        
        # Subject match score
        book_subjects = book.get('subjects', [])
        all_input_subjects = []
        for input_book in input_books:
            if 'subjects' in input_book and isinstance(input_book['subjects'], list):
                all_input_subjects.extend(input_book['subjects'])
                
        scores['subject_match'] = self.calculate_subject_match(book_subjects, all_input_subjects)
        
        # Subject depth score
        scores['subject_depth'] = self.calculate_subject_depth(book_subjects, all_input_subjects)
        
        # Year relevance
        book_year = self.extract_year(book.get('first_publish_date', ''))
        input_years = []
        for input_book in input_books:
            year = self.extract_year(input_book.get('first_publish_date', ''))
            if year:
                input_years.append(year)
                
        scores['year_relevance'] = self.calculate_year_relevance(book_year, input_years)
        
        # Author relation
        scores['author_relation'] = self.calculate_author_relation(book, input_books)
        
        # Popularity score
        scores['popularity'] = self.calculate_popularity(book)
        
        # Combine scores using weights
        final_score = 0
        for feature, score in scores.items():
            if feature in self.weights:
                final_score += score * self.weights[feature]
                
        return final_score, scores
    
    def generate_detailed_explanation(self, book: Dict[str, Any], input_books: List[Dict[str, Any]], 
                                     score: float, component_scores: Dict[str, float]) -> str:
        """Generate detailed explanation of why this book was recommended"""
        reasons = []
        
        # Subject match explanation
        if component_scores.get('subject_match', 0) > 0.6:
            # Find the most notable shared subjects
            book_subjects = book.get('subjects', [])
            all_input_subjects = []
            for input_book in input_books:
                if isinstance(input_book.get('subjects', []), list):
                    all_input_subjects.extend(input_book['subjects'])
                    
            # Get shared subjects
            book_set = set([s.lower() for s in book_subjects if s])
            input_set = set([s.lower() for s in all_input_subjects if s])
            shared = book_set.intersection(input_set)
            
            if shared:
                examples = list(shared)[:3]
                reasons.append(f"it shares genres you enjoy like {', '.join(examples)}")
        
        # Year relevance explanation
        if component_scores.get('year_relevance', 0) > 0.7:
            book_year = self.extract_year(book.get('first_publish_date', ''))
            reasons.append(f"it's from the same era ({book_year})")
        elif component_scores.get('year_relevance', 0) > 0.5:
            reasons.append("it's from a similar time period")
        
        # Author relation explanation
        if component_scores.get('author_relation', 0) > 0.9:
            book_author = book.get('author_name', [''])[0] if isinstance(book.get('author_name', []), list) else book.get('author_name', '')
            reasons.append(f"it's by an author you've enjoyed ({book_author})")
        elif component_scores.get('author_relation', 0) > 0.4:
            reasons.append("it's by an author similar to ones you've read")
        
        # Subject depth explanation
        if component_scores.get('subject_depth', 0) > 0.6 and component_scores.get('subject_match', 0) > 0.4:
            reasons.append("it has themes that closely match your reading preferences")
        
        # Popularity explanation (only if it's a major factor)
        if component_scores.get('popularity', 0) > 0.7 and len(reasons) < 3:
            reasons.append("it's a notable work in its genre")
        
        # Create the explanation
        if reasons:
            explanation = f"This book has a {round(score)}% match to your preferences because {' and '.join(reasons)}."
        else:
            explanation = f"This book has a {round(score)}% match to your reading preferences based on multiple factors."
        
        return explanation

class BookRecommender:
    def __init__(self):
        self.rate_limiter = RateLimiter(14400, 20000)
        try:
            self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            print("Successfully initialized Groq client")
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            self.groq_client = None

        try:
            self.lightweight_recommender = LightweightBookRecommender()
            print("Successfully initialized Lightweight Book Recommender")
            self.use_enhanced_algorithm = True
        except Exception as e:
            print(f"Warning: Could not initialize Lightweight Book Recommender: {e}")
            print("Falling back to basic similarity algorithm")
            self.use_enhanced_algorithm = False

    def extract_year(self, date_str: str) -> Optional[int]:
        if not date_str:
            return None
        try:
            return int(str(date_str)[:4])
        except (ValueError, TypeError):
            import re
            year_match = re.search(r'\d{4}', str(date_str).strip())
            if year_match:
                return int(year_match.group())
            return None

    def get_book_details(self, book_id: str) -> Dict[str, Any]:
        try:
            print(f"Fetching details for book ID: {book_id}")
            for attempt in range(MAX_RETRIES):
                try:
                    work_response = requests.get(
                        f"{OPEN_LIBRARY_WORKS}{book_id}.json",
                        timeout=OPENLIB_TIMEOUT                        
                    )
                    if not work_response.ok:
                        print(f"Failed to fetch book details: {work_response.status_code}")
                        print(f"Response content: {work_response.text}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(2 ** attempt)
                            continue
                        return None

                    work_data = work_response.json()
                    return work_data

                except requests.exceptions.Timeout:
                    print(f"Timeout on attempt {attempt + 1}")
                    if attempt == MAX_RETRIES - 1:
                        return None
                    time.sleep(2 ** attempt)
                except Exception as e:
                    print(f"Error on attempt {attempt + 1}: {str(e)}")
                    if attempt == MAX_RETRIES - 1:
                        return None
                    time.sleep(2 ** attempt)

            return None
        except Exception as e:
            print(f"Error fetching book details: {str(e)}")
            return None

    def calculate_similarity_score(self, candidate_book: Dict, input_books: List[Dict]) -> float:
        """Calculate similarity score between candidate book and input books"""
        # Use lightweight algorithm if available
        if hasattr(self, 'use_enhanced_algorithm') and self.use_enhanced_algorithm:
            try:
                score, component_scores = self.lightweight_recommender.calculate_enhanced_similarity(
                    candidate_book, input_books
                )
                
                # Store component scores for later explanation generation
                candidate_book['component_scores'] = component_scores
                
                return score
            except Exception as e:
                print(f"Error using lightweight algorithm: {str(e)}")
                print("Falling back to basic similarity algorithm")
                # Fall back to basic algorithm on error
        
        # Basic algorithm (your original implementation)
        weights = {
            'subject_match': 0.8,
            'year_match': 0.2
        }
    
        input_subjects = set()
        for b in input_books:
            if 'subjects' in b and isinstance(b['subjects'], list):
                input_subjects.update(b['subjects'])
    
        candidate_subjects = set()
        if 'subjects' in candidate_book and isinstance(candidate_book['subjects'], list):
            candidate_subjects.update(candidate_book['subjects'])
    
        subject_similarity = len(input_subjects & candidate_subjects) / max(len(input_subjects | candidate_subjects), 1)
    
        candidate_year = self.extract_year(candidate_book.get('first_publish_date', ''))
        input_years = []
        for ib in input_books:
            year = self.extract_year(ib.get('first_publish_date', ''))
            if year:
                input_years.append(year)
    
        if input_years and candidate_year:
            avg_year = sum(input_years) / len(input_years)
            year_similarity = 1 / (1 + abs(candidate_year - avg_year) / 100)
        else:
            year_similarity = 0
    
        score = (
            weights['subject_match'] * subject_similarity +
            weights['year_match'] * year_similarity
        )
        return score

    def generate_explanation(self, book: Dict, input_books: List[Dict], similarity_score: float) -> str:
        """Generate explanation of why this book was recommended"""
        # Use enhanced explanation if component scores are available
        if 'component_scores' in book and hasattr(self, 'use_enhanced_algorithm') and self.use_enhanced_algorithm:
            try:
                explanation = self.lightweight_recommender.generate_detailed_explanation(
                    book, input_books, similarity_score * 100, book['component_scores']
                )
                return explanation
            except Exception as e:
                print(f"Error generating enhanced explanation: {str(e)}")
                # Fall back to basic explanation on error
        
        # Basic explanation (your original implementation)
        explanations = []
    
        book_subjects = set(book.get('subjects', []) if isinstance(book.get('subjects', []), list) else [])
        input_subjects = set()
        for input_book in input_books:
            if isinstance(input_book.get('subjects', []), list):
                input_subjects.update(input_book.get('subjects', []))
    
        shared_subjects = book_subjects & input_subjects
        if shared_subjects:
            subject_examples = list(shared_subjects)[:3]
            explanations.append(f"shares genres like {', '.join(subject_examples)}")
    
        book_year = self.extract_year(book.get('first_publish_date', ''))
        input_years = []
        for input_book in input_books:
            year = self.extract_year(input_book.get('first_publish_date', ''))
            if year:
                input_years.append(year)
    
        if input_years and book_year:
            avg_year = sum(input_years) / len(input_years)
            year_diff = abs(book_year - avg_year)
            if year_diff <= 20:
                explanations.append("was published around the same time")
            elif year_diff <= 50:
                explanations.append("was published in a similar era")
    
        if explanations:
            explanation = f"This book was recommended because it {' and '.join(explanations)}, with a {similarity_score:.1f}% match to your preferences."
        else:
            explanation = "This book matches your reading preferences."
    
        return explanation

    def generate_reading_recommendation(self, book: Dict, input_books: List[Dict]) -> str:
        parts = []
        subjects = book.get('subjects', [])
        main_genres = subjects[:3] if subjects else []
        themes = subjects[3:6] if len(subjects) > 3 else []

        if main_genres:
            primary_genre = main_genres[0].lower()
            parts.append(f"A notable work in the {primary_genre} genre")

        if themes:
            theme_desc = f"explores themes of {', '.join(themes).lower()}"
            parts.append(theme_desc)

        if book.get('first_publish_date'):
            try:
                year = int(book.get('first_publish_date')[:4])
                if year < 1900:
                    parts.append("represents a significant historical perspective")
                elif year < 1950:
                    parts.append("offers insights into mid-century literary development")
                elif year > 2010:
                    parts.append("presents contemporary narrative techniques")
            except (ValueError, TypeError):
                pass

        if not parts:
            return "A noteworthy addition to its genre, offering readers a distinctive literary perspective."

        recommendation = ' and '.join(parts) + '.'
        return recommendation

    def call_groq_api(self, prompt: str, max_tokens: int = 512) -> Optional[str]:
        try:
            if not self.groq_client:
                print("Groq client not initialized")
                return None

            estimated_tokens = len(prompt.split()) + max_tokens

            if not self.can_make_request(estimated_tokens):
                print("Rate limit reached, falling back to basic generation")
                return None

            max_retries = 5
            for attempt in range(max_retries):
                try:
                    print(f"Making Groq API call, attempt {attempt + 1}")
                    start_time = time.time()

                    # Set a longer timeout for the API call
                    chat_completion = self.groq_client.chat.completions.create(
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }],
                        model="groq/compound",
                        temperature=0.7,
                        max_tokens=max_tokens,
                        timeout=GROQ_TIMEOUT  # 150 second timeout
                    )

                    response_time = time.time() - start_time
                    print(f"Groq API response received in {response_time:.2f} seconds")

                    if chat_completion.choices and chat_completion.choices[0].message.content:
                        content = chat_completion.choices[0].message.content.strip()
                        if len(content) > 10:  # Ensure we have meaningful content
                            return content
                        else:
                            raise Exception("Response too short")

                except Exception as e:
                    print(f"Groq API attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        sleep_time = 10 * (2 ** attempt)  # Longer wait between retries
                        print(f"Waiting {sleep_time} seconds before retry")
                        time.sleep(sleep_time)
                    else:
                        print("All retries failed")
                        return None

            return None

        except Exception as e:
            print(f"Unexpected error in call_groq_api: {str(e)}")
            return None

    def can_make_request(self, estimated_tokens: int) -> bool:
        return self.rate_limiter.can_make_request(estimated_tokens)

    def generate_similarity_explanation_with_ai(self, book: Dict, input_books: List[Dict], similarity_score: float) -> str:
        shared_subjects = set(book.get('subjects', [])) & set(sum([b.get('subjects', []) for b in input_books], []))

        book_year = self.extract_year(book.get('first_publish_date', ''))
        input_years = []
        for input_book in input_books:
            year = self.extract_year(input_book.get('first_publish_date', ''))
            if year:
                input_years.append(year)

        avg_year = sum(input_years) / len(input_years) if input_years else None

        prompt = f"""Analyze why this book matches the reader's preferences:
        Book Details:
        Title: {book.get('title', '')}
        Author: {book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown'}
        Year: {book_year if book_year else 'Unknown'}
        Shared Genres: {', '.join(list(shared_subjects)[:3])}
        Similarity Score: {similarity_score:.1f}%
        Reader's Preferences:
        - Favorite Genres: {', '.join(list(set(sum([b.get('subjects', [])[:3] for b in input_books], []))))}
        - Preferred Era: Around {int(avg_year) if avg_year else 'Unknown'}
        Explain why this book would appeal to the reader based on these matches. Use 2nd person like you and your. Please don't mention the date. Focus on specific connections and shared elements. Keep it concise (4-5 sentences) and analytical."""

        response = self.call_groq_api(prompt, max_tokens=256)
        if response:
            return response.strip()
        return self.generate_explanation(book, input_books, similarity_score)

    def generate_reading_recommendation_with_ai(self, book: Dict, input_books: List[Dict]) -> str:
        prompt = f"""Create a detailed and compelling recommendation for why someone should read this book:
        Title: {book.get('title', '')}
        Author: {book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown'}
        Year: {book.get('first_publish_date', 'Unknown')}
        Genres: {', '.join(book.get('subjects', [])[:5]) if book.get('subjects') else 'Unknown'}
        Create an engaging recommendation that covers:
        1. The unique aspects and standout features of this book
        2. The emotional journey and reading experience it offers
        3. The book's cultural or literary significance
        4. Who would particularly enjoy or benefit from reading it
        5. What lasting impact or insights readers can expect to gain
        Write in an enthusiastic, persuasive tone that makes readers excited to start the book.
        Use 2nd person like you and your. Do not mention the date.
        Provide specific details and compelling reasons.
        Aim for 4-6 sentences that paint a vivid picture of the reading experience."""

        response = self.call_groq_api(prompt)
        if response:
            return response.strip()
        return self.generate_reading_recommendation(book, input_books)

recommender = BookRecommender()

@app.route('/api/recommend', methods=['POST', 'OPTIONS'])  
def get_recommendations():
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'https://lemon-water-065707a1e.4.azurestaticapps.net')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response
    try:
        print("Received recommendation request")
        data = request.json
        book_titles = data.get('books', [])
        filters = data.get('filters', {})
        
        # Add pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 2))
        
        print(f"\n--- Starting recommendation process for books: {book_titles} (page {page}, per_page {per_page}) ---")

        if not book_titles:
            return jsonify({'error': 'No books provided'}), 400

        input_books = []
        input_book_ids = set()
        input_authors = set()

        try:
            # Process input books (unchanged)
            for title in book_titles:
                print(f"Processing book: {title}")
                response = requests.get(
                    OPEN_LIBRARY_SEARCH,
                    params={'q': title, 'fields': 'key,title,author_name,first_publish_year,subject,cover_i', 'limit': 1},
                    timeout=OPENLIB_TIMEOUT
                )

                if not response.ok:
                    print(f"OpenLibrary API error for {title}: {response.status_code}")
                    print(f"Response content: {response.text}")
                    continue

                if response.json().get('docs'):
                    book = response.json()['docs'][0]
                    book_id = book.get('key', '').split('/')[-1]
                    input_book_ids.add(book_id)
                    if book.get('author_name'):
                        input_authors.add(book.get('author_name')[0])
                    book_details = recommender.get_book_details(book_id)
                    if book_details:
                        input_books.append(book_details)
                    else:
                        print(f"Could not get details for book: {title}")

            if not input_books:
                return jsonify({'error': 'Could not process any of the input books'}), 400

            print(f"Successfully processed {len(input_books)} books")

            # Analyze subjects (unchanged)
            all_subjects = []
            for book in input_books:
                subjects = book.get('subjects', [])
                all_subjects.extend(subjects)

            common_subjects = Counter(all_subjects).most_common(10)
            seen_books = set()
            recommendations = []

            # Find recommendations (unchanged)
            for (subject, _) in common_subjects:
                response = requests.get(
                    OPEN_LIBRARY_SEARCH,
                    params={
                        'q': f'subject:{subject}',
                        'fields': 'key,title,author_name,first_publish_year,subject,cover_i',
                        'limit': 20
                    }
                )

                if response.ok:
                    for b in response.json().get('docs', []):
                        book_id = b.get('key', '').split('/')[-1]
                        author = b.get('author_name', ['Unknown'])[0] if b.get('author_name') else 'Unknown'

                        if book_id not in input_book_ids and book_id not in seen_books and author not in input_authors:
                            book_details = recommender.get_book_details(book_id)
                            if book_details:
                                similarity_score = recommender.calculate_similarity_score(book_details, input_books)
                                explanation = recommender.generate_explanation(book_details, input_books, similarity_score * 100)
                                basic_reading_rec = recommender.generate_reading_recommendation(book_details, input_books)

                                cover_id = b.get('cover_i')

                                recommendation = {
                                    'id': book_id,
                                    'title': b.get('title', ''),
                                    'author': author,
                                    'year': b.get('first_publish_year'),
                                    'genres': b.get('subject', [])[:5] if b.get('subject') else [],
                                    'similarity_score': round(similarity_score * 100, 1),
                                    'explanation': explanation,
                                    'why_read': basic_reading_rec,
                                    'cover_url': f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None,
                                }

                                recommendations.append(recommendation)
                                seen_books.add(book_id)

            # Filter and sort all recommendations
            filtered_recommendations = apply_filters(recommendations, filters)
            all_recommendations = sorted(
                filtered_recommendations,
                key=lambda x: x['similarity_score'],
                reverse=True
            )
            
            # Apply pagination
            total_recommendations = len(all_recommendations)
            start_idx = (page - 1) * per_page
            end_idx = min(start_idx + per_page, total_recommendations)
            
            if start_idx >= total_recommendations:
                return jsonify({
                    'status': 'completed',
                    'recommendations': [],
                    'pagination': {
                        'current_page': page,
                        'per_page': per_page,
                        'total_items': total_recommendations,
                        'total_pages': math.ceil(total_recommendations / per_page) or 1
                    }
                })
            
            paged_recommendations = all_recommendations[start_idx:end_idx]

            # Enhance recommendations (only for the current page)
            for recommendation in paged_recommendations:
                try:
                    book_id = recommendation['id']
                    book_details = recommender.get_book_details(book_id)
                    if book_details:
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                print(f"Attempt {attempt + 1} for AI content generation for {book_id}")

                                # Generate explanation first
                                new_explanation = recommender.generate_similarity_explanation_with_ai(
                                    book_details, input_books, recommendation['similarity_score']
                                )
                                if new_explanation and len(new_explanation.strip()) > 10:
                                    recommendation['explanation'] = new_explanation
                                    print(f"Successfully generated explanation: {len(new_explanation)} chars")

                                # Add a small delay between API calls
                                time.sleep(1)

                                # Then generate why_read
                                why_read = recommender.generate_reading_recommendation_with_ai(book_details, input_books)
                                if why_read and len(why_read.strip()) > 10:
                                    recommendation['why_read'] = why_read
                                    print(f"Successfully generated why_read: {len(why_read)} chars")
                                    break  # Break only if both generations are successful

                                if not why_read or not new_explanation:
                                    raise Exception("Empty AI response")

                            except Exception as retry_e:
                                print(f"Retry {attempt + 1} failed: {str(retry_e)}")
                                if attempt == max_retries - 1:
                                    # On final retry failure, ensure we have fallback content
                                    if not recommendation.get('explanation'):
                                        recommendation['explanation'] = recommender.generate_explanation(
                                            book_details, input_books, recommendation['similarity_score']
                                        )
                                    if not recommendation.get('why_read'):
                                        recommendation['why_read'] = recommender.generate_reading_recommendation(
                                            book_details, input_books
                                        )
                                    break
                                time.sleep(2 ** attempt)  # Exponential backoff
                except Exception as e:
                    print(f"Error enhancing recommendation: {str(e)}")
                    # Ensure fallback content is present
                    if not recommendation.get('explanation'):
                        recommendation['explanation'] = recommender.generate_explanation(
                            book_details, input_books, recommendation['similarity_score']
                        )
                    if not recommendation.get('why_read'):
                        recommendation['why_read'] = recommender.generate_reading_recommendation(
                            book_details, input_books
                        )

            # Return final JSON response with pagination metadata
            return jsonify({
                'status': 'completed',
                'recommendations': paged_recommendations,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_items': total_recommendations,
                    'total_pages': math.ceil(total_recommendations / per_page) or 1
                }
            })

        except Exception as inner_e:
            print(f"Error in book processing: {str(inner_e)}")
            return jsonify({'error': f'Error processing books: {str(inner_e)}'}), 500

    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return jsonify({'error': str(e)}), 500
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
