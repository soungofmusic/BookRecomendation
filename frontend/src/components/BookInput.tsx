import React, { useState, useRef, useCallback } from 'react';
import { cacheService, preloadImage } from '../services/cache';
import { GlowingButton } from './GlowingButton';

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

export const BookInput: React.FC<{
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

    const cacheKey = `search:${query}`;
    const cachedResults = cacheService.get<Book[]>(cacheKey);
    
    if (cachedResults) {
      setSuggestions({ loading: false, data: cachedResults, error: null });
      return;
    }

    setSuggestions(prev => ({ ...prev, loading: true }));
    
    try {
      const response = await fetch(
        `https://openlibrary.org/search.json?q=${encodeURIComponent(query)}&limit=5`
      );

      if (!response.ok) throw new Error('Failed to fetch books');

      const data = await response.json();
      const formattedBooks: Book[] = await Promise.all(
        data.docs.slice(0, 5).map(async (book: any) => {
          const coverUrl = book.cover_i 
            ? `https://covers.openlibrary.org/b/id/${book.cover_i}-M.jpg`
            : null;

          if (coverUrl) {
            try {
              await preloadImage(coverUrl);
            } catch (error) {
              console.warn(`Failed to preload image for ${book.title}`);
            }
          }

          return {
            id: book.key,
            title: book.title || 'Unknown Title',
            author: book.author_name?.[0] || 'Unknown Author',
            year: book.first_publish_year,
            cover: coverUrl,
            genres: book.subject?.slice(0, 3) || []
          };
        })
      );

      cacheService.set(cacheKey, formattedBooks);
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

  const handleSuggestionSelect = (index: number, book: Book) => {
    const newInputs = [...bookInputs];
    newInputs[index] = book.title;
    setBookInputs(newInputs);
    setSuggestions({ loading: false, data: [], error: null });

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
        const validBooks = bookInputs.filter(book => book.trim());
        if (validBooks.length > 0) {
          onSubmit(validBooks);
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
                  placeholder={`Enter book ${index + 1}`}
                  className={`
                    w-full p-4 rounded-lg
                    bg-white/70 backdrop-blur-sm
                    border-2 transition-all duration-300
                    ${activeIndex === index ? 'border-blue-500 ring-4 ring-blue-200' : 'border-gray-200'}
                    focus:border-blue-500 focus:ring-4 focus:ring-blue-200
                    hover:shadow-lg
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
                        <div className="flex-shrink-0 w-12 h-16 bg-gray-100 rounded overflow-hidden">
                          {book.cover ? (
                            <img
                              src={book.cover}
                              alt={book.title}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                const target = e.target as HTMLImageElement;
                                target.src = `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="64" viewBox="0 0 48 64"><rect width="48" height="64" fill="%23f3f4f6"/><text x="50%" y="50%" font-family="Arial" font-size="24" fill="%236b7280" dominant-baseline="middle" text-anchor="middle">${book.title[0]}</text></svg>`;
                              }}
                            />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center bg-blue-100 text-blue-500 font-medium">
                              {book.title[0]}
                            </div>
                          )}
                        </div>
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
            </div>
          ))}
        </div>

        <GlowingButton
          type="submit"
          disabled={isLoading || !bookInputs.some(book => book.trim())}
          loading={isLoading}
        >
          Get Recommendations
        </GlowingButton>
      </form>
    </div>
  );
};

export default BookInput;