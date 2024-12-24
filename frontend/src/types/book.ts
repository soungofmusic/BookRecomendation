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
  why_read?: string;
}

export interface FilterState {
  genre: string;
  yearRange: [number, number];
  minScore: number;
}

export interface RecommendationsProps {
  recommendations: (Book | null)[];
  isLoading: boolean;
}

export interface TooltipProps {
  content: string;
  children: React.ReactNode;
}

export interface ApiResponse {
  status: 'processing' | 'completed' | 'error';
  recommendations?: Book[];
  error?: string;
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