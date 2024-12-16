interface ProgressData {
    status: 'processing' | 'completed';
    stage?: string;
    processed?: number;
    total?: number;
    recommendations: any[];
    error?: string;
  }
  
  export const getRecommendations = async (
    books: string[], 
    onProgress: (data: ProgressData) => void,
    onError: (error: string) => void
  ) => {
    try {
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ books }),
      });
  
      if (!response.ok) {
        throw new Error('Network response was not ok');
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
              const jsonData = JSON.parse(line.slice(6));
              onProgress(jsonData);
            } catch (e) {
              console.error('Error parsing JSON:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      onError(error instanceof Error ? error.message : 'An error occurred');
    }
  };