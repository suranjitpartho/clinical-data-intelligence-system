import React from 'react';

/**
 * Renders clinical markdown with specific brand styling for headers and bold text.
 */
export const renderMarkdown = (text) => {
  if (!text) return null;
  
  const lines = text.split('\n');
  
  return lines.map((line, i) => {
    if (line.startsWith('###')) {
      return <h3 key={i} className="text-clinical-blue font-bold text-lg mt-6 mb-2">{line.replace('###', '').trim()}</h3>;
    }
    if (line.startsWith('##')) {
      return <h2 key={i} className="text-clinical-blue font-bold text-xl mt-8 mb-3">{line.replace('##', '').trim()}</h2>;
    }
    
    const parts = line.split(/(\*\*.*?\*\*)/g);
    const renderedLine = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j} className="font-bold text-dark-grey">{part.slice(2, -2)}</strong>;
      }
      return part;
    });

    return <p key={i} className="mb-3">{renderedLine}</p>;
  });
};
