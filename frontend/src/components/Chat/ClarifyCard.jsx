import React, { useState } from 'react';
import { HelpCircle, Send, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';

const ClarifyCard = ({ questions, onSubmit }) => {
  const [answers, setAnswers] = useState({});
  const [customInputs, setCustomInputs] = useState({});
  const [currentTab, setCurrentTab] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSelect = (qId, value) => {
    setAnswers(prev => ({ ...prev, [qId]: value }));
    setError('');
  };

  const handleCustomChange = (qId, value) => {
    setCustomInputs(prev => ({ ...prev, [qId]: value }));
  };

  const handleNext = () => {
    if (!answers[questions[currentTab]?.id]) {
      setError('Please select an option to continue.');
      return;
    }
    setError('');
    if (currentTab < questions.length - 1) {
      setCurrentTab(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setError('');
    setCurrentTab(prev => Math.max(0, prev - 1));
  };

  const handleSubmit = async () => {
    const missing = questions.filter(q => {
      const a = answers[q.id];
      return !a || (a === 'Other (specify)' && !customInputs[q.id]?.trim());
    });
    if (missing.length > 0) {
      setError('Please answer all questions before submitting.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const formatted = questions.map(q => ({
        id: q.id,
        question: q.question,
        answer: answers[q.id] === 'Other (specify)' ? customInputs[q.id] : answers[q.id],
      }));
      await onSubmit(formatted);
    } catch (err) {
      setError('Failed to submit. Please try again.');
      setSubmitting(false);
    }
  };

  if (!questions || questions.length === 0) return null;

  const q = questions[currentTab];
  const isLast = currentTab === questions.length - 1;

  return (
    <div className="w-full border border-white/10 rounded-xl bg-[#0F172A]/90 backdrop-blur-md shadow-xl mt-2 animate-fade-in-up overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2.5 bg-white/[0.03] border-b border-white/5">
        <HelpCircle size={14} className="text-gray-500" />
        <span className="text-[10px] font-bold uppercase tracking-wider text-gray-500">
          Clarify your query
        </span>
      </div>

      <div className="flex items-center gap-1 px-4 pt-2 pb-1">
        {questions.map((_, idx) => (
          <div
            key={idx}
            className={`h-1 flex-1 rounded-full transition-all ${
              idx === currentTab ? 'bg-clinical-blue/40' : 'bg-white/10'
            }`}
          />
        ))}
        <span className="text-[9px] text-gray-600 font-medium ml-2">
          {currentTab + 1}/{questions.length}
        </span>
      </div>

      <div className="px-4 py-2 min-h-[110px]">
        <label className="block text-[12px] font-medium text-gray-300 mb-2.5">
          <span className="text-gray-500 mr-1.5">Q{currentTab + 1}.</span>
          {q.question}
        </label>

        {q.type === 'choice' ? (
          <div className="space-y-1">
            {(() => {
              const opts = q.options || [];
              const hasOther = opts.some(o => /other|custom/i.test(o));
              return hasOther ? opts : [...opts, 'Other (specify)'];
            })().map(opt => (
              <label
                key={opt}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-md border cursor-pointer transition-all ${
                  answers[q.id] === opt
                    ? 'border-clinical-blue/30 bg-clinical-blue/[0.06] text-white'
                    : 'border-white/5 bg-white/[0.02] text-gray-500 hover:border-clinical-blue/30 hover:text-clinical-blue'
                }`}
              >
                <input
                  type="radio"
                  name={q.id}
                  value={opt}
                  checked={answers[q.id] === opt}
                  onChange={() => handleSelect(q.id, opt)}
                  className="appearance-none w-3 h-3 rounded-full border border-white/10 checked:border-clinical-blue/40 checked:bg-clinical-blue/40 transition-all shrink-0 mt-0.5"
                />
                <span className="text-[11px] font-medium">{opt}</span>
              </label>
            ))}
            {answers[q.id] === 'Other (specify)' && (
              <input
                type="text"
                placeholder="Enter custom value..."
                value={customInputs[q.id] || ''}
                onChange={e => handleCustomChange(q.id, e.target.value)}
                className="w-full mt-1 px-3 py-1.5 bg-slate-900/60 border border-white/10 rounded-md text-[11px] text-gray-200 focus:outline-none focus:border-clinical-blue/40"
              />
            )}
          </div>
        ) : q.type === 'date' ? (
          <input
            type="date"
            value={answers[q.id] || ''}
            onChange={e => handleSelect(q.id, e.target.value)}
            className="w-full px-3 py-1.5 bg-slate-900/60 border border-white/10 rounded-md text-[11px] text-gray-200 focus:outline-none focus:border-clinical-blue/40"
          />
        ) : (
          <textarea
            rows={2}
            placeholder="Type your answer..."
            value={answers[q.id] || ''}
            onChange={e => handleSelect(q.id, e.target.value)}
            className="w-full px-3 py-1.5 bg-slate-900/60 border border-white/10 rounded-md text-[11px] text-gray-200 focus:outline-none focus:border-clinical-blue/40 resize-none"
          />
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 pb-1">
          <AlertCircle size={11} className="text-red-400 shrink-0" />
          <span className="text-[10px] text-red-400">{error}</span>
        </div>
      )}

      <div className="flex items-center justify-between px-4 py-2 border-t border-white/5">
        <button
          onClick={handleBack}
          disabled={currentTab === 0}
          className="flex items-center gap-1 px-2.5 py-1.5 text-[10px] text-gray-500 hover:text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
        >
          <ChevronLeft size={12} />
          Back
        </button>

        {isLast ? (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="flex items-center gap-2 px-4 py-1.5 bg-clinical-blue text-slate-950 rounded-md text-[11px] font-bold hover:bg-clinical-blue/80 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {submitting ? (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-slate-950/30 border-t-slate-950 rounded-full animate-spin" />
                Submitting...
              </span>
            ) : (
              <>
                <Send size={14} fill="currentColor" />
                Submit Answers
              </>
            )}
          </button>
        ) : (
          <button
            onClick={handleNext}
            className="flex items-center gap-1 px-3 py-1.5 bg-white/10 rounded-md text-[10px] font-medium text-gray-300 hover:bg-white/20 transition-all"
          >
            Next
            <ChevronRight size={12} />
          </button>
        )}
      </div>
    </div>
  );
};

export default ClarifyCard;