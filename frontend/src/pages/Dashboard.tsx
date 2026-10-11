import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";

interface HistoryItem {
  session_id: string;
  company: string;
  score: number;
  created_at: string;
}

interface WeakTopic {
  topic: string;
  score: number;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const sessionId = localStorage.getItem("session_id");

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [weakTopics, setWeakTopics] = useState<WeakTopic[]>([]);
  const [histLoading, setHistLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [hist, weak] = await Promise.all([
          api<HistoryItem[]>("/dashboard/history", { method: "GET" }),
          api<{ weak_topics: WeakTopic[] }>("/dashboard/weak-topics", { method: "GET" }),
        ]);
        setHistory(Array.isArray(hist) ? hist : []);
        setWeakTopics(weak?.weak_topics ?? []);
      } catch {
        // Dashboard still renders if analytics are unavailable.
      } finally {
        setHistLoading(false);
      }
    };
    if (isAuthenticated) loadData();
    else setHistLoading(false);
  }, [isAuthenticated]);

  const avgScore =
    history.length > 0
      ? Math.round(history.reduce((sum, item) => sum + item.score, 0) / history.length)
      : null;

  const actions = [
    {
      id: "action-upload-resume",
      icon: "01",
      label: "Upload resume",
      desc: "Parse skills, projects, and experience",
      path: "/resume",
    },
    {
      id: "action-select-company",
      icon: "02",
      label: "Start practice",
      desc: "Pick a company and add the job description",
      path: "/companies",
    },
    {
      id: "action-continue-interview",
      icon: "03",
      label: sessionId ? "Continue interview" : "No active interview",
      desc: sessionId ? "Pick up the current session" : "Start one from Practice",
      path: sessionId ? `/interview/${sessionId}` : null,
    },
    {
      id: "action-view-results",
      icon: "04",
      label: "Latest results",
      desc: sessionId ? "Scores from the current session" : "Finish an interview first",
      path: sessionId ? `/results/${sessionId}` : null,
    },
  ];

  return (
    <div className="page space-y-8">
      <section className="card overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-500/30 to-pink-500/20 p-8">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-200">Interview Coach</p>
          <h1 className="mt-2 text-4xl">Prepare for the role you actually want.</h1>
          <p className="mt-3 max-w-2xl text-slate-300">
            Upload a resume, add a job description, and practice questions grounded in both.
          </p>
          {avgScore !== null && (
            <p className="mt-4 inline-block rounded-full bg-white/10 px-3 py-1 text-sm text-white">
              Average score {avgScore}% across {history.length} session{history.length === 1 ? "" : "s"}
            </p>
          )}
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {actions.map((action) => (
          <button
            key={action.id}
            id={action.id}
            disabled={!action.path}
            onClick={() => action.path && navigate(action.path)}
            className="card p-5 text-left transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <p className="text-xs font-semibold text-indigo-300">{action.icon}</p>
            <h2 className="mt-3 text-lg">{action.label}</h2>
            <p className="mt-1 text-sm">{action.desc}</p>
          </button>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="card p-6">
          <h2 className="text-lg">Weak topics</h2>
          {histLoading ? (
            <p className="mt-4 text-sm">Loading…</p>
          ) : weakTopics.length > 0 ? (
            <ul className="mt-4 space-y-2">
              {weakTopics.map((topic) => (
                <li key={topic.topic} className="flex items-center justify-between text-sm">
                  <span className="text-slate-200">{topic.topic}</span>
                  <span className="text-rose-300">{topic.score}%</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 text-sm">Complete an interview to see weak areas.</p>
          )}
        </div>

        <div className="card p-6 md:col-span-2">
          <h2 className="text-lg">Recent interviews</h2>
          {histLoading ? (
            <p className="mt-4 text-sm">Loading…</p>
          ) : history.length > 0 ? (
            <div className="mt-3 overflow-x-auto">
              <table>
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Score</th>
                    <th>Date</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(0, 5).map((item) => (
                    <tr key={item.session_id}>
                      <td className="text-slate-100">{item.company}</td>
                      <td>{item.score}%</td>
                      <td>{new Date(item.created_at).toLocaleDateString()}</td>
                      <td>
                        <button
                          onClick={() => navigate(`/results/${item.session_id}`)}
                          className="text-sm text-indigo-300"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mt-4 text-sm">No interviews yet. Start one from Practice.</p>
          )}
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
