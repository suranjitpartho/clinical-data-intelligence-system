import React from 'react';

const DataTable = ({ data }) => {
  if (!data || !Array.isArray(data) || data.length === 0) return null;

  return (
    <div className="overflow-x-auto w-full border border-gray-100 rounded-lg bg-white custom-scrollbar">
      <table className="min-w-full divide-y divide-gray-100 text-[11px]">
        <thead className="bg-gray-50">
          <tr>
            {Object.keys(data[0]).map((key) => (
              <th key={key} className="px-3 py-2 text-left font-bold text-gray-400 uppercase tracking-wider">
                {key.replace('_', ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {data.slice(0, 10).map((row, rIdx) => (
            <tr key={rIdx} className="hover:bg-gray-50/50 transition-colors">
              {Object.values(row).map((val, cIdx) => (
                <td key={cIdx} className="px-3 py-2 text-gray-600 font-medium whitespace-nowrap">
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
