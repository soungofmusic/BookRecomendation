import React, { useState, useRef, useCallback } from 'react';

interface Book {
  id: string;
  title: string;
  author: string;
  year?: number;
  cover?: string;
  genres?: string[];
}

interface SuggestionState {
  loading: boolean;
  data: Book[];
  error: string | null;
}

const BookInput: React.FC<{
  onSubmit: (books: string[]) => void;
  isLoading: boolean;
}> = ({ onSubmit, isLoading }) => {
  const [bookInputs, setBookInputs] = useState<string[]>(Array(5).fill(''));
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestionState>({
    loading: false,
    data: [],
    error: null
  });
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const searchBooks = async (query: string) => {
    if (!query.trim()) {
      setSuggestions({ loading: false, data: [], error: null });
      return;
    }

    setSuggestions(prev => ({ ...prev, loading: true }));
    try {
      const response = await fetch(
        `https://openlibrary.org/search.json?q=${encodeURIComponent(query)}&limit=5`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch books');
      }

      const data = await response.json();
      const formattedBooks: Book[] = data.docs
        .slice(0, 5)
        .map((book: any) => ({
          id: book.key,
          title: book.title || 'Unknown Title',
          author: book.author_name?.[0] || 'Unknown Author',
          year: book.first_publish_year,
          cover: book.cover_i 
            ? `https://covers.openlibrary.org/b/id/${book.cover_i}-M.jpg` 
            : undefined,
          genres: book.subject?.slice(0, 3) || []
        }));

      setSuggestions({
        loading: false,
        data: formattedBooks,
        error: null
      });
    } catch (error) {
      console.error('Search error:', error);
      setSuggestions({
        loading: false,
        data: [],
        error: error instanceof Error ? error.message : 'Failed to fetch suggestions'
      });
    }
  };

  const handleInputChange = useCallback((index: number, value: string) => {
    const newInputs = [...bookInputs];
    newInputs[index] = value;
    setBookInputs(newInputs);

    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      searchBooks(value);
    }, 300);
  }, [bookInputs]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, index: number) => {
    if (e.key === 'Enter' && index < 4) {
      e.preventDefault();
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleSuggestionSelect = (index: number, book: Book) => {
    const newInputs = [...bookInputs];
    newInputs[index] = book.title;
    setBookInputs(newInputs);
    setSuggestions({ loading: false, data: [], error: null });

    // Move focus to next input if available
    if (index < 4) {
      setTimeout(() => {
        inputRefs.current[index + 1]?.focus();
      }, 100);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      <form onSubmit={(e) => { 
        e.preventDefault();
        if (bookInputs.every(book => book.trim())) {
          onSubmit(bookInputs);
        }
      }}>
        <div className="space-y-4">
          {bookInputs.map((input, index) => (
            <div key={index} className="relative">
              <div className="relative group">
                <input
                  ref={el => inputRefs.current[index] = el}
                  type="text"
                  value={input}
                  onChange={(e) => handleInputChange(index, e.target.value)}
                  onFocus={() => setActiveIndex(index)}
                  onKeyDown={(e) => handleKeyDown(e, index)}
                  placeholder={`Enter book ${index + 1}`}
                  className={`
                    w-full p-4 rounded-lg
                    bg-white/70 backdrop-blur-sm
                    border-2 transition-all duration-300
                    ${activeIndex === index ? 'border-blue-500 ring-4 ring-blue-200' : 'border-gray-200'}
                    focus:border-blue-500 focus:ring-4 focus:ring-blue-200
                    hover:shadow-lg
                    ${suggestions.loading && activeIndex === index ? 'pr-12' : 'pr-4'}
                  `}
                />

                {suggestions.loading && activeIndex === index && (
                  <div className="absolute right-4 top-1/2 -translate-y-1/2">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-500 border-t-transparent" />
                  </div>
                )}
              </div>

              {activeIndex === index && suggestions.data.length > 0 && (
                <div className="absolute z-50 w-full mt-2 bg-white rounded-lg shadow-lg border border-gray-200 max-h-60 overflow-y-auto">
                  {suggestions.data.map((book) => (
                    <div
                      key={book.id}
                      onClick={() => handleSuggestionSelect(index, book)}
                      className="p-4 hover:bg-blue-50 cursor-pointer border-b last:border-b-0"
                    >
                      <div className="flex items-start space-x-3">
                        {book.cover && (
                          <img
                            src={book.cover}
                            alt={book.title}
                            className="w-12 h-16 object-cover rounded"
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        )}
                        <div>
                          <div className="font-medium">{book.title}</div>
                          <div className="text-sm text-gray-600">
                            by {book.author}
                            {book.year && ` (${book.year})`}
                          </div>
                          {book.genres && book.genres.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {book.genres.map((genre, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-0.5 text-xs bg-blue-100 text-blue-800 rounded-full"
                                >
                                  {genre}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {suggestions.error && activeIndex === index && (
                <div className="mt-1 text-sm text-red-500">
                  {suggestions.error}
                </div>
              )}
            </div>
          ))}
        </div>

        <button
          type="submit"
          disabled={isLoading || bookInputs.some(book => !book.trim())}
          className="w-full mt-6 py-3 px-4 bg-blue-500 text-white rounded-lg
                   hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed
                   transition-colors duration-200"
        >
          {isLoading ? (
            <div className="flex items-center justify-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
              <span>Getting Recommendations...</span>
            </div>
          ) : (
            'Get Recommendations'
          )}
        </button>
      </form>
    </div>
  );
};

export default BookInput;