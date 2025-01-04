import React, { useEffect, useState } from 'react';
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

// Book Cover Component
const BookCover: React.FC<{ book: Book }> = React.memo(({ book }) => {
  const [imageLoaded, setImageLoaded] = useState(false);

  return (
    <div className="relative flex-shrink-0 w-24 h-36 bg-gray-100 dark:bg-gray-800 rounded overflow-hidden group">
      {/* Blur placeholder */}
      {book.cover_url && !imageLoaded && (
        <div className="absolute inset-0 animate-pulse bg-skeleton-gradient bg-skeleton">
          <div className="w-full h-full bg-shimmer-gradient animate-shimmer" />
          <span className="absolute inset-0 flex items-center justify-center text-2xl font-bold text-gray-400">
            {book.title[0]}
          </span>
        </div>
      )}

      {/* Main image or fallback */}
      {book.cover_url ? (
        <img
          src={book.cover_url}
          alt={`Cover of ${book.title}`}
          className={`w-full h-full object-cover transition-all duration-300 
                   group-hover:scale-110 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
          loading="lazy"
          onLoad={() => setImageLoaded(true)}
          onError={() => setImageLoaded(true)}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gradient-to-b from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-600">
          <span className="text-2xl font-bold text-gray-400 dark:text-gray-500">{book.title[0]}</span>
        </div>
      )}

      {/* Hover overlay */}
      <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100
                    transition-opacity duration-300 flex flex-col justify-end p-2" />
    </div>
  );
});

// Main Component
const Recommendations: React.FC<RecommendationsProps> = ({
  recommendations,
  isLoading
}) => {
  const [displayedBooks, setDisplayedBooks] = useState<(Book | null)[]>([null, null]);

  useEffect(() => {
    setDisplayedBooks(recommendations);
  }, [recommendations]);

  const renderBook = (book: Book) => {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-xl transition-all duration-300">
        <div className="p-4">
          {/* Book Cover and Details Section */}
          <div className="flex gap-4">
            <BookCover book={book} />

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
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div 
                          className="bg-blue-500 dark:bg-blue-400 h-1.5 rounded-full transition-all duration-300" 
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
            <div className="mt-4 p-3 bg-gradient-to-br from-indigo-50 to-purple-50 
                         dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg">
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
            <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Why Read This Book?
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
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
                  className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                          text-xs rounded hover:bg-gray-200 dark:hover:bg-gray-600 
                          transition-colors duration-150"
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
        <h2 className="text-2xl font-bold mb-6 text-center bg-gradient-to-r from-blue-600 to-indigo-600 
                     dark:from-blue-400 dark:to-indigo-400 text-transparent bg-clip-text">
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

  return (
    <div className="mt-8">
      <h2 className="text-2xl font-bold mb-6 text-center bg-gradient-to-r from-blue-600 to-indigo-600 
                   dark:from-blue-400 dark:to-indigo-400 text-transparent bg-clip-text">
        Recommended Books
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {displayedBooks.map((book, index) => (
          <div key={index} className="animate-fadeIn">
            {book && renderBook(book)}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Recommendations;