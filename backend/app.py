from flask import Flask, request, jsonify
import requests
import json
import time
import math
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from datetime import datetime, timedelta
import os
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from dotenv import load_dotenv
from groq import Groq
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://lemon-water-065707a1e.4.azurestaticapps.net"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True,
        "max_age": 600
    }
})

# --------------------------------------------------------------------------------
#                               Configuration
# --------------------------------------------------------------------------------
OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"        # Book Search API
OPEN_LIBRARY_WORKS = "https://openlibrary.org/works/"              # Work API
OPEN_LIBRARY_EDITIONS = "https://openlibrary.org/books/"           # Edition API (e.g. /books/OL1M.json)
OPEN_LIBRARY_AUTHORS = "https://openlibrary.org/authors/"          # Authors API
OPEN_LIBRARY_SUBJECTS = "https://openlibrary.org/subjects/"        # Subjects API
OPEN_LIBRARY_COVERS = "https://covers.openlibrary.org"             # Covers API
OPEN_LIBRARY_RECENT_CHANGES = "https://openlibrary.org/recentchanges"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Timeout settings
OPENLIB_TIMEOUT = 10        # Reduced from 1000 to 10 (seconds) to fail faster
REQUEST_TIMEOUT = 10        # Also reduce to 10 seconds
OVERALL_TIMEOUT = 540       # Overall limit (still 9 minutes, but we’ll try to finish well before that)

# Request limits
MAX_RETRIES = 2
# --------------------------------------------------------------------------------
# ! Lower concurrency from 3 to 1 to reduce parallel overhead
# --------------------------------------------------------------------------------
CONCURRENT_REQUESTS = 1
MAX_BOOKS_PER_REQUEST = 5
MAX_RECOMMENDATIONS_PER_SUBJECT = 10

# Processing settings
BATCH_SIZE = 5
MIN_SIMILARITY_SCORE = 5

HEADERS = {
    "User-Agent": "ReadNext/1.0 (oungs@oregonstate.edu)"
}

# --------------------------------------------------------------------------------
#                               RateLimiter + Cache
# --------------------------------------------------------------------------------

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
            # reset daily count if 24h passed
            if current_time - self.last_reset > timedelta(days=1):
                self.daily_requests = 0
                self.last_reset = current_time
            # reset minute count if 1 minute passed
            if current_time - self.minute_reset > timedelta(minutes=1):
                self.minute_tokens = 0
                self.minute_reset = current_time

            if (self.daily_requests < self.daily_limit and
                    self.minute_tokens + estimated_tokens <= self.minute_limit):
                self.daily_requests += 1
                self.minute_tokens += estimated_tokens
                return True
            return False

class Cache:
    def __init__(self, expiry_seconds: int):
        self.cache = {}
        self.expiry = expiry_seconds
        self.lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                item = self.cache[key]
                if datetime.now() - item['timestamp'] < timedelta(seconds=self.expiry):
                    return item['data']
                del self.cache[key]
            return None

    def set(self, key: str, value: Any):
        with self.lock:
            self.cache[key] = {
                'data': value,
                'timestamp': datetime.now()
            }

# --------------------------------------------------------------------------------
#                              Utility Functions
# --------------------------------------------------------------------------------

def apply_filters(recommendations: List[Dict], filters: Dict) -> List[Dict]:
    """
    Applies user-specified filters (genre, yearRange, minScore, readingLevel)
    to the recommendation list.
    """
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

        if filters.get('readingLevel'):
            if book.get('reading_level') != filters['readingLevel']:
                continue

        filtered_books.append(book)

    return filtered_books

# --------------------------------------------------------------------------------
#                       Book Recommender (Optimized)
# --------------------------------------------------------------------------------

class BookRecommender:
    def __init__(self):
        self.rate_limiter = RateLimiter(14400, 20000)
        self.cache = Cache(3600)
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        # --------------------------------------------------------------------------------
        # Lower concurrency to reduce memory/calls
        # --------------------------------------------------------------------------------
        self.executor = ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS)

        try:
            self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            print("Successfully initialized Groq client")
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            self.groq_client = None

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

    def get_book_details(self, book_id: str) -> Optional[Dict]:
        """
        Retrieve work details from the /works/ API by the given work ID.
        Caches results to avoid repeated calls.
        """
        try:
            cached_data = self.cache.get(book_id)
            if cached_data:
                return cached_data

            for attempt in range(MAX_RETRIES):
                try:
                    t0 = time.time()
                    work_response = self.session.get(
                        f"{OPEN_LIBRARY_WORKS}{book_id}.json",
                        timeout=OPENLIB_TIMEOUT
                    )
                    elapsed = time.time() - t0
                    print(f"DEBUG: get_book_details({book_id}) took {elapsed:.2f}s")

                    if work_response.ok:
                        work_data = work_response.json()
                        self.cache.set(book_id, work_data)
                        return work_data
                    elif work_response.status_code == 404:
                        print(f"Book not found: {book_id}")
                        return None
                    elif attempt < MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                        
                except requests.exceptions.Timeout:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    print(f"Timeout fetching book {book_id}")
                    return None
                except Exception as e:
                    print(f"Error fetching book {book_id}: {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(1)
                        continue
                    return None

            return None
        except Exception as e:
            print(f"Unexpected error for book {book_id}: {str(e)}")
            return None

    def calculate_similarity_score(self, candidate_book: Dict, input_books: List[Dict]) -> float:
        """
        Calculates a simple similarity score between candidate_book and input_books,
        based on subject overlap, publication year closeness, etc.
        """
        weights = {
            'subject_match': 0.5,
            'year_match': 0.25,
            'popularity_match': 0.25
        }
        
        # Subject similarity
        input_subjects = set()
        for b in input_books:
            if 'subjects' in b and isinstance(b['subjects'], list):
                for subject in b['subjects']:
                    if any(keyword in subject.lower() for keyword in ['fiction', 'non-fiction', 'mystery', 'romance', 'fantasy']):
                        input_subjects.add((subject, 1.5))
                    else:
                        input_subjects.add((subject, 1.0))

        candidate_subjects = set()
        if 'subjects' in candidate_book and isinstance(candidate_book['subjects'], list):
            for subject in candidate_book['subjects']:
                if any(keyword in subject.lower() for keyword in ['fiction', 'non-fiction', 'mystery', 'romance', 'fantasy']):
                    candidate_subjects.add((subject, 1.5))
                else:
                    candidate_subjects.add((subject, 1.0))

        weighted_matches = sum(w1 * w2 for (s1, w1) in input_subjects for (s2, w2) in candidate_subjects if s1 == s2)
        total_possible = sum(w1 * w2 for (_, w1) in input_subjects for (_, w2) in candidate_subjects)
        subject_similarity = weighted_matches / max(total_possible, 1)

        # Year similarity
        candidate_year = self.extract_year(candidate_book.get('first_publish_date', ''))
        input_years = []
        for ib in input_books:
            year = self.extract_year(ib.get('first_publish_date', ''))
            if year:
                input_years.append(year)

        if input_years and candidate_year:
            avg_year = sum(input_years) / len(input_years)
            if avg_year < 1900:
                year_similarity = 1 / (1 + abs(candidate_year - avg_year) / 150)
            else:
                year_similarity = 1 / (1 + abs(candidate_year - avg_year) / 50)
        else:
            year_similarity = 0

        # Popularity consideration
        popularity_similarity = 0
        if 'ratings_count' in candidate_book and any('ratings_count' in b for b in input_books):
            input_ratings = [b.get('ratings_count', 0) for b in input_books if 'ratings_count' in b]
            if input_ratings:
                avg_ratings = sum(input_ratings) / len(input_ratings)
                candidate_ratings = candidate_book.get('ratings_count', 0)
                # Avoid math domain errors if rating is 0
                if candidate_ratings > 0 and avg_ratings > 0:
                    popularity_similarity = 1 / (1 + abs(math.log(candidate_ratings + 1) - math.log(avg_ratings + 1)) / 2)

        score = (
            weights['subject_match'] * subject_similarity +
            weights['year_match'] * year_similarity +
            weights['popularity_match'] * popularity_similarity
        )
        
        # Slight bonus if average_rating > 4.0
        if candidate_book.get('average_rating', 0) > 4.0:
            score *= 1.1

        return min(score, 1.0)

    def determine_reading_level(self, book: Dict) -> str:
        subjects = set(s.lower() for s in book.get('subjects', []))
        if any(term in subjects for term in ['young adult', 'ya', 'teen']):
            return 'Young Adult'
        elif any(term in subjects for term in ['children', 'juvenile', 'middle grade']):
            return 'Children'
        elif any(term in subjects for term in ['academic', 'scholarly', 'technical']):
            return 'Academic'
        return 'Adult'

    def analyze_narrative_style(self, book: Dict) -> str:
        subjects = set(s.lower() for s in book.get('subjects', []))
        if any(term in subjects for term in ['literary fiction', 'literary']):
            return 'Literary'
        elif any(term in subjects for term in ['experimental', 'postmodern']):
            return 'Experimental'
        elif any(term in subjects for term in ['commercial fiction', 'genre fiction']):
            return 'Commercial'
        return 'General'

    def call_groq_api(self, prompt: str, max_tokens: int = 256) -> Optional[str]:
        if not self.groq_client:
            return None

        estimated_tokens = len(prompt.split()) + max_tokens
        if not self.rate_limiter.can_make_request(estimated_tokens):
            return None

        for attempt in range(MAX_RETRIES):
            try:
                t0 = time.time()
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama3-8b-8192",
                    temperature=0.7,
                    max_tokens=max_tokens,
                    timeout=OPENLIB_TIMEOUT
                )
                elapsed = time.time() - t0
                print(f"DEBUG: call_groq_api took {elapsed:.2f}s")

                if chat_completion.choices and chat_completion.choices[0].message.content:
                    content = chat_completion.choices[0].message.content.strip()
                    if len(content) > 10:
                        return content

            except Exception as e:
                print(f"Groq API attempt {attempt + 1} failed: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)

        return None

    def generate_similarity_explanation_with_ai(self, book: Dict, input_books: List[Dict], similarity_score: float) -> str:
        reading_level = self.determine_reading_level(book)
        narrative_style = self.analyze_narrative_style(book)
        shared_subjects = set(book.get('subjects', [])) & set(sum([b.get('subjects', []) for b in input_books], []))

        prompt = f"""Analyze why this book matches the reader's preferences:

        Book Details:
        Title: {book.get('title', '')}
        Author: {book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown'}
        Reading Level: {reading_level}
        Narrative Style: {narrative_style}
        Shared Genres: {', '.join(list(shared_subjects)[:3])}
        Rating: {book.get('average_rating', 'Unknown')}
        Similarity Score: {similarity_score:.1f}%

        Reader's Previous Books:
        - Genres: {', '.join(list(set(sum([b.get('subjects', [])[:3] for b in input_books], []))))}
        - Reading Levels: {', '.join(set(self.determine_reading_level(b) for b in input_books))}
        - Narrative Styles: {', '.join(set(filter(None, [self.analyze_narrative_style(b) for b in input_books])))}

        Create a personalized explanation focusing on specific connections and shared elements.
        Keep it concise (4-5 sentences) and use natural language."""

        response = self.call_groq_api(prompt, max_tokens=256)
        if response:
            return response.strip()
        else:
            return self.generate_fallback_explanation(book, input_books, similarity_score)

    def generate_fallback_explanation(self, book: Dict, input_books: List[Dict], similarity_score: float) -> str:
        reading_level = self.determine_reading_level(book)
        narrative_style = self.analyze_narrative_style(book)
        shared_subjects = set(book.get('subjects', [])) & set(sum([b.get('subjects', []) for b in input_books], []))
        
        explanation_parts = []
        
        if shared_subjects:
            shared_genres = list(shared_subjects)[:2]
            explanation_parts.append(f"matches your interest in {' and '.join(shared_genres)}")

        if input_books and reading_level == self.determine_reading_level(input_books[0]):
            explanation_parts.append(f"offers a similar reading experience at the {reading_level} level")

        book_year = self.extract_year(book.get('first_publish_date', ''))
        if book_year:
            input_years = [self.extract_year(b.get('first_publish_date', '')) for b in input_books if self.extract_year(b.get('first_publish_date', ''))]
            if input_years:
                avg_year = sum(input_years) / len(input_years)
                if abs(book_year - avg_year) <= 20:
                    explanation_parts.append("was published in a similar time period")

        if book.get('average_rating', 0) > 4.0:
            explanation_parts.append("has received excellent reader reviews")

        if explanation_parts:
            explanation = f"This book {', '.join(explanation_parts)}"
            if similarity_score > 0:
                explanation += f", with a {similarity_score:.1f}% match to your preferences"
            return explanation + "."
        
        return f"This book has a {similarity_score:.1f}% match with your reading preferences."

    def process_input_books(self, book_titles: List[str]) -> Tuple[List[Dict], set, set]:
        """
        1) Search for each title using /search.json
        2) Take the first doc
        3) Extract the 'key' -> /works/<ID>
        4) Get the work details
        """
        input_books = []
        input_book_ids = set()
        input_authors = set()

        def process_single_book(title):
            try:
                t0 = time.time()
                response = self.session.get(
                    OPEN_LIBRARY_SEARCH,
                    params={'q': title, 'fields': 'key,title,author_name,first_publish_year,subject,cover_i', 'limit': 1},
                    timeout=OPENLIB_TIMEOUT
                )
                elapsed = time.time() - t0
                print(f"DEBUG: Searching book '{title}' took {elapsed:.2f}s")
                
                if not response.ok:
                    print(f"Search failed for {title}: {response.status_code}")
                    return None

                docs = response.json().get('docs', [])
                if not docs:
                    print(f"No results found for {title}")
                    return None

                book = docs[0]
                book_id = book.get('key', '').split('/')[-1]  # e.g. "OL1234M"
                author = book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown'
                
                # Next, fetch that "work" or "edition" details
                book_details = self.get_book_details(book_id)
                if book_details:
                    return {
                        'book_details': book_details,
                        'book_id': book_id,
                        'author': author
                    }
                return None

            except Exception as e:
                print(f"Error processing book {title}: {str(e)}")
                return None

        futures = []
        with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
            for title in book_titles:
                futures.append(executor.submit(process_single_book, title))
            
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=REQUEST_TIMEOUT)
                    if result:
                        input_books.append(result['book_details'])
                        input_book_ids.add(result['book_id'])
                        input_authors.add(result['author'])
                except TimeoutError:
                    print("Book processing timed out")
                    continue
                except Exception as e:
                    print(f"Error processing book: {str(e)}")
                    continue

        return input_books, input_book_ids, input_authors

# --------------------------------------------------------------------------------
#                          Initialize Recommender
# --------------------------------------------------------------------------------
recommender = BookRecommender()

@app.route('/')
def home():
    return "Book Recommendation API is running!"

@app.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({"message": "hello"})

# --------------------------------------------------------------------------------
#                 Existing Recommendation Endpoint (Optimized)
# --------------------------------------------------------------------------------

@app.route('/api/recommend', methods=['POST', 'OPTIONS'])
def get_recommendations():
    """
    Main recommendation endpoint:
      1. Limit to 5 user-specified books.
      2. Process input, gather subjects.
      3. Attempt 2 passes with different thresholds (30, then 15).
      4. Return up to 2 final recommendations.
    """
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', 'https://lemon-water-065707a1e.4.azurestaticapps.net')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
        return response

    try:
        data = request.json
        if not data or not data.get('books'):
            return jsonify({'error': 'No books provided'}), 400

        book_titles = data['books'][:5]
        filters = data.get('filters', {})
        print(f"Processing recommendation request for books: {book_titles}")

        # Start timing
        start_time = time.time()

        try:
            input_books, input_book_ids, input_authors = recommender.process_input_books(book_titles)
        except Exception as e:
            print(f"Error processing input books: {str(e)}")
            return jsonify({'error': 'Failed to process input books. Please try again.'}), 500

        if not input_books:
            return jsonify({'error': 'Could not find any of the specified books. Please check the titles and try again.'}), 400

        # Analyze subjects with broader matching
        all_subjects = []
        for book in input_books:
            subjects = book.get('subjects', [])
            if isinstance(subjects, list):
                all_subjects.extend(subjects)
            
            # Add broader genre categories
            genres = set()
            for subject in subjects:
                s_lower = subject.lower()
                if 'fiction' in s_lower:
                    genres.add('Fiction')
                elif 'non-fiction' in s_lower or 'nonfiction' in s_lower:
                    genres.add('Non-Fiction')
                for g in ['Mystery', 'Science Fiction', 'Fantasy', 'Romance', 'Thriller', 'Horror']:
                    if g.lower() in s_lower:
                        genres.add(g)
            all_subjects.extend(list(genres))

        # Count frequency, top 15
        common_subjects = Counter(all_subjects).most_common(15)
        recommendations = []
        seen_books = set()
        searched_subjects = []
        found_any_matches = False

        # We'll do 2 attempts with thresholds: 30 first, then 15
        for attempt in range(2):
            # Lower threshold on second attempt
            min_similarity = 30 if attempt == 0 else 15

            for subject, _ in common_subjects:
                searched_subjects.append(subject)
                try:
                    # Only 2 queries (quoted and unquoted)
                    search_queries = [
                        f'subject:"{subject}"',
                        subject
                    ]
                    
                    for query in search_queries:
                        # --------------------------------------------------------------------------------
                        # reduce 'limit' to 5 to minimize overhead
                        # --------------------------------------------------------------------------------
                        t0 = time.time()
                        response = requests.get(
                            OPEN_LIBRARY_SEARCH,
                            params={
                                'q': query,
                                'fields': 'key,title,author_name,first_publish_year,subject,cover_i',
                                'limit': 5
                            },
                            timeout=OPENLIB_TIMEOUT
                        )
                        elapsed = time.time() - t0
                        print(f"DEBUG: Searching subject '{subject}', query '{query}' took {elapsed:.2f}s")

                        if response.ok:
                            for book in response.json().get('docs', []):
                                book_id = book.get('key', '').split('/')[-1]
                                author = book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown'

                                if (book_id not in input_book_ids and 
                                    book_id not in seen_books and 
                                    author not in input_authors):
                                    
                                    book_details = recommender.get_book_details(book_id)
                                    if book_details:
                                        similarity_score = recommender.calculate_similarity_score(book_details, input_books)
                                        if similarity_score * 100 >= min_similarity:
                                            found_any_matches = True
                                            reading_level = recommender.determine_reading_level(book_details)
                                            narrative_style = recommender.analyze_narrative_style(book_details)
                                            
                                            try:
                                                explanation = recommender.generate_similarity_explanation_with_ai(
                                                    book_details, input_books, similarity_score * 100
                                                )
                                            except Exception:
                                                explanation = recommender.generate_fallback_explanation(
                                                    book_details, input_books, similarity_score * 100
                                                )

                                            recommendation = {
                                                'id': book_id,
                                                'title': book.get('title', ''),
                                                'author': author,
                                                'year': book.get('first_publish_year'),
                                                'genres': book.get('subject', [])[:5] if book.get('subject') else [],
                                                'similarity_score': round(similarity_score * 100, 1),
                                                'reading_level': reading_level,
                                                'narrative_style': narrative_style,
                                                'explanation': explanation,
                                                'cover_url': (f"https://covers.openlibrary.org/b/id/{book.get('cover_i')}-L.jpg"
                                                              if book.get('cover_i') else None),
                                            }
                                            recommendations.append(recommendation)
                                            seen_books.add(book_id)

                                # Short-circuit if we already have 2 or more recs from this subject
                                if len(recommendations) >= MAX_RECOMMENDATIONS_PER_SUBJECT:
                                    break

                        # If we already got enough recommendations overall
                        if len(recommendations) >= MAX_RECOMMENDATIONS_PER_SUBJECT:
                            break

                except Exception as e:
                    print(f"Error processing subject '{subject}': {str(e)}")
                    continue

                # If we have a decent amount, let's break out
                if len(recommendations) >= 10:
                    break
            
            # If we found anything after the first pass, don't do second
            if recommendations:
                break

        if not recommendations:
            error_message = "We couldn't find matching recommendations. "
            if searched_subjects:
                error_message += f"We searched in these categories: {', '.join(searched_subjects[:5])}"
            if not found_any_matches:
                error_message += ". Try books with more common genres or more recent publications."
            return jsonify({'error': error_message}), 404

        # Filter and sort recommendations
        filtered_recommendations = apply_filters(recommendations, filters)
        final_recommendations = sorted(
            filtered_recommendations,
            key=lambda x: x['similarity_score'],
            reverse=True
        )[:2]

        if not final_recommendations and recommendations:
            final_recommendations = sorted(
                recommendations,
                key=lambda x: x['similarity_score'],
                reverse=True
            )[:2]

        elapsed_total = time.time() - start_time
        print(f"DEBUG: Total recommendation processing took {elapsed_total:.2f}s")

        return jsonify({
            'status': 'completed',
            'recommendations': final_recommendations
        })

    except Exception as e:
        print(f"Error generating recommendations: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

# --------------------------------------------------------------------------------
#        Additional Example Endpoints
# --------------------------------------------------------------------------------

# (unchanged stubs below)...

@app.route('/api/search_books', methods=['GET'])
def search_books():
    """
    Example: /api/search_books?q=tolkien&limit=5
    """
    query = request.args.get('q', '')
    limit = request.args.get('limit', 5, type=int)
    try:
        resp = requests.get(
            OPEN_LIBRARY_SEARCH,
            params={'q': query, 'limit': limit},
            timeout=10
        )
        if not resp.ok:
            return jsonify({"error": "Search API request failed"}), 500
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/work/<work_id>', methods=['GET'])
def get_work_details(work_id):
    try:
        resp = requests.get(f"{OPEN_LIBRARY_WORKS}{work_id}.json", timeout=10)
        if not resp.ok:
            return jsonify({"error": f"Work {work_id} not found"}), resp.status_code
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/edition/<edition_id>', methods=['GET'])
def get_edition_details(edition_id):
    try:
        resp = requests.get(f"{OPEN_LIBRARY_EDITIONS}{edition_id}.json", timeout=10)
        if not resp.ok:
            return jsonify({"error": f"Edition {edition_id} not found"}), resp.status_code
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/my_books', methods=['GET'])
def my_books_stub():
    mock_response = {
        "username": "example_user",
        "books": [
            {"key": "/books/OL100M", "title": "My Favorite Book"},
            {"key": "/books/OL200M", "title": "Another Great Book"}
        ]
    }
    return jsonify(mock_response)

@app.route('/api/author/<author_id>', methods=['GET'])
def get_author_details(author_id):
    try:
        url = f"{OPEN_LIBRARY_AUTHORS}{author_id}.json"
        resp = requests.get(url, timeout=10)
        if not resp.ok:
            return jsonify({"error": f"Author {author_id} not found"}), resp.status_code
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/subjects/<subject_name>', methods=['GET'])
def get_subject_books(subject_name):
    try:
        url = f"{OPEN_LIBRARY_SUBJECTS}{subject_name}.json"
        resp = requests.get(url, timeout=10)
        if not resp.ok:
            return jsonify({"error": f"Subject {subject_name} not found"}), resp.status_code
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search_inside', methods=['GET'])
def search_inside_stub():
    query = request.args.get('q', '')
    mock_response = {
        "query": query,
        "results": [
            {"snippet": "Here is some text mentioning your query..."},
        ]
    }
    return jsonify(mock_response)

@app.route('/api/partner', methods=['POST'])
def partner_api_stub():
    data = request.json or {}
    ids = data.get('ids', [])
    mock_response = {
        "queried_ids": ids,
        "status": "stub",
        "message": "Partner/Read API requires special usage"
    }
    return jsonify(mock_response)

@app.route('/api/covers', methods=['GET'])
def covers_api_example():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({"error": "No ISBN provided"}), 400

    cover_url = f"{OPEN_LIBRARY_COVERS}/b/isbn/{isbn}-L.jpg"
    return jsonify({"cover_url": cover_url})

@app.route('/api/recent_changes', methods=['GET'])
def recent_changes_stub():
    limit = request.args.get('limit', 10)
    try:
        resp = requests.get(f"{OPEN_LIBRARY_RECENT_CHANGES}.json?limit={limit}", timeout=10)
        if not resp.ok:
            return jsonify({"error": "Recent Changes request failed"}), resp.status_code
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/lists', methods=['GET'])
def lists_api_stub():
    username = request.args.get('username', 'someuser')
    mock_response = {
        "username": username,
        "lists": [
            {
                "name": "Fiction Favorites",
                "books": ["/books/OL123M", "/books/OL456M"]
            }
        ]
    }
    return jsonify(mock_response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Bind to 0.0.0.0 so Azure can see the port
    app.run(host='0.0.0.0', port=port)
