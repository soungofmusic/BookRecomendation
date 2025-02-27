import React, { useState, useEffect, useCallback } from 'react';
import BookInput from './components/BookInput';
import Recommendations from './components/Recommendations';
import { Alert, AlertDescription } from './components/Alert';
import confetti from 'canvas-confetti';
import AnimatedBook from './components/AnimatedBook';
import ThemeToggle from './components/ThemeToggle';

interface Book {
  id: string;
  title: string;
  author: string;
  year?: number;
  genres?: string[];
  similarity_score?: number;
  explanation?: string;
  cover_url?: string;
  why_read?: string;
}

interface PaginationData {
  current_page: number;
  per_page: number;
  total_items: number;
  total_pages: number;
}

function App() {
  const [recommendations, setRecommendations] = useState<(Book | null)[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);
  const [loadingMessage, setLoadingMessage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pagination, setPagination] = useState<PaginationData | null>(null);
  const [hasMore, setHasMore] = useState<boolean>(false);
  
  // Save input books for "load more" requests
  const [lastSubmittedBooks, setLastSubmittedBooks] = useState<string[]>([]);

  // Handle mobile viewport height
  useEffect(() => {
    const setVH = () => {
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    };

    setVH();
    window.addEventListener('resize', setVH);
    return () => window.removeEventListener('resize', setVH);
  }, []);

  const triggerConfetti = () => {
    const isMobile = window.innerWidth < 768;
    confetti({
      particleCount: isMobile ? 50 : 100,
      spread: isMobile ? 50 : 70,
      origin: { y: isMobile ? 0.5 : 0.6 },
      colors: ['#3B82F6', '#6366F1', '#A855F7'],
    });

    setTimeout(() => {
      confetti({
        particleCount: isMobile ? 25 : 50,
        spread: isMobile ? 40 : 50,
        origin: { y: isMobile ? 0.55 : 0.65 },
        colors: ['#3B82F6', '#6366F1', '#A855F7'],
      });
    }, 200);
  };
  
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

  const fetchRecommendations = async (books: string[], page: number, isLoadMore: boolean = false): Promise<void> => {
    const loadingStateSetter = isLoadMore ? setIsLoadingMore : setIsLoading;
    const messageSetter = isLoadMore ? () => {} : setLoadingMessage; // Only show messages for initial load
    
    loadingStateSetter(true);
    if (!isLoadMore) {
      messageSetter("Starting your literary journey...");
    }
    
    const startTime = Date.now();
    const loadingUpdateInterval = !isLoadMore ? setInterval(() => {
      const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
      messageSetter(getLoadingMessage(elapsedTime));
    }, 1000) : null;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 900000);

      const response = await fetch(`https://book-recommender-api-affpgxcqgah8cvah.westus-01.azurewebsites.net/api/recommend?page=${page}&per_page=2`, {
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

      if (!response.ok) {
        const errorText = await response.text();
        const errorMessage = (() => {
          try {
            const errorJson = JSON.parse(errorText);
            return errorJson.error || `Unable to process request: ${response.status}`;
          } catch {
            return errorText || `Unable to process request: ${response.status}`;
          }
        })();
        throw new Error(errorMessage);
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      if (data.recommendations?.length) {
        // Save pagination data
        if (data.pagination) {
          setPagination(data.pagination);
          setCurrentPage(data.pagination.current_page);
          setHasMore(data.pagination.current_page < data.pagination.total_pages);
        } else {
          setHasMore(false);
        }
        
        // Update recommendations based on whether this is initial load or "load more"
        if (isLoadMore) {
          setRecommendations(prev => [...prev, ...data.recommendations]);
        } else {
          setTimeout(() => {
            setRecommendations(data.recommendations);
            triggerConfetti();
          }, 3000);
        }
      } else {
        if (!isLoadMore) {
          setError("We couldn't find matching recommendations. Please try different books.");
          setRecommendations([]);
        }
        setHasMore(false);
      }
      
      if (loadingUpdateInterval) clearInterval(loadingUpdateInterval);
      
      setTimeout(() => {
        loadingStateSetter(false);
        if (!isLoadMore) messageSetter("");
      }, isLoadMore ? 0 : 2000);
      
      setRetryCount(0);
    } catch (error) {
      console.error('Error processing recommendations:', error);
      if (loadingUpdateInterval) clearInterval(loadingUpdateInterval);
      
      if (error instanceof Error && 
          (error.message.includes('Failed to fetch') || 
           error.message.includes('network')) &&
          !error.message.includes('500') &&
          retryCount < 3) {
        setRetryCount(prev => prev + 1);
        setError('Reconnecting to our library...');
        if (!isLoadMore) messageSetter("Retrying connection...");
        await new Promise(resolve => setTimeout(resolve, Math.pow(3, retryCount) * 2000));
        return fetchRecommendations(books, page, isLoadMore);
      }
      
      setError(error instanceof Error ? error.message : 'Unable to reach our library at the moment');
      if (!isLoadMore) {
        setRecommendations([]);
      }
      loadingStateSetter(false);
      if (!isLoadMore) messageSetter("");
    }
  };

  const handleBookSubmit = async (books: string[]) => {
    if (books.length !== 5) {
      setError("Please enter exactly 5 books for the best recommendations.");
      return;
    }
    
    // Reset states for new search
    setRecommendations([]);
    setCurrentPage(1);
    setPagination(null);
    setHasMore(false);
    setError(null);
    
    // Save the books for potential "load more" requests
    setLastSubmittedBooks(books);
    
    // Fetch first page
    await fetchRecommendations(books, 1);
  };

  const handleLoadMore = useCallback(() => {
    if (!isLoadingMore && hasMore && lastSubmittedBooks.length > 0) {
      fetchRecommendations(lastSubmittedBooks, currentPage + 1, true);
    }
  }, [isLoadingMore, hasMore, lastSubmittedBooks, currentPage]);

  return (
    <div className="min-h-screen min-h-[calc(var(--vh,1vh)*100)] bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-900 dark:to-gray-800 transition-colors duration-200">
      {/* Theme Toggle - positioned differently for mobile and desktop */}
      <div className="fixed bottom-4 right-4 md:top-4 md:bottom-auto z-50">
        <ThemeToggle />
      </div>

      <div className="container mx-auto py-6 md:py-12 px-4 sm:px-6">
        {/* Header Section */}
        <div className="text-center mb-8 md:mb-12">
          <div className="flex items-center justify-center gap-3 md:gap-4 mb-4 md:mb-6">
            <img 
              src="/favicon.ico" 
              alt="Read Next" 
              className="w-12 h-12 md:w-20 md:h-20 transition-transform duration-300 hover:scale-105" 
            />
            <h1 className="text-3xl md:text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 
                         dark:from-blue-400 dark:to-indigo-400 text-transparent bg-clip-text">
              Read Next
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-300 max-w-2xl mx-auto text-sm md:text-base">
            Share 5 books you love, and we'll find your perfect next reads
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6 md:mb-8 animate-fadeIn max-w-4xl mx-auto">
            <AlertDescription className="text-sm">
              {error}
              {retryCount > 0 && (
                <div className="mt-1">
                  Retry attempt {retryCount} of 3...
                </div>
              )}
            </AlertDescription>
          </Alert>
        )}

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {/* Input Section */}
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-lg md:rounded-xl 
                         shadow-lg md:shadow-xl p-4 md:p-6 mb-6 md:mb-8 
                         transition-all duration-300 hover:shadow-xl md:hover:shadow-2xl">
            <div className="mb-4 md:mb-6">
              <h2 className="text-lg md:text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2">
                Your Favorite Books
              </h2>
              <p className="text-gray-600 dark:text-gray-400 text-xs md:text-sm">
                Enter 5 books you've enjoyed to get personalized recommendations
              </p>
            </div>
            
            <BookInput
              onSubmit={handleBookSubmit}
              isLoading={isLoading}
            />

            {/* Loading State */}
            {isLoading && loadingMessage && (
              <div className="mt-6 md:mt-8 space-y-3 md:space-y-4 
                           transition-all duration-500 transform animate-fadeInScale">
                <div className="animate-bookBounce max-w-[150px] md:max-w-[200px] mx-auto">
                  <AnimatedBook />
                </div>
                <div className="text-center text-gray-600 dark:text-gray-400 transition-opacity">
                  <span className="animate-slideUp inline-block text-sm md:text-base">
                    {loadingMessage}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Recommendations Section */}
          <div className={`mt-6 md:mt-8 transition-all duration-500 
                        ${!isLoading ? 'animate-fadeInScale' : 'opacity-0'}`}>
            <Recommendations
              recommendations={recommendations}
              isLoading={isLoading}
            />
            
            {/* Load More Button */}
            {hasMore && recommendations.length > 0 && (
              <div className="flex justify-center mt-8">
                <button
                  onClick={handleLoadMore}
                  disabled={isLoadingMore}
                  className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-500 
                           text-white rounded-lg font-medium shadow-md
                           transition-all duration-300 transform hover:scale-105
                           disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {isLoadingMore ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                      <span>Loading...</span>
                    </div>
                  ) : (
                    'Load More Recommendations'
                  )}
                </button>
              </div>
            )}
            
            {/* Pagination Info (optional) */}
            {pagination && recommendations.length > 0 && (
              <div className="text-center mt-4 text-sm text-gray-500 dark:text-gray-400">
                Showing {recommendations.length} of {pagination.total_items} recommendations
              </div>
            )}
          </div>
        </div>

        {/* Footer - extra bottom padding on mobile for theme toggle */}
        <footer className="mt-12 md:mt-16 text-center text-gray-500 dark:text-gray-400 
                        text-xs md:text-sm pb-20 md:pb-8">
          <p>Powered by Open Library API & Meta Llama</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
