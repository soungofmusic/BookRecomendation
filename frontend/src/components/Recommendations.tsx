import React from 'react';
import LibraryFinder from './LibraryFinder';
import BookSkeleton from './BookSkeleton';

// Interfaces
interface Book {
  id: string;
  title: string;
  author: string;
  year?: number;
  genres?: string[];
  similarity_score?: number;
  explanation?: string;
  cover_url?: string;
  basic_recommendation?: string;
  ai_recommendation?: string;
  why_read?: string;
}

interface RecommendationsProps {
  recommendations: (Book | null)[];
  isLoading: boolean;
}

interface TooltipProps {
  content: string;
  children: React.ReactNode;
}

// Tooltip Component
const Tooltip: React.FC<TooltipProps> = ({ content, children }) => (
  <div className="group relative inline-block">
    {children}
    <div className="opacity-0 invisible group-hover:opacity-100 group-hover:visible 
                    transition-opacity duration-200 absolute -top-2 left-1/2 -translate-x-1/2 
                    -translate-y-full bg-gray-900 text-white text-sm rounded px-2 py-1 w-48 z-10">
      {content}
      <div className="absolute top-full left-1/2 -translate-x-1/2 -translate-y-1/2 
                      border-4 border-transparent border-t-gray-900" />
    </div>
  </div>
);

// Main Component
const Recommendations: React.FC<RecommendationsProps> = ({
  recommendations,
  isLoading
}) => {
  const renderBook = (book: Book) => {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-xl transition-all duration-300">
        <div className="p-4">
          {/* Book Cover and Details Section */}
          <div className="flex gap-4">
            {/* Book Cover */}
            <div className="relative flex-shrink-0 w-24 h-36 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden group">
              {book.cover_url ? (
                <>
                  <img
                    src={book.cover_url}
                    alt={`Cover of ${book.title}`}
                    className="w-full h-full object-cover transition-transform duration-300 
                             group-hover:scale-110"
                    loading="lazy"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = `data:image/svg+xml,${encodeURIComponent(`
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 144" fill="#E5E7EB">
                          <rect width="96" height="144"/>
                          <text x="48" y="72" font-family="Arial" font-size="24" fill="#4B5563" 
                                text-anchor="middle" dominant-baseline="middle">
                            ${book.title[0]}
                          </text>
                        </svg>
                      `)}`;
                    }}
                  />
                  <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100
                                transition-opacity duration-300 flex flex-col justify-end p-2" />
                </>
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-blue-50 to-white dark:from-blue-900 dark:to-gray-800">
                  <span className="text-2xl font-bold text-blue-400">{book.title[0]}</span>
                </div>
              )}
            </div>

            {/* Book Details */}
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{book.title}</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">by {book.author}</p>
              {book.year && (
                <p className="text-gray-500 dark:text-gray-500 text-sm">Published {book.year}</p>
              )}
              
              {/* Similarity Score */}
              {book.similarity_score !== undefined && (
                <div className="mt-2">
                  <Tooltip content="Match score based on your preferences">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-1.5">
                        <div 
                          className="bg-blue-500 h-1.5 rounded-full transition-all duration-300" 
                          style={{ width: `${book.similarity_score}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                        {book.similarity_score}%
                      </span>
                    </div>
                  </Tooltip>
                </div>
              )}
            </div>
          </div>

          {/* Score Explanation */}
          {book.explanation && (
            <div className="mt-4 p-3 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg">
              <h4 className="text-sm font-semibold text-indigo-700 dark:text-indigo-300 mb-2">
                Why This Match?
              </h4>
              <p className="text-sm text-indigo-800 dark:text-indigo-200 leading-relaxed">
                {book.explanation}
              </p>
            </div>
          )}

          {/* Why Read This Book */}
          {book.why_read && (
            <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">
                Why Read This Book?
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                {book.why_read}
              </p>
            </div>
          )}

          {/* Genres */}
          {book.genres && book.genres.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1">
              {book.genres.map((genre) => (
                <span 
                  key={genre}
                  className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded
                            hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-150"
                >
                  {genre}
                </span>
              ))}
            </div>
          )}

          {/* Library Finder */}
          <LibraryFinder 
            title={book.title}
            author={book.author}
          />
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-6 text-center bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 text-transparent bg-clip-text">
          Finding Your Next Books...
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2].map((index) => (
            <div key={index} className="animate-fadeIn">
              <BookSkeleton />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Check if we have any recommendations to show
  const hasRecommendations = recommendations.filter(book => book !== null).length > 0;

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-bold mb-6 text-center bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 text-transparent bg-clip-text">
        {hasRecommendations ? 'Recommended Books' : 'No Recommendations Found'}
      </h2>
      
      {hasRecommendations ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {recommendations.map((book, index) => (
            book && (
              <div key={book.id || `book-${index}`} className="animate-fadeIn">
                {renderBook(book)}
              </div>
            )
          ))}
        </div>
      ) : (
        <div className="text-center py-10 text-gray-500 dark:text-gray-400">
          Try entering different books to get recommendations.
        </div>
      )}
    </div>
  );
};

export default Recommendations;
