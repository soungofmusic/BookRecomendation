// Cache service for API responses and images
class CacheService {
    private cache: Map<string, { data: any; timestamp: number }> = new Map();
    private readonly CACHE_DURATION = 1000 * 60 * 30; // 30 minutes
  
    set(key: string, data: any): void {
      this.cache.set(key, {
        data,
        timestamp: Date.now()
      });
    }
  
    get<T>(key: string): T | null {
      const item = this.cache.get(key);
      if (!item) return null;
  
      if (Date.now() - item.timestamp > this.CACHE_DURATION) {
        this.cache.delete(key);
        return null;
      }
  
      return item.data as T;
    }
  
    clear(): void {
      this.cache.clear();
    }
  }
  
  export const cacheService = new CacheService();
  
  // Image preloading utility
  export const preloadImage = (src: string): Promise<string> => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.src = src;
      img.onload = () => resolve(src);
      img.onerror = () => reject(new Error(`Failed to load image: ${src}`));
    });
  };