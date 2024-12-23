import React from 'react';

interface LibraryFinderProps {
  title: string;
  author: string;
}

const LibraryFinder: React.FC<LibraryFinderProps> = ({ title, author }) => {
  const worldcatUrl = `https://www.worldcat.org/search?q=${encodeURIComponent(title)}+${encodeURIComponent(author)}`;
  const openlibraryUrl = `https://openlibrary.org/search?q=${encodeURIComponent(title)}+${encodeURIComponent(author)}`;

  return (
    <div className="mt-4 space-y-2">
      <h4 className="text-sm font-medium text-gray-800">📚 Find this book:</h4>
      <div className="space-x-4">
        <a 
          href={worldcatUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Search WorldCat Libraries
        </a>
        <a 
          href={openlibraryUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Search OpenLibrary
        </a>
      </div>
    </div>
  );
};

export default LibraryFinder;