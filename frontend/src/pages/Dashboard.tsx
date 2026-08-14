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
        // Non-critical: dashboard still shows without analytics
      } finally {
        setHistLoading(false);
      }
    };
    if (isAuthenticated) loadData();
    else setHistLoading(false);
  }, [isAuthenticated]);

  const latestSession = history[0];
  const avgScore =
    history.length > 0
      ? Math.round(history.reduce((s, h) => s + h.score, 0) / history.length)
      : null;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl p-8 text-white shadow-lg">
        <h1 className="text-3xl font-extrabold">Interview Intelligence Platform</h1>
        <p className="mt-2 opacity-85 text-lg">
          {isAuthenticated
            ? "Your AI-powered interview coach is ready."
            : "Please log in to continue."}
        </p>
        {avgScore !== null && (
          <p className="mt-3 text-sm font-medium bg-white/20 inline-block px-3 py-1 rounded-full">
            Average Score: {avgScore}% across {history.length} session{history.length !== 1 ? "s" : ""}
          </p>
        )}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            {
              id: "action-upload-resume",
              icon: "📄",
              label: "Upload Resume",
              desc: "Parse your resume for tailored questions",
              path: "/resume",
              gradient: "from-purple-500 to-indigo-500",
              disabled: false,
            },
            {
              id: "action-select-company",
              icon: "🏢",
              label: "Select Company",
              desc: "Choose a company to mock interview",
              path: "/companies",
              gradient: "from-blue-500 to-cyan-500",
              disabled: false,
            },
            {
              id: "action-continue-interview",
              icon: "🎯",
              label: sessionId ? "Continue Interview" : "Start Interview",
              desc: sessionId ? "Resume your active session" : "Select a company first",
              path: sessionId ? `/interview/${sessionId}` : null,
              gradient: "from-green-500 to-emerald-500",
              disabled: !sessionId,
            },
            {
              id: "action-view-results",
              icon: "📊",
              label: "View Results",
              desc: sessionId ? "See your latest session results" : "No session yet",
              path: sessionId ? `/results/${sessionId}` : null,
              gradient: "from-orange-500 to-rose-500",
              disabled: !sessionId,
            },
          ].map((action) => (
            <button
              key={action.id}
              id={action.id}
              onClick={() => action.path && navigate(action.path)}
              disabled={action.disabled}
              className={`group relative overflow-hidden rounded-2xl p-5 text-left shadow transition-all duration-200
                ${action.disabled
                  ? "bg-gray-100 cursor-not-allowed opacity-60"
                  : "bg-white hover:shadow-lg hover:-translate-y-0.5 active:scale-95 cursor-pointer"
                }`}
            >
              {!action.disabled && (
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${action.gradient} opacity-0 group-hover:opacity-5 transition-opacity`}
                />
              )}
              <div className="text-3xl mb-3">{action.icon}</div>
              <h3 className="font-semibold text-gray-900">{action.label}</h3>
              <p className="text-xs text-gray-500 mt-1">{action.desc}</p>
              {!action.disabled && (
                <div
                  className={`mt-3 text-xs font-semibold bg-gradient-to-r ${action.gradient} bg-clip-text text-transparent`}
                >
                  Go →
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Weak Topics */}
        <div className="bg-white rounded-2xl shadow p-6 space-y-3">
          <h3 className="text-lg font-bold text-gray-900">Weak Topics</h3>
          {histLoading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-4 bg-gray-100 rounded w-3/4" />
              <div className="h-4 bg-gray-100 rounded w-1/2" />
            </div>
          ) : weakTopics.length > 0 ? (
            <ul className="space-y-2">
              {weakTopics.map((wt) => (
                <li key={wt.topic} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">{wt.topic}</span>
                  <span className="text-red-500 font-semibold">{wt.score}%</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-400 text-sm">
              Complete an interview to see your weak areas.
            </p>
          )}
        </div>

        {/* Interview History */}
        <div className="bg-white rounded-2xl shadow p-6 col-span-1 md:col-span-2 space-y-3">
          <h3 className="text-lg font-bold text-gray-900">Recent Interviews</h3>
          {histLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2].map((i) => (
                <div key={i} className="h-10 bg-gray-100 rounded-lg" />
              ))}
            </div>
          ) : history.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 text-xs uppercase tracking-wide border-b border-gray-100">
                    <th className="text-left py-2 pr-4">Company</th>
                    <th className="text-left py-2 pr-4">Score</th>
                    <th className="text-left py-2">Date</th>
                    <th className="text-left py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(0, 5).map((h) => (
                    <tr key={h.session_id} className="border-b border-gray-50 hover:bg-gray-50 transition">
                      <td className="py-2.5 pr-4 font-medium text-gray-900">{h.company}</td>
                      <td className="py-2.5 pr-4">
                        <span
                          className={`font-semibold ${
                            h.score >= 75
                              ? "text-green-600"
                              : h.score >= 50
                              ? "text-yellow-600"
                              : "text-red-500"
                          }`}
                        >
                          {h.score}%
                        </span>
                      </td>
                      <td className="py-2.5 text-gray-500">
                        {new Date(h.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-2.5">
                        <button
                          onClick={() => navigate(`/results/${h.session_id}`)}
                          className="text-blue-500 hover:text-blue-700 text-xs font-medium"
                        >
                          View →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-400 text-sm">
              No interviews yet. Select a company to get started!
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
