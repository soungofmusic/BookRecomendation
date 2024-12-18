import React, { useState } from 'react';
import BookInput from './components/BookInput';
import Recommendations from './components/Recommendations';

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

function App() {
  const [recommendations, setRecommendations] = useState<(Book | null)[]>([null, null]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState({
    processed: 0,
    total: 0
  });
  const [currentStage, setCurrentStage] = useState<string>('input_processing');

  const handleBookSubmit = async (books: string[]) => {
    if (!books.length) return;
    
    setIsLoading(true);
    setError(null);
    setRecommendations([null, null]);
    setProgress({ processed: 0, total: 0 });
    setCurrentStage('input_processing');
    
    try {
      console.log('Sending books to backend:', books);
      
      const API_URL = process.env.VITE_API_URL || 'http://localhost:5000';
      const response = await fetch(`${API_URL}/api/recommend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ books }),
      });
    
      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.error) {
                throw new Error(data.error);
              }

              // Update current stage
              if (data.stage) {
                setCurrentStage(data.stage);
              }

              if (data.recommendations?.length) {
                setRecommendations(prev => {
                  const newRecs = [...prev];
                  data.recommendations.forEach((rec: Book, index: number) => {
                    if (index < 2) {
                      newRecs[index] = rec;
                    }
                  });
                  return newRecs;
                });
              }

              if (data.processed !== undefined && data.total !== undefined) {
                setProgress({
                  processed: data.processed,
                  total: data.total
                });
              }

              if (data.status === 'completed') {
                setCurrentStage('completed');
                setIsLoading(false);
              }
            } catch (e) {
              console.error('Error parsing JSON:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      setError(error instanceof Error ? error.message : 'Failed to get recommendations');
      setRecommendations([null, null]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="container mx-auto py-12 px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-transparent bg-clip-text">
            Book Recommendations
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Enter your favorite books and discover new reads tailored to your taste
          </p>
        </div>

        {error && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 animate-fadeIn">
            <p className="text-sm">
              {error} Please try again or check if the backend server is running.
            </p>
          </div>
        )}

        <div className="max-w-4xl mx-auto">
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-xl p-6 mb-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                What books do you love?
              </h2>
              <p className="text-gray-600 text-sm">
                Enter up to 5 books to get personalized recommendations
              </p>
            </div>
            
            <BookInput
              onSubmit={handleBookSubmit}
              isLoading={isLoading}
            />
          </div>

          <div className="mt-8">
            <Recommendations
              recommendations={recommendations}
              isLoading={isLoading}
              processedCount={progress.processed}
              totalCount={progress.total}
              stage={currentStage}
            />
          </div>
        </div>

        <footer className="mt-16 text-center text-gray-500 text-sm">
          <p>Powered by Open Library API & Meta Llama</p>
        </footer>
      </div>
    </div>
  );
}

export default App;