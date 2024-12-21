import React, { useState } from 'react';
import BookInput from './components/BookInput';
import Recommendations from './components/Recommendations';
import { Alert, AlertDescription } from './components/Alert';

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
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  const getLoadingMessage = (elapsedTime: number) => {
    if (elapsedTime < 10) return "Analyzing your book choices...";
    if (elapsedTime < 20) return "Discovering matching themes and styles...";
    if (elapsedTime < 30) return "Finding your perfect next reads...";
    if (elapsedTime < 45) return "Almost there...";
    return "This is taking longer than usual. Please wait...";
  };

  const handleBookSubmit = async (books: string[]) => {
    if (books.length !== 5) {
      setError("Please enter exactly 5 books for the best recommendations.");
      return;
    }
    
    setIsLoading(true);
    setLoadingMessage("Starting your book journey...");
    setError(null);
    setRecommendations([null, null]);

    const makeRequest = async (attempt: number = 0): Promise<void> => {
      const startTime = Date.now();
      const loadingUpdateInterval = setInterval(() => {
        const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
        setLoadingMessage(getLoadingMessage(elapsedTime));
      }, 1000);

      try {
        console.log('Processing your book selection:', books);
        const response = await fetch('https://book-recommender-api-affpgxcqgah8cvah.westus-01.azurewebsites.net/api/recommend', {
          method: 'POST',
          mode: 'cors',
          credentials: 'omit',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ books })
        });
    
        let errorMessage = '';
        
        if (!response.ok) {
          const errorText = await response.text();
          try {
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.error || `Unable to process request: ${response.status}`;
          } catch (e) {
            errorMessage = errorText || `Unable to process request: ${response.status}`;
          }
          throw new Error(errorMessage);
        }

        const data = await response.json();

        if (data.error) {
          throw new Error(data.error);
        }

        if (data.recommendations?.length) {
          setRecommendations([
            data.recommendations[0] || null,
            data.recommendations[1] || null
          ]);
        } else {
          setError("We couldn't find matching recommendations. Please try different books.");
          setRecommendations([null, null]);
        }
        
        clearInterval(loadingUpdateInterval);
        setIsLoading(false);
        setLoadingMessage("");
        setRetryCount(0);

      } catch (error) {
        console.error('Error processing recommendations:', error);
        clearInterval(loadingUpdateInterval);
        
        if (error instanceof Error && 
            (error.message.includes('Failed to fetch') || 
             error.message.includes('network')) &&
            !error.message.includes('500') &&
            attempt < 3) {
          setRetryCount(attempt + 1);
          setError('Reconnecting to recommendation service...');
          setLoadingMessage("Retrying connection...");
          await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
          return makeRequest(attempt + 1);
        }
        
        setError(error instanceof Error ? error.message : 'Unable to get recommendations at this time');
        setRecommendations([null, null]);
        setIsLoading(false);
        setLoadingMessage("");
      }
    };

    try {
      await makeRequest();
    } catch (error) {
      console.error('Error in request:', error);
      setIsLoading(false);
      setLoadingMessage("");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="container mx-auto py-12 px-4">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <img src="/favicon.ico" alt="Book Next" className="w-10 h-10" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 text-transparent bg-clip-text">
              Book Next
            </h1>
          </div>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Share 5 books you love, and we'll find your perfect next reads
          </p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-8 animate-fadeIn">
            <AlertDescription>
              {error}
              {retryCount > 0 && (
                <div className="mt-1">
                  Retry attempt {retryCount} of 3...
                </div>
              )}
            </AlertDescription>
          </Alert>
        )}

        <div className="max-w-4xl mx-auto">
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-xl p-6 mb-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-2">
                Your Favorite Books
              </h2>
              <p className="text-gray-600 text-sm">
                Enter 5 books you've enjoyed to get personalized recommendations
              </p>
            </div>
            
            <BookInput
              onSubmit={handleBookSubmit}
              isLoading={isLoading}
            />

            {isLoading && loadingMessage && (
              <div className="mt-4 text-center text-gray-600">
                {loadingMessage}
              </div>
            )}
          </div>

          <div className="mt-8">
            <Recommendations
              recommendations={recommendations}
              isLoading={isLoading}
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