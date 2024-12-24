# app.py
from flask import Flask, request, jsonify
import requests
import json
import time
from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import datetime, timedelta
import os
from threading import Lock
from dotenv import load_dotenv
from groq import Groq
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
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
OPENLIB_TIMEOUT = 120  # 2 minutes
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

        if filters.get('pageCount'):
            min_pages, max_pages = filters['pageCount']
            if not book.get('page_count') or book['page_count'] < min_pages or book['page_count'] > max_pages:
                continue

        if filters.get('minScore') is not None:
            if not book.get('similarity_score') or book['similarity_score'] < filters['minScore']:
                continue

        filtered_books.append(book)

    return filtered_books

class BookRecommender:
    def __init__(self):
        self.rate_limiter = RateLimiter(14400, 20000)
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

                    edition_search = requests.get(
                        "https://openlibrary.org/search.json",
                        params={
                            'q': f'key:/works/{book_id}',
                            'fields': 'number_of_pages,key',
                            'limit': 1
                        },
                        timeout=OPENLIB_TIMEOUT
                    )

                    if edition_search.ok:
                        edition_data = edition_search.json()
                        if edition_data.get('docs'):
                            work_data['number_of_pages'] = edition_data['docs'][0].get('number_of_pages')

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

    def calculate_reading_time(self, page_count: Optional[int], genres: Optional[List[str]] = None) -> dict:
        """
        Calculate estimated reading time based on page count and book genres.
        """
        if not page_count:
            return {
                'slow': {'hours': None, 'minutes': None},
                'average': {'hours': None, 'minutes': None},
                'fast': {'hours': None, 'minutes': None}
            }

        # Words per page varies by genre and format
        base_words_per_page = 250  # standard baseline
        
        # Adjust words per page based on genre
        if genres:
            genres_lower = [g.lower() for g in genres]
            
            if any(g in genres_lower for g in ['textbook', 'academic', 'science', 'mathematics', 'technical']):
                words_per_page = base_words_per_page * 0.8
            elif any(g in genres_lower for g in ['fiction', 'novel', 'story', 'fantasy', 'mystery']):
                words_per_page = base_words_per_page * 1.2
            elif any(g in genres_lower for g in ['poetry', 'children', 'juvenile', 'picture book']):
                words_per_page = base_words_per_page * 0.5
            else:
                words_per_page = base_words_per_page
        else:
            words_per_page = base_words_per_page

        # Different reading speeds (words per minute)
        reading_speeds = {
            'slow': 150,      # Careful, detailed reading
            'average': 250,   # Average adult reading speed
            'fast': 400       # Speed reading
        }
        
        total_words = page_count * words_per_page
        
        reading_times = {}
        for speed_type, wpm in reading_speeds.items():
            total_minutes = total_words / wpm
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            
            reading_times[speed_type] = {
                'hours': hours,
                'minutes': minutes
            }
        
        return reading_times

    def calculate_similarity_score(self, candidate_book: Dict, input_books: List[Dict]) -> float:
        weights = {
            'subject_match': 0.6,
            'year_match': 0.4
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

        if book.get('number_of_pages'):
            pages = book.get('number_of_pages')
            if pages < 200:
                parts.append("provides a focused, concise narrative")
            elif pages > 500:
                parts.append("delivers an extensive literary experience")

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
                        model="llama3-8b-8192",
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
        print(f"\n--- Starting recommendation process for books: {book_titles} ---")

        if not book_titles:
            return jsonify({'error': 'No books provided'}), 400

        input_books = []
        input_book_ids = set()
        input_authors = set()

        try:
            # Process input books
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

            # Analyze subjects
            all_subjects = []
            for book in input_books:
                subjects = book.get('subjects', [])
                all_subjects.extend(subjects)

            common_subjects = Counter(all_subjects).most_common(10)
            seen_books = set()
            recommendations = []

            # Find recommendations
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
                                reading_time = recommender.calculate_reading_time(
                                    book_details.get('number_of_pages'),
                                    b.get('subject',[])
                                )

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
                                    'page_count': book_details.get('number_of_pages'),
                                    'reading_time': reading_time
                                }

                                recommendations.append(recommendation)
                                seen_books.add(book_id)

            # Filter and sort
            filtered_recommendations = apply_filters(recommendations, filters)
            final_recommendations = sorted(
                filtered_recommendations,
                key=lambda x: x['similarity_score'],
                reverse=True
            )[:2]

            for recommendation in final_recommendations:
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


            # Return final JSON response
            return jsonify({
                'status': 'completed',
                'recommendations': final_recommendations
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
