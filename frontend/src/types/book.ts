// Book type definitions for the recommendation system
export interface Book {
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
    page_count?: number;
    reading_time?: {
      hours?: number;
      minutes?: number;
    };
  }
  
  export interface FilterState {
    genre: string;
    yearRange: [number, number];
    pageCount: [number, number];
    minScore: number;
  }
  
  export interface RecommendationsProps {
    recommendations: (Book | null)[];
    isLoading: boolean;
    processedCount?: number;
    totalCount?: number;
    stage?: string;
  }
  
  export interface TooltipProps {
    content: string;
    children: React.ReactNode;
  }
  
  // Utility type for API response
  export interface ApiResponse {
    status: 'processing' | 'completed' | 'error';
    stage?: string;
    processed?: number;
    total?: number;
    recommendations?: Book[];
    error?: string;
  }
  
  // Types for reading time calculations
  export interface ReadingTime {
    hours?: number;
    minutes?: number;
  }
  
  // Types for book details from the API
  export interface BookDetails {
    key: string;
    title: string;
    author_name?: string[];
    first_publish_year?: number;
    subject?: string[];
    cover_i?: number;
  }
  
  // Types for recommendation generation progress
  export interface ProgressState {
    stage: string;
    processed: number;
    total: number;
  }