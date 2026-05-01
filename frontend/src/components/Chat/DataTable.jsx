import React from 'react';

const DataTable = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) return null;

  return (
    <div className="overflow-x-auto w-full border border-white/10 rounded-xl bg-[#0F172A]/80 backdrop-blur-md custom-scrollbar shadow-xl mt-3">
      <table className="min-w-full divide-y divide-white/5 text-[11px]">
        <thead className="bg-black/40">
          <tr>
            {Object.keys(data[0]).map((key) => (
              <th key={key} className="px-4 py-2.5 text-left font-bold text-gray-500 uppercase tracking-[0.15em] text-[9px]">
                {key.replace('_', ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {data.slice(0, 10).map((row, rIdx) => (
            <tr key={rIdx} className="hover:bg-white/[0.03] transition-all duration-150 group">
              {Object.values(row).map((val, cIdx) => (
                <td key={cIdx} className="px-4 py-2 text-gray-300 font-medium whitespace-nowrap">
                  {typeof val === 'number' && !Number.isInteger(val) ? val.toFixed(2) : val?.toString() || '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>


  );
};

export default DataTable;
