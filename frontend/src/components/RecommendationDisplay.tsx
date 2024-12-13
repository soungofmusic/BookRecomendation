import React from 'react';

interface Book {
  id: string;
  title: string;
  author: string;
  subjects?: string[];
}

const RecommendationDisplay: React.FC<{ recommendations: Book[] }> = ({ recommendations }) => {
  if (!recommendations.length) return null;

  return (
    <div className="mt-12 relative">
      <div className="absolute inset-0 bg-gradient-to-b from-blue-50 to-purple-50 opacity-50 rounded-xl" />
      
      <div className="relative bg-white/80 backdrop-blur-lg rounded-xl shadow-2xl p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-8 animate-slideIn">
          Your Perfect Next Reads
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {recommendations.map((book, index) => (
            <div
              key={book.id}
              className="group relative bg-white rounded-lg shadow-lg overflow-hidden
                         transform transition-all duration-500 hover:scale-105
                         animate-[slideIn_0.5s_ease-out_forwards]"
              style={{ animationDelay: `${index * 200}ms` }}
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 
                           group-hover:from-blue-500/10 group-hover:to-purple-500/10 transition-all duration-500" />
              
              <div className="relative p-6">
                <div className="flex items-start justify-between">
                  <h3 className="text-xl font-bold text-gray-800 group-hover:text-blue-600 
                               transition-colors duration-300">
                    {book.title}
                  </h3>
                  <div className="ml-4 transform rotate-0 group-hover:rotate-12 transition-transform duration-300">
                    📚
                  </div>
                </div>

                <p className="mt-2 text-gray-600">{book.author}</p>

                {book.subjects && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {book.subjects.map((subject, i) => (
                      <span
                        key={i}
                        className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-sm
                                 transform transition-all duration-300 hover:scale-110
                                 hover:bg-blue-100 cursor-pointer"
                      >
                        {subject}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RecommendationDisplay;