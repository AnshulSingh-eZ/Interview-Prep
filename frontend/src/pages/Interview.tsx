import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../services/api";

interface Question {
  id: string;
  number: number;
  category: string;
  text: string;
  difficulty?: number;
}

interface EvalResult {
  score: number;
  feedback: string;
  strengths: string[];
  weaknesses: string[];
}

const CATEGORY_COLORS: Record<string, string> = {
  Resume: "bg-purple-100 text-purple-700",
  Behavioral: "bg-green-100 text-green-700",
  DSA: "bg-blue-100 text-blue-700",
  OS: "bg-orange-100 text-orange-700",
  DBMS: "bg-red-100 text-red-700",
  CN: "bg-cyan-100 text-cyan-700",
  General: "bg-gray-100 text-gray-700",
};

// Available interview modes
const INTERVIEW_MODES = [
  "Behavioural",
  "Technical DSA",
  "Core CS Fundamentals",
  "System Design",
  "Projects / Resume Discussion",
];

const scoreColor = (score: number) => {
  if (score >= 7.5) return "text-green-600";
  if (score >= 5) return "text-yellow-600";
  return "text-red-600";
};

const Interview: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIdx, setCurrentIdx] = useState<number>(0);
  const [answer, setAnswer] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);
  const [finished, setFinished] = useState<boolean>(false);
// Track current mode and attempts per mode
const [currentMode, setCurrentMode] = useState<string>("Behavioural");
  const [attemptsMap, setAttemptsMap] = useState<Record<string, number>>({});

  // Track completed checkmarks for Technical DSA and System Design modes
  const [completedMap, setCompletedMap] = useState<Record<string, boolean>>({});

  const toggleCompleted = (qid: string) => {
    setCompletedMap((prev) => ({ ...prev, [qid]: !prev[qid] }));
  };

  // Helper to fetch mode‑specific questions from the backend
  const fetchModeQuestions = async (mode: string) => {
    try {
      const data = await api<any>(`/interview/${sessionId}/mode_questions?mode=${encodeURIComponent(mode)}`, {
        method: "GET",
      });
      // Expect same shape as generic questions
      setQuestions(data);
    } catch (err) {
      console.error("Failed to fetch mode questions", err);
    }
  };

// Mapping from interview mode to question category keywords
const MODE_CATEGORY_MAP: Record<string, string[]> = {
  Behavioural: ["Behavioural", "Behavioral"],
  "Technical DSA": ["DSA", "Technical DSA"],
  "Core CS Fundamentals": ["Core", "CS Fundamentals"],
  "System Design": ["System Design"],
  "Projects / Resume Discussion": ["Resume", "Projects"],
};

// Filtered questions based on selected mode
const [filteredQuestions, setFilteredQuestions] = useState<Question[]>([]);

// Update filtered questions whenever mode or full question list changes
useEffect(() => {
  const keywords = MODE_CATEGORY_MAP[currentMode] || [];
  const filtered = questions.filter((q) =>
    keywords.some((kw) => q.category.toLowerCase().includes(kw.toLowerCase()))
  );
  let limited = filtered.length ? filtered : questions;
  if (currentMode === 'Technical DSA') {
    limited = limited.slice(0, 10);
  } else if (currentMode === 'System Design') {
    limited = limited.slice(0, 5);
  }
  setFilteredQuestions(limited);
  setCurrentIdx(0); // reset to first question of filtered set
}, [questions, currentMode]);


  // Load questions: prefer localStorage cache (set by Companies.tsx on start),
  // then fall back to GET /interview/:sessionId/questions
  const loadQuestions = useCallback(async () => {
    if (!sessionId) return;

    // Try cache first
    const cached = localStorage.getItem(`questions_${sessionId}`);
    if (cached) {
      try {
        const parsed: Question[] = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setQuestions(parsed);
          setLoading(false);
          return;
        }
      } catch {
        // ignore parse error, fall through to fetch
      }
    }

    // Fetch from API
    try {
      const data = await api<Question[]>(`/interview/${sessionId}/questions`, {
        method: "GET",
      });
      setQuestions(data);
    } catch (err: any) {
      setError(err.message ?? "Failed to load interview questions.");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadQuestions();
  }, [loadQuestions]);

  const handleSubmit = async () => {
    const currentQuestion = questions[currentIdx];
    if (!answer.trim()) {
      setError("Please write your answer before submitting.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const result = await api<EvalResult>(`/interview/${sessionId}/answer`, {
  method: "POST",
  body: JSON.stringify({
    question_id: currentQuestion.id,
    answer: answer.trim(),
  }),
});
setEvalResult(result);
// Increment attempts for the current mode
setAttemptsMap((prev) => ({
  ...prev,
  [currentMode]: (prev[currentMode] || 0) + 1,
}));
    } catch (err: any) {
      setError(err.message ?? "Failed to submit answer.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
      setEvalResult(null);
      setAnswer("");
      setError(null);
      if (currentIdx + 1 < filteredQuestions.length) {
        setCurrentIdx((i) => i + 1);
      } else {
        setFinished(true);
      }
    };

  const goToResults = () => {
    navigate(`/results/${sessionId}`);
  };

  // ── Loading ────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500 font-medium">Generating your interview questions…</p>
        </div>
      </div>
    );
  }

  // ── Finished ───────────────────────────────────────────────────────────────
  if (finished) {
      return (
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="card mx-auto max-w-md w-full text-center space-y-4">
            <div className="text-6xl">🎉</div>
            <h1 className="text-2xl font-bold text-gray-900">Interview Complete!</h1>
            <p className="text-gray-500">
              You've answered all {filteredQuestions.length} questions. Check your results to see detailed feedback and your readiness score.
            </p>
            <button
              id="view-results-btn"
              onClick={goToResults}
              className="w-full py-3 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition"
            >
              View Results →
            </button>
          </div>
        </div>
      );
    }

  // ── Error ──────────────────────────────────────────────────────────────────
  if (!filteredQuestions.length) {
      return (
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-3">
            <p className="text-5xl">😕</p>
            <p className="text-gray-600 font-medium">No questions found for this mode.</p>
            {error && <p className="text-red-500 text-sm">{error}</p>}
          </div>
        </div>
      );
    }

  const currentQuestion = filteredQuestions[currentIdx];
  const progressPercent = Math.round(((currentIdx + 1) / filteredQuestions.length) * 100);
  const categoryClass = CATEGORY_COLORS[currentQuestion.category] || CATEGORY_COLORS.General;




  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Progress Bar */}
      <div>
        <div className="flex justify-between text-sm text-gray-500 mb-1">
          <span>Question {currentIdx + 1}</span>
          <span>Mode: {currentMode}</span>
          <span>Total attempted: {attemptsMap[currentMode] || 0}</span>
        </div>


{/* Mode Buttons */}
<div className="flex items-center gap-4 mt-2">
  {INTERVIEW_MODES.map((mode) => (
    <button
      key={mode}
      onClick={async () => {
        const newMode = mode;
        await api<any>(`/interview/${sessionId}/mode`, {
          method: "PATCH",
          body: JSON.stringify({ mode: newMode.toUpperCase().replace(/ /g, "_") }),
        });
        setCurrentMode(newMode);
        // Fetch dedicated questions for the selected mode
        await fetchModeQuestions(newMode);
      }}
      className={`px-3 py-1 rounded mr-2 transition-colors ${
        mode === currentMode ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800 hover:bg-gray-300"
      }`}
    >
      {mode}
    </button>
  ))}
</div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm flex gap-2 items-center">
          <span>⚠</span> {error}
        </div>
      )}

      {/* Question Card */}
      <div className="card">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${categoryClass}`}>
            {currentQuestion.category}
          </span>
          {currentQuestion.difficulty != null && (
            <span className="text-xs text-gray-400">
              Difficulty: {currentQuestion.difficulty}/100
            </span>
          )}
        </div>

        {/* Question text */}
        <div className="px-6 py-6">
          <p className="text-gray-900 text-lg font-medium leading-relaxed">
            {currentQuestion.text}
          </p>
          {/* Completion checkbox for Technical DSA and System Design */}
          {(currentMode === 'Technical DSA' || currentMode === 'System Design') && (
            <div className="flex items-center mt-4">
              <input
                type="checkbox"
                checked={!!completedMap[currentQuestion.id]}
                onChange={() => toggleCompleted(currentQuestion.id)}
                className="mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded"
              />
              <label className="text-sm text-gray-700">Mark as completed</label>
            </div>
          )}
        </div>

        {/* Answer area — hide after evaluation */}
        {!evalResult && (
          <div className="px-6 pb-6 space-y-4">
            <textarea
              id="answer-textarea"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={7}
              placeholder="Type your detailed answer here…"
              className="w-full p-4 border border-gray-200 rounded-xl text-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
            />
            <button id="submit-answer-btn" onClick={handleSubmit} disabled={submitting || !answer.trim()} className="btn-primary w-full">
              {submitting ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Evaluating…
                </span>
              ) : (
                "Submit Answer"
              )}
            </button>
          </div>
        )}
      </div>

      {/* Evaluation Feedback */}
      {evalResult && (
        <div className="card animate-fade-in">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">AI Feedback</h3>
            <span className={`text-2xl font-bold ${scoreColor(evalResult.score)}`}>
              {evalResult.score}/10
            </span>
          </div>

          <div className="px-6 py-5 space-y-4">
            {/* Feedback */}
            <p className="text-gray-700 text-sm leading-relaxed">{evalResult.feedback}</p>

            {/* Strengths */}
            {evalResult.strengths?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-2">
                  ✓ Strengths
                </p>
                <ul className="space-y-1">
                  {evalResult.strengths.map((s, i) => (
                    <li key={i} className="text-sm text-gray-700 flex gap-2">
                      <span className="text-green-500 shrink-0">•</span> {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Weaknesses */}
            {evalResult.weaknesses?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-red-700 uppercase tracking-wide mb-2">
                  ✗ Areas to Improve
                </p>
                <ul className="space-y-1">
                  {evalResult.weaknesses.map((w, i) => (
                    <li key={i} className="text-sm text-gray-700 flex gap-2">
                      <span className="text-red-400 shrink-0">•</span> {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Next / Finish */}
            <button id="next-question-btn" onClick={handleNext} className="mt-2 btn-primary w-full">
              {currentIdx + 1 < questions.length ? "Next Question →" : "View Results →"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Interview;
