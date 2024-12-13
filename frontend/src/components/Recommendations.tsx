import React from 'react';

interface Book {
    id: string;
    title: string;
    author: string;
    year?: number;
    genres?: string[];
    similarity_score?: number;
    explanation?: string;
  }
  
  const Recommendations: React.FC<{ recommendations: Book[]; isLoading: boolean }> = ({ 
    recommendations, 
    isLoading 
  }) => {
    if (isLoading) {
      return (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mx-auto"></div>
          <p className="mt-4 text-gray-600">Finding your next favorite books...</p>
        </div>
      );
    }
  
    if (!recommendations.length) {
      return null;
    }
  
    return (
      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-6">Recommended Books</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {recommendations.map((book) => (
            <div key={book.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-all duration-300">
              <h3 className="text-xl font-semibold mb-2">{book.title}</h3>
              <p className="text-gray-600 mb-2">by {book.author}</p>
              {book.year && (
                <p className="text-gray-500 text-sm mb-3">Published in {book.year}</p>
              )}
              {book.similarity_score && (
                <div className="mb-3">
                  <div className="flex items-center gap-2">
                    <div className="text-sm text-gray-600">Match Score:</div>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-500" 
                        style={{ width: `${book.similarity_score}%` }}
                      />
                    </div>
                    <div className="text-sm font-medium text-blue-600">
                      {book.similarity_score}%
                    </div>
                  </div>
                </div>
              )}
              {book.explanation && (
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800">{book.explanation}</p>
                </div>
              )}
              {book.genres && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {book.genres.map((genre, index) => (
                    <span 
                      key={index} 
                      className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full
                               hover:bg-blue-200 transition-colors duration-200"
                    >
                      {genre}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };
  
  export default Recommendations;