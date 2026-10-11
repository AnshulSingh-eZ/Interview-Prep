import React, { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";

interface Question {
  id: string;
  number: number;
  category: string;
  text: string;
  difficulty?: number;
  is_followup?: boolean;
  answered?: boolean;
}

interface EvalResult {
  score: number;
  feedback: string;
  strengths: string[];
  weaknesses: string[];
  followups?: Question[];
}

const Interview: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);
  const [pendingFollowups, setPendingFollowups] = useState<Question[]>([]);
  const [finished, setFinished] = useState(false);

  const loadQuestions = useCallback(async () => {
    if (!sessionId) return;
    try {
      const data = await api<Question[]>(`/interview/${sessionId}/questions`, { method: "GET" });
      const list = Array.isArray(data) ? data : [];
      setQuestions(list);
      const openIdx = list.findIndex((q) => !q.answered);
      if (list.length && openIdx === -1) setFinished(true);
      else setCurrentIdx(openIdx < 0 ? 0 : openIdx);
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
    if (!currentQuestion || !answer.trim()) {
      setError("Write an answer before submitting.");
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
      setPendingFollowups(result.followups ?? []);
    } catch (err: any) {
      setError(err.message ?? "Failed to submit answer.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    const inserted = pendingFollowups.filter(
      (followup) => !questions.some((question) => question.id === followup.id)
    );
    const nextList = inserted.length
      ? [
          ...questions.slice(0, currentIdx + 1),
          ...inserted,
          ...questions.slice(currentIdx + 1),
        ].map((question, index) => ({ ...question, number: index + 1 }))
      : questions;

    if (inserted.length) setQuestions(nextList);
    setPendingFollowups([]);
    setEvalResult(null);
    setAnswer("");
    setError(null);

    if (currentIdx + 1 < nextList.length) setCurrentIdx((idx) => idx + 1);
    else setFinished(true);
  };

  if (loading) {
    return (
      <div className="page flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <div className="spinner" />
        <p>Preparing questions from your resume and job description…</p>
      </div>
    );
  }

  if (finished) {
    return (
      <div className="page flex min-h-[50vh] items-center justify-center">
        <div className="card max-w-lg space-y-4 p-8 text-center">
          <h1 className="text-3xl">Interview complete</h1>
          <p>You answered {questions.length} questions, including follow-ups based on your answers.</p>
          <button onClick={() => navigate(`/results/${sessionId}`)} className="btn-primary">
            View results
          </button>
        </div>
      </div>
    );
  }

  if (!questions.length) {
    return (
      <div className="page">
        <div className="card p-8 text-center">
          <h1 className="text-2xl">No questions yet</h1>
          <p className="mt-2">{error || "Start an interview from the practice page."}</p>
          <button onClick={() => navigate("/companies")} className="btn-primary mt-6">
            Back to practice
          </button>
        </div>
      </div>
    );
  }

  const current = questions[currentIdx];
  const progress = Math.round(((currentIdx + (evalResult ? 1 : 0)) / questions.length) * 100);

  return (
    <div className="page max-w-3xl space-y-5">
      <div>
        <div className="mb-2 flex items-center justify-between text-sm">
          <span>Question {currentIdx + 1} of {questions.length}</span>
          <span>{progress}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <article className="card">
        <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
          <div className="flex items-center gap-2">
            <span className="badge badge-primary">{current.category}</span>
            {current.is_followup && <span className="badge badge-accent">Follow-up</span>}
          </div>
          {current.difficulty != null && (
            <span className="text-xs text-slate-400">Difficulty {Math.round(current.difficulty)}</span>
          )}
        </div>
        <div className="px-6 py-6">
          <h1 className="text-2xl font-medium leading-snug">{current.text}</h1>
        </div>

        {!evalResult && (
          <div className="space-y-4 px-6 pb-6">
            <textarea
              id="answer-textarea"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              rows={7}
              placeholder="Answer in your own words. Follow-ups will dig into what you say."
            />
            <button id="submit-answer-btn" onClick={handleSubmit} disabled={submitting || !answer.trim()} className="btn-primary">
              {submitting ? "Evaluating and preparing follow-ups…" : "Submit answer"}
            </button>
          </div>
        )}
      </article>

      {evalResult && (
        <section className="card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg">Feedback</h2>
            <p className="text-2xl font-semibold text-white">{evalResult.score}/10</p>
          </div>
          <p className="text-slate-200">{evalResult.feedback}</p>
          {!!evalResult.strengths?.length && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-300">Strengths</p>
              <ul className="mt-2 space-y-1">
                {evalResult.strengths.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {!!evalResult.weaknesses?.length && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-rose-300">Work on</p>
              <ul className="mt-2 space-y-1">
                {evalResult.weaknesses.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          )}
          {pendingFollowups.length > 0 && (
            <p className="text-sm text-indigo-200">
              {pendingFollowups.length} follow-up {pendingFollowups.length === 1 ? "question" : "questions"} added from this answer.
            </p>
          )}
          <button id="next-question-btn" onClick={handleNext} className="btn-primary">
            {currentIdx + 1 < questions.length || pendingFollowups.length > 0 ? "Next question" : "View results"}
          </button>
        </section>
      )}
    </div>
  );
};

export default Interview;
