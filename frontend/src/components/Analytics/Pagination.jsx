import React from 'react';
import { ChevronRight, ChevronLeft } from 'lucide-react';

const Pagination = ({ pagination, currentPage, onPageChange }) => {
  if (pagination.total_pages <= 1) return null;

  return (
    <div className="flex items-center justify-between pt-6 border-t border-white/5 mt-6">
      <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest">
        Showing {((pagination.current_page - 1) * pagination.page_size) + 1}–{Math.min(pagination.current_page * pagination.page_size, pagination.total_items)} of {pagination.total_items}
      </p>
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className="w-8 h-8 flex items-center justify-center rounded-md bg-white/5 border border-white/10 text-gray-400 hover:border-clinical-blue/40 hover:text-clinical-blue disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200"
        >
          <ChevronLeft size={14} />
        </button>

        {Array.from({ length: pagination.total_pages }, (_, i) => i + 1)
          .filter(p => p === 1 || p === pagination.total_pages || Math.abs(p - currentPage) <= 1)
          .reduce((acc, p, idx, arr) => {
            if (idx > 0 && p - arr[idx - 1] > 1) acc.push('...');
            acc.push(p);
            return acc;
          }, [])
          .map((p, i) =>
            p === '...' ? (
              <span key={`ellipsis-${i}`} className="text-[10px] text-gray-600 px-1">···</span>
            ) : (
              <button
                key={p}
                onClick={() => onPageChange(p)}
                className={`w-8 h-8 flex items-center justify-center rounded-md text-[11px] font-bold border transition-all duration-200 ${
                  currentPage === p
                    ? 'bg-clinical-blue text-slate-900 border-clinical-blue shadow-[0_0_10px_rgba(0,200,255,0.2)]'
                    : 'bg-white/5 text-gray-400 border-white/10 hover:border-clinical-blue/40 hover:text-clinical-blue'
                }`}
              >
                {p}
              </button>
            )
          )
        }

        <button
          onClick={() => onPageChange(Math.min(pagination.total_pages, currentPage + 1))}
          disabled={currentPage === pagination.total_pages}
          className="w-8 h-8 flex items-center justify-center rounded-md bg-white/5 border border-white/10 text-gray-400 hover:border-clinical-blue/40 hover:text-clinical-blue disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200"
        >
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
};

export default Pagination;
