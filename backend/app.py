# app.py
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
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

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://lemon-water-065707a1e.4.azurestaticapps.net"])

OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_WORKS = "https://openlibrary.org/works/"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

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
            
            # Reset daily counter if 24 hours have passed
            if current_time - self.last_reset > timedelta(days=1):
                self.daily_requests = 0
                self.last_reset = current_time

            # Reset minute counter if 1 minute has passed
            if current_time - self.minute_reset > timedelta(minutes=1):
                self.minute_tokens = 0
                self.minute_reset = current_time

            # Check if we're within limits
            if (self.daily_requests < self.daily_limit and 
                self.minute_tokens + estimated_tokens <= self.minute_limit):
                self.daily_requests += 1
                self.minute_tokens += estimated_tokens
                return True
            return False

def apply_filters(recommendations: List[Dict], filters: Dict) -> List[Dict]:
    """Apply filters to the list of book recommendations."""
    if not filters or not recommendations:
        return recommendations

    filtered_books = []
    for book in recommendations:
        if not book:
            continue

        # Genre filter
        if filters.get('genre'):
            if not book.get('genres') or filters['genre'] not in book['genres']:
                continue

        # Year range filter
        if filters.get('yearRange'):
            min_year, max_year = filters['yearRange']
            if not book.get('year') or book['year'] < min_year or book['year'] > max_year:
                continue

        # Page count filter
        if filters.get('pageCount'):
            min_pages, max_pages = filters['pageCount']
            if not book.get('page_count') or book['page_count'] < min_pages or book['page_count'] > max_pages:
                continue

        # Similarity score filter
        if filters.get('minScore') is not None:
            if not book.get('similarity_score') or book['similarity_score'] < filters['minScore']:
                continue

        filtered_books.append(book)

    return filtered_books

class BookRecommender:
    def __init__(self):
        self.rate_limiter = RateLimiter(14400, 20000)  # Free tier limits
        try:
            self.groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            print("Successfully initialized Groq client")
        except Exception as e:
            print(f"Warning: Could not initialize Groq client: {e}")
            self.groq_client = None
    
    def extract_year(self, date_str: str) -> Optional[int]:
        """Safely extract year from various date string formats"""
        if not date_str:
            return None
            
        try:
            # Try direct integer conversion first
            return int(str(date_str)[:4])
        except (ValueError, TypeError):
            # Handle month names and other formats
            date_str = str(date_str).strip()
            
            # Look for 4-digit year pattern
            import re
            year_match = re.search(r'\d{4}', date_str)
            if year_match:
                return int(year_match.group())
                
            return None

    def get_book_details(self, book_id: str) -> Dict[str, Any]:
        """Fetch detailed book information from Open Library"""
        try:
            work_response = requests.get(f"{OPEN_LIBRARY_WORKS}{book_id}.json")
            if not work_response.ok:
                return None

            work_data = work_response.json()

            # Try to get an edition with page count
            edition_search = requests.get(
                "https://openlibrary.org/search.json",
                params={
                    'q': f'key:/works/{book_id}',
                    'fields': 'number_of_pages,key',
                    'limit': 1
                }
            )

            if edition_search.ok:
                edition_data = edition_search.json()
                if edition_data.get('docs'):
                    work_data['number_of_pages'] = edition_data['docs'][0].get('number_of_pages')

            return work_data
        except Exception as e:
            print(f"Error fetching book details: {e}")
            return None

    def calculate_reading_time(self, page_count: Optional[int]) -> dict:
        """Calculate estimated reading time based on page count"""
        if not page_count:
            return {'hours': None, 'minutes': None}

        avg_words_per_page = 250
        avg_reading_speed = 200  # words per minute

        total_minutes = (page_count * avg_words_per_page) / avg_reading_speed
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)

        return {
            'hours': hours,
            'minutes': minutes
        }

    def calculate_similarity_score(self, candidate_book: Dict, input_books: List[Dict]) -> float:
        """Calculate similarity score between a candidate book and input books"""
        weights = {
            'subject_match': 0.6,
            'year_match': 0.4
        }

        # Subject similarity
        input_subjects = set()
        for book in input_books:
            if 'subjects' in book and isinstance(book['subjects'], list):
                input_subjects.update(book['subjects'])

        candidate_subjects = set()
        if 'subjects' in candidate_book and isinstance(candidate_book['subjects'], list):
            candidate_subjects.update(candidate_book['subjects'])

        subject_similarity = len(input_subjects & candidate_subjects) / max(len(input_subjects | candidate_subjects), 1)

        # Year proximity
        candidate_year = self.extract_year(candidate_book.get('first_publish_date', ''))
        input_years = []
        
        for book in input_books:
            year = self.extract_year(book.get('first_publish_date', ''))
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
        """Generate basic explanation about similarity match"""
        explanations = []

        # Shared subjects
        book_subjects = set(book.get('subjects', []) if isinstance(book.get('subjects', []), list) else [])
        input_subjects = set()
        for input_book in input_books:
            if isinstance(input_book.get('subjects', []), list):
                input_subjects.update(input_book.get('subjects', []))

        shared_subjects = book_subjects & input_subjects
        if shared_subjects:
            subject_examples = list(shared_subjects)[:3]
            explanations.append(f"shares genres like {', '.join(subject_examples)}")

        # Year proximity using the extract_year method
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
            explanation = f"This book was recommended because it {' and '.join(explanations)}"
            explanation += f", with a {similarity_score:.1f}% match to your preferences."
        else:
            explanation = "This book matches your reading preferences."

        return explanation

    def generate_reading_recommendation(self, book: Dict, input_books: List[Dict]) -> str:
        """Generate an objective reading experience description"""
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
        """Make a rate-limited call to the Groq API"""
        if not self.groq_client:
            return None
            
        estimated_tokens = len(prompt.split()) + max_tokens
        
        if not self.rate_limiter.can_make_request(estimated_tokens):
            print("Rate limit reached, falling back to basic generation")
            return None

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=max_tokens
            )
            
            return chat_completion.choices[0].message.content

        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return None

    def generate_similarity_explanation_with_ai(self, book: Dict, input_books: List[Dict], similarity_score: float) -> str:
        """Generate a similarity explanation using Groq API"""
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

Explain why this book would appeal to the reader based on these matches. Use 2nd person like you and your.  Focus on specific connections and shared elements. Keep it concise (4-5 sentences) and analytical."""

        response = self.call_groq_api(prompt, max_tokens=256)
        if response:
            return response.strip()
        return self.generate_explanation(book, input_books, similarity_score)

    def generate_reading_recommendation_with_ai(self, book: Dict, input_books: List[Dict]) -> str:
        """Generate a recommendation using Groq API"""
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
Use 2nd person like you and your. 
Provide specific details and compelling reasons.
Aim for 4-6 sentences that paint a vivid picture of the reading experience."""

        response = self.call_groq_api(prompt)
        if response:
            return response.strip()
        return self.generate_reading_recommendation(book, input_books)

recommender = BookRecommender()

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    def generate():
        try:
            data = request.json
            book_titles = data.get('books', [])
            filters = data.get('filters', {})
            print(f"\n--- Starting recommendation process for books: {book_titles} ---")

            if not book_titles:
                yield f"data: {json.dumps({'error': 'No books provided'})}\n\n"
                return

            input_books = []
            input_book_ids = set()
            input_authors = set()

            print("\n=== Processing Input Books ===")
            for idx, title in enumerate(book_titles):
                response = requests.get(
                    OPEN_LIBRARY_SEARCH,
                    params={'q': title, 'fields': 'key,title,author_name,first_publish_year,subject,cover_i', 'limit': 1}
                )
                if response.ok and response.json().get('docs'):
                    book = response.json()['docs'][0]
                    book_id = book.get('key', '').split('/')[-1]
                    input_book_ids.add(book_id)
                    if book.get('author_name'):
                        input_authors.add(book.get('author_name')[0])
                    book_details = recommender.get_book_details(book_id)
                    if book_details:
                        input_books.append(book_details)
                        print(f"Processed input book: {book.get('title')}")

                data_dict = {
                    'status': 'processing',
                    'stage': 'input_processing',
                    'processed': idx + 1,
                    'total': len(book_titles),
                    'recommendations': []
                }
                yield f"data: {json.dumps(data_dict)}\n\n"

            all_subjects = []
            for book in input_books:
                subjects = book.get('subjects', [])
                all_subjects.extend(subjects)

            common_subjects = Counter(all_subjects).most_common(10)
            seen_books = set()
            recommendations = []

            data_dict = {
                'status': 'processing',
                'stage': 'finding_recommendations',
                'processed': 0,
                'total': len(common_subjects),
                'recommendations': []
            }

            yield f"data: {json.dumps(data_dict)}\n\n"

            for subject_idx, (subject, _) in enumerate(common_subjects):
                response = requests.get(
                    OPEN_LIBRARY_SEARCH,
                    params={
                        'q': f'subject:{subject}',
                        'fields': 'key,title,author_name,first_publish_year,subject,cover_i',
                        'limit': 20
                    }
                )

                if response.ok:
                    for book in response.json().get('docs', []):
                        book_id = book.get('key', '').split('/')[-1]
                        author = book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown'

                        if book_id not in input_book_ids and book_id not in seen_books and author not in input_authors:
                            book_details = recommender.get_book_details(book_id)
                            if book_details:
                                similarity_score = recommender.calculate_similarity_score(book_details, input_books)
                                explanation = recommender.generate_explanation(book_details, input_books, similarity_score * 100)
                                basic_reading_rec = recommender.generate_reading_recommendation(book_details, input_books)

                                cover_id = book.get('cover_i')
                                reading_time = recommender.calculate_reading_time(book_details.get('number_of_pages'))

                                recommendation = {
                                    'id': book_id,
                                    'title': book.get('title', ''),
                                    'author': author,
                                    'year': book.get('first_publish_year'),
                                    'genres': book.get('subject', [])[:5] if book.get('subject') else [],
                                    'similarity_score': round(similarity_score * 100, 1),
                                    'explanation': explanation,
                                    'why_read': basic_reading_rec,
                                    'cover_url': f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None,
                                    'page_count': book_details.get('number_of_pages'),
                                    'reading_time': reading_time
                                }

                                recommendations.append(recommendation)
                                seen_books.add(book_id)

                                filtered_recommendations = apply_filters(recommendations, filters)
                                current_recommendations = sorted(
                                    filtered_recommendations,
                                    key=lambda x: x['similarity_score'],
                                    reverse=True
                                )[:2]

                                data_dict = {
                                    'status': 'processing',
                                    'stage': 'finding_recommendations',
                                    'processed': subject_idx + 1,
                                    'total': len(common_subjects),
                                    'recommendations': current_recommendations
                                }

                                yield f"data: {json.dumps(data_dict)}\n\n"

            filtered_recommendations = apply_filters(recommendations, filters)
            final_recommendations = sorted(
                filtered_recommendations,
                key=lambda x: x['similarity_score'],
                reverse=True
            )[:2]

            print("\n=== Enhancing final recommendations with AI ===")
            data_dict = {
                'status': 'processing',
                'stage': 'enhancing_recommendations',
                'processed': 0,
                'total': len(final_recommendations),
                'recommendations': final_recommendations
            }

            yield f"data: {json.dumps(data_dict)}\n\n"

            # Now enhance the final recommendations with AI
            for idx, recommendation in enumerate(final_recommendations):
                try:
                    book_id = recommendation['id']
                    book_details = recommender.get_book_details(book_id)

                    if book_details:
                        # Use the new AI-enhanced methods
                        new_explanation = recommender.generate_similarity_explanation_with_ai(
                            book_details, 
                            input_books, 
                            recommendation['similarity_score']
                        )
                        why_read = recommender.generate_reading_recommendation_with_ai(
                            book_details, 
                            input_books
                        )

                        if new_explanation:
                            recommendation['explanation'] = new_explanation
                        if why_read:
                            recommendation['why_read'] = why_read

                    data_dict = {
                        'status': 'processing',
                        'stage': 'enhancing_recommendations',
                        'processed': idx + 1,
                        'total': len(final_recommendations),
                        'recommendations': final_recommendations
                    }

                    yield f"data: {json.dumps(data_dict)}\n\n"

                except Exception as e:
                    print(f"Error enhancing recommendation: {e}")
                    # Keep existing basic explanation if AI enhancement fails

            data_dict = {
                'status': 'completed',
                'recommendations': final_recommendations
            }

            yield f"data: {json.dumps(data_dict)}\n\n"

        except Exception as e:
            print(f"Error generating recommendations: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Content-Type': 'text/event-stream'
        }
    )

if __name__ == '__main__':
    app.run(debug=True)
