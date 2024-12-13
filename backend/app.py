from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter

app = Flask(__name__)
CORS(app)

OPEN_LIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPEN_LIBRARY_WORKS = "https://openlibrary.org/works/"

class BookRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
    def get_book_details(self, book_id: str) -> Dict[str, Any]:
        """Fetch detailed book information from Open Library"""
        try:
            response = requests.get(f"{OPEN_LIBRARY_WORKS}{book_id}.json")
            if response.ok:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching book details: {e}")
            return None

    def calculate_similarity_score(self, candidate_book: Dict, input_books: List[Dict]) -> float:
        """Calculate similarity score between a candidate book and input books"""
        score = 0
        weights = {
            'subject_match': 0.4,
            'year_match': 0.2,
            'author_match': 0.2,
            'description_match': 0.2
        }

        # Subject similarity
        input_subjects = set()
        for book in input_books:
            input_subjects.update(book.get('subjects', []))
        candidate_subjects = set(candidate_book.get('subjects', []))
        subject_similarity = len(input_subjects & candidate_subjects) / max(len(input_subjects | candidate_subjects), 1)

        # Year proximity
        try:
            candidate_year = int(candidate_book.get('first_publish_year', '0')[:4])
            input_years = [int(book.get('first_publish_year', '0')[:4]) for book in input_books if book.get('first_publish_year')]
            if input_years and candidate_year:
                avg_year = sum(input_years) / len(input_years)
                year_similarity = 1 / (1 + abs(candidate_year - avg_year) / 100)
            else:
                year_similarity = 0
        except:
            year_similarity = 0

        # Author similarity
        input_authors = set()
        for book in input_books:
            input_authors.update(book.get('authors', []))
        candidate_authors = set(candidate_book.get('authors', []))
        author_similarity = len(input_authors & candidate_authors) / max(len(input_authors | candidate_authors), 1)

        # Calculate weighted score
        score = (
            weights['subject_match'] * subject_similarity +
            weights['year_match'] * year_similarity +
            weights['author_match'] * author_similarity
        )

        return score

    def generate_explanation(self, book: Dict, input_books: List[Dict], similarity_score: float) -> str:
        """Generate human-readable explanation for recommendation"""
        explanations = []
        
        # Shared subjects
        shared_subjects = set(book.get('subjects', [])) & set(sum([b.get('subjects', []) for b in input_books], []))
        if shared_subjects:
            subject_examples = list(shared_subjects)[:3]
            explanations.append(f"shares genres like {', '.join(subject_examples)}")

        # Year proximity
        try:
            book_year = int(book.get('first_publish_year', '0'))
            input_years = [int(b.get('first_publish_year', '0')) for b in input_books if b.get('first_publish_year')]
            if input_years and book_year:
                avg_year = sum(input_years) / len(input_years)
                year_diff = abs(book_year - avg_year)
                if year_diff <= 20:
                    explanations.append(f"was published around the same time")
                elif year_diff <= 50:
                    explanations.append(f"was published in a similar era")
        except:
            pass

        # Author connection
        shared_authors = set(book.get('authors', [])) & set(sum([b.get('authors', []) for b in input_books], []))
        if shared_authors:
            explanations.append("is by an author you've read")

        # Combine explanations
        if explanations:
            explanation = f"This book was recommended because it {' and '.join(explanations)}"
            explanation += f", with a {similarity_score:.1f}% match to your preferences."
        else:
            explanation = "This book matches your reading preferences based on multiple factors."

        return explanation

# Initialize recommender
recommender = BookRecommender()

@app.route('/')
def home():
    return jsonify({"message": "Book Recommendation API is running"})

@app.route('/api/search', methods=['GET'])
def search_books():
    """Search endpoint for book autocomplete"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    try:
        response = requests.get(
            OPEN_LIBRARY_SEARCH,
            params={
                'q': query,
                'fields': 'key,title,author_name,first_publish_year,subject,cover_i',
                'limit': 5
            }
        )
        
        if not response.ok:
            return jsonify({"error": "Failed to search books"}), response.status_code

        data = response.json()
        books = [{
            'id': book.get('key', '').split('/')[-1],
            'title': book.get('title', ''),
            'author': book.get('author_name', ['Unknown Author'])[0] if book.get('author_name') else 'Unknown Author',
            'year': book.get('first_publish_year'),
            'cover': f"https://covers.openlibrary.org/b/id/{book.get('cover_i')}-M.jpg" if book.get('cover_i') else None,
            'genres': book.get('subject', [])[:5] if book.get('subject') else []
        } for book in data.get('docs', [])]

        return jsonify(books)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """Get book recommendations based on input books"""
    data = request.json
    book_titles = data.get('books', [])
    
    if not book_titles:
        return jsonify({"error": "No books provided"}), 400

    try:
        # Get details for input books
        input_books = []
        all_subjects = set()
        
        for title in book_titles:
            response = requests.get(
                OPEN_LIBRARY_SEARCH,
                params={'q': title, 'limit': 1}
            )
            if response.ok and response.json().get('docs'):
                book = response.json()['docs'][0]
                book_details = recommender.get_book_details(book.get('key', '').split('/')[-1])
                if book_details:
                    input_books.append(book_details)
                    if 'subjects' in book_details:
                        all_subjects.update(book_details['subjects'])

        if not input_books:
            return jsonify({"error": "Could not process input books"}), 400

        # Find similar books
        recommendations = []
        seen_books = set()
        
        # Search by common subjects
        common_subjects = Counter(sum([book.get('subjects', []) for book in input_books], [])).most_common(5)
        
        for subject, _ in common_subjects:
            response = requests.get(
                OPEN_LIBRARY_SEARCH,
                params={
                    'q': f'subject:{subject}',
                    'fields': 'key,title,author_name,first_publish_year,subject,cover_i',
                    'limit': 5
                }
            )
            
            if response.ok:
                for book in response.json().get('docs', []):
                    book_id = book.get('key', '').split('/')[-1]
                    if book_id not in seen_books:
                        book_details = recommender.get_book_details(book_id)
                        if book_details:
                            similarity_score = recommender.calculate_similarity_score(book_details, input_books)
                            explanation = recommender.generate_explanation(book_details, input_books, similarity_score * 100)
                            
                            recommendations.append({
                                'id': book_id,
                                'title': book.get('title', ''),
                                'author': book.get('author_name', ['Unknown'])[0] if book.get('author_name') else 'Unknown',
                                'year': book.get('first_publish_year'),
                                'cover': f"https://covers.openlibrary.org/b/id/{book.get('cover_i')}-M.jpg" if book.get('cover_i') else None,
                                'genres': book.get('subject', [])[:5] if book.get('subject') else [],
                                'similarity_score': round(similarity_score * 100, 1),
                                'explanation': explanation
                            })
                            seen_books.add(book_id)

        # Sort by similarity score and get top 2
        recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
        recommendations = recommendations[:2]

        return jsonify({"recommendations": recommendations})
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        return jsonify({"error": "Failed to generate recommendations"}), 500

if __name__ == '__main__':
    app.run(debug=True)