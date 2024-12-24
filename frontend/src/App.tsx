import React, { useState } from 'react';
import BookInput from './components/BookInput';
import Recommendations from './components/Recommendations';
import { Alert, AlertDescription } from './components/Alert';
import confetti from 'canvas-confetti';
import AnimatedBook from './components/AnimatedBook';

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

const triggerConfetti = () => {
  confetti({
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 },
    colors: ['#3B82F6', '#6366F1', '#A855F7'], // blue and indigo to match your theme
  });

  // Add a second burst of confetti for more effect
  setTimeout(() => {
    confetti({
      particleCount: 50,
      spread: 50,
      origin: { y: 0.65 },
      colors: ['#3B82F6', '#6366F1', '#A855F7'],
    });
  }, 200);
};

function App() {
  const [recommendations, setRecommendations] = useState<(Book | null)[]>([null, null]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  const getLoadingMessage = (elapsedTime: number) => {
    if (elapsedTime < 20) return "Opening your book collection...";
    if (elapsedTime < 40) return "Reading through countless stories...";
    if (elapsedTime < 60) return "Matching literary patterns...";
    if (elapsedTime < 90) return "Writing your next chapter...";
    if (elapsedTime < 120) return "Analyzing writing styles...";
    if (elapsedTime < 150) return "Finding perfect matches...";
    if (elapsedTime < 180) return "Polishing recommendations...";
    if (elapsedTime < 210) return "Crafting detailed insights...";
    if (elapsedTime < 240) return "Adding final touches...";
    return "Carefully curating your recommendations...";
  };

  const handleBookSubmit = async (books: string[]) => {
    if (books.length !== 5) {
      setError("Please enter exactly 5 books for the best recommendations.");
      return;
    }
    
    setIsLoading(true);
    setLoadingMessage("Starting your literary journey...");
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
        
        // Add signal to allow timeout/cancellation
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 900000); // 15 minutes timeout

        const response = await fetch('https://book-recommender-api-affpgxcqgah8cvah.westus-01.azurewebsites.net/api/recommend', {
          method: 'POST',
          mode: 'cors',
          credentials: 'omit',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify({ books }),
          signal: controller.signal
        });
    
        clearTimeout(timeoutId);

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
          // Longer delay for setting recommendations
          setTimeout(() => {
            setRecommendations([
              data.recommendations[0] || null,
              data.recommendations[1] || null
            ]);
            triggerConfetti();
          }, 3000);
        } else {
          setError("We couldn't find matching recommendations. Please try different books.");
          setRecommendations([null, null]);
        }
        
        clearInterval(loadingUpdateInterval);
        setTimeout(() => {
          setIsLoading(false);
          setLoadingMessage("");
        }, 2000);
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
          setError('Reconnecting to our library...');
          setLoadingMessage("Retrying connection...");
          // Increased exponential backoff
          await new Promise(resolve => setTimeout(resolve, Math.pow(3, attempt) * 2000));
          return makeRequest(attempt + 1);
        }
        
        setError(error instanceof Error ? error.message : 'Unable to reach our library at the moment');
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
          <div className="flex items-center justify-center gap-4 mb-6">
            <img 
              src="/favicon.ico" 
              alt="Read Next" 
              className="w-16 h-16 md:w-20 md:h-20 transition-transform duration-300 hover:scale-105" 
            />
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 text-transparent bg-clip-text">
              Read Next
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
          <div className="bg-white/80 backdrop-blur-sm rounded-xl shadow-xl p-6 mb-8 transition-all duration-300 hover:shadow-2xl">
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
              <div className="mt-8 space-y-4 transition-all duration-500 transform animate-fadeInScale">
                <div className="animate-bookBounce">
                  <AnimatedBook />
                </div>
                <div className="text-center text-gray-600 transition-opacity">
                  <span className="animate-slideUp inline-block">
                    {loadingMessage}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className={`mt-8 transition-all duration-500 ${!isLoading ? 'animate-fadeInScale' : 'opacity-0'}`}>
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
