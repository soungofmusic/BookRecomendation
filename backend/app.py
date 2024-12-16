from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import requests
import json
from typing import List, Dict, Any, Optional
from collections import Counter
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    print("Llama CPP not available. Running without AI explanations.")
    LLAMA_AVAILABLE = False

app = Flask(__name__)
CORS(app)

OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_WORKS = "https://openlibrary.org/works/"

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
        if LLAMA_AVAILABLE:
            try:
                self.llm = Llama(
                    model_path="./models/Llama-3.2-3B-Instruct-f16.gguf",
                    n_ctx=2048,
                    n_threads=4
                )
                print("Llama model loaded successfully")
            except Exception as e:
                print(f"Error loading Llama model: {e}")
                self.llm = None
        else:
            self.llm = None

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
        try:
            candidate_year = int(candidate_book.get('first_publish_date', '0')[:4])
            input_years = []
            for book in input_books:
                if 'first_publish_date' in book:
                    try:
                        year = int(book['first_publish_date'][:4])
                        input_years.append(year)
                    except (ValueError, TypeError):
                        continue

            if input_years and candidate_year:
                avg_year = sum(input_years) / len(input_years)
                year_similarity = 1 / (1 + abs(candidate_year - avg_year) / 100)
            else:
                year_similarity = 0
        except (ValueError, TypeError):
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

        # Year proximity
        try:
            book_year = None
            if book.get('first_publish_date'):
                try:
                    book_year = int(str(book['first_publish_date'])[:4])
                except (ValueError, TypeError):
                    pass

            input_years = []
            for input_book in input_books:
                if input_book.get('first_publish_date'):
                    try:
                        year = int(str(input_book['first_publish_date'])[:4])
                        input_years.append(year)
                    except (ValueError, TypeError):
                        continue

            if input_years and book_year:
                avg_year = sum(input_years) / len(input_years)
                year_diff = abs(book_year - avg_year)
                if year_diff <= 20:
                    explanations.append("was published around the same time")
                elif year_diff <= 50:
                    explanations.append("was published in a similar era")
        except Exception as e:
            print(f"Error processing year comparison: {e}")
            pass

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

    def generate_reading_recommendation_with_llama(self, book: Dict, input_books: List[Dict]) -> str:
        """Generate a compelling and detailed reason why someone should read this book using Llama"""
        if not self.llm:
            return self.generate_reading_recommendation(book, input_books)

        try:
            prompt = f"""<s>[INST] Create a detailed and compelling recommendation for why someone should read this book:

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
Provide specific details and compelling reasons.
Aim for 4-6 sentences that paint a vivid picture of the reading experience. [/INST]</s>"""

            response = self.llm(
                prompt,
                max_tokens=512,
                temperature=0.75,
                stop=["[/INST]", "</s>"],
                top_p=0.9,
                repeat_penalty=1.1
            )

            recommendation = response['choices'][0]['text'].strip()

            # Validate output quality
            if len(recommendation) < 100 or "**" in recommendation or len(recommendation) > 1000:
                return self.generate_reading_recommendation(book, input_books)
                
            return recommendation

        except Exception as e:
            print(f"Error generating Llama recommendation: {e}")
            return self.generate_reading_recommendation(book, input_books)

    def generate_similarity_explanation_with_llama(self, book: Dict, input_books: List[Dict], similarity_score: float) -> str:
        """Generate a detailed explanation of why this book matches the user's preferences using Llama"""
        if not self.llm:
            return self.generate_explanation(book, input_books, similarity_score)

        try:
            shared_subjects = set(book.get('subjects', [])) & set(sum([b.get('subjects', []) for b in input_books], []))
            book_year = int(book.get('first_publish_date', '0')[:4]) if book.get('first_publish_date') else None
            input_years = [int(b.get('first_publish_date', '0')[:4]) for b in input_books if b.get('first_publish_date')]
            avg_year = sum(input_years) / len(input_years) if input_years else None

            prompt = f"""<s>[INST] Analyze why this book matches the reader's preferences:

Book Details:
Title: {book.get('title', '')}
Author: {book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown'}
Year: {book_year if book_year else 'Unknown'}
Shared Genres: {', '.join(list(shared_subjects)[:3])}
Similarity Score: {similarity_score:.1f}%

Reader's Preferences:
- Favorite Genres: {', '.join(list(set(sum([b.get('subjects', [])[:3] for b in input_books], []))))}
- Preferred Era: Around {int(avg_year) if avg_year else 'Unknown'}

Explain why this book would appeal to the reader based on these matches. Focus on specific connections and shared elements. Keep it concise (4-5 sentences) and analytical. [/INST]</s>"""

            response = self.llm(
                prompt,
                max_tokens=256,
                temperature=0.7,
                stop=["[/INST]", "</s>"],
                top_p=0.9,
                repeat_penalty=1.1
            )

            explanation = response['choices'][0]['text'].strip()

            # Validate output quality
            if len(explanation) < 50 or "**" in explanation or len(explanation) > 500:
                return self.generate_explanation(book, input_books, similarity_score)

            return explanation

        except Exception as e:
            print(f"Error generating Llama explanation: {e}")
            return self.generate_explanation(book, input_books, similarity_score)

recommender = BookRecommender()

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    def generate():
        try:
            data = request.json
            book_titles = data.get('books', [])
            filters = data.get('filters', {})
            print(f"\n--- Starting recommendation process for books: {book_titles} ---")

            # Initialize final_recommendations to avoid referencing it before assignment
            final_recommendations = []

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

            # During finding recommendations, only do basic explanation and reading rec
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
                                # Basic explanation and reading recommendation here
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
                                    'why_read': None,
                                    'cover_url': f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None,
                                    'page_count': book_details.get('number_of_pages'),
                                    'reading_time': reading_time
                                }

                                recommendations.append(recommendation)
                                seen_books.add(book_id)

                                # Apply filters to current recommendations
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

            # Get final filtered recommendations
            filtered_recommendations = apply_filters(recommendations, filters)
            final_recommendations = sorted(
                filtered_recommendations,
                key=lambda x: x['similarity_score'],
                reverse=True
            )[:2]

            print("\n=== Enhancing final recommendations with Llama ===")
            data_dict = {
                'status': 'processing',
                'stage': 'enhancing_recommendations',
                'processed': 0,
                'total': len(final_recommendations),
                'recommendations': final_recommendations
            }

            yield f"data: {json.dumps(data_dict)}\n\n"

            # Now use Llama for the final 2 recommendations
            for idx, recommendation in enumerate(final_recommendations):
                try:
                    book_id = recommendation['id']
                    book_details = recommender.get_book_details(book_id)

                    if book_details:
                        # Overwrite explanation and why_read with Llama enhanced versions
                        new_explanation = recommender.generate_similarity_explanation_with_llama(book_details, input_books, recommendation['similarity_score'])
                        why_read = recommender.generate_reading_recommendation_with_llama(book_details, input_books)

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
                    # Keep existing basic explanation if Llama fails

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
