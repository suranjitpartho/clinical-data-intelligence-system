import React from 'react';

/**
 * Renders clinical markdown with specific brand styling for headers and bold text.
 */
export const renderMarkdown = (text, isError = false) => {
  if (!text) return null;
  
  const lines = text.split('\n');
  
  return lines.map((line, i) => {
    if (line.startsWith('###')) {
      return <h3 key={i} className={`${isError ? 'text-red-300' : 'text-clinical-blue'} font-bold text-sm mt-4 mb-2`}>{line.replace('###', '').trim()}</h3>;
    }
    if (line.startsWith('##')) {
      return <h2 key={i} className={`${isError ? 'text-red-300' : 'text-clinical-blue'} font-bold text-base mt-6 mb-3`}>{line.replace('##', '').trim()}</h2>;
    }
    
    const parts = line.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    const renderedLine = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j} className={`font-bold ${isError ? 'text-red-300' : 'text-gray-300'}`}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return <em key={j} className="italic">{part.slice(1, -1)}</em>;
      }
      return part;
    });

    return <p key={i} className={`mb-4 last:mb-0 ${isError ? 'text-red-300/80 italic text-[11px]' : 'text-[13px]'}`}>{renderedLine}</p>;
  });
};
