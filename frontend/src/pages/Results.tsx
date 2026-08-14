import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
} from "recharts";

interface ResultsData {
  overall_score: number;
  resume_score: number;
  behavioral_score: number;
  dsa_score: number;
  os_score: number;
  dbms_score: number;
  cn_score: number;
  weak_topics: string[];
  strong_topics: string[];
}

const scoreGradient = (score: number): string => {
  if (score >= 75) return "from-green-400 to-emerald-600";
  if (score >= 50) return "from-yellow-400 to-orange-500";
  return "from-red-400 to-rose-600";
};

const scoreLabel = (score: number): string => {
  if (score >= 75) return "Strong";
  if (score >= 50) return "Average";
  return "Needs Work";
};

interface ScoreCardProps {
  label: string;
  score: number;
}

const ScoreCard: React.FC<ScoreCardProps> = ({ label, score }) => {
  const gradient = scoreGradient(score);
  return (
    <div className="bg-white rounded-2xl shadow p-5 flex flex-col items-center gap-2">
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{label}</p>
      <div className={`text-3xl font-extrabold bg-gradient-to-r ${gradient} bg-clip-text text-transparent`}>
        {score}%
      </div>
      <span
        className={`text-xs font-medium px-2 py-0.5 rounded-full ${
          score >= 75
            ? "bg-green-100 text-green-700"
            : score >= 50
            ? "bg-yellow-100 text-yellow-700"
            : "bg-red-100 text-red-600"
        }`}
      >
        {scoreLabel(score)}
      </span>
      {/* Mini progress bar */}
      <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${gradient}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
};

const Results: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      if (!sessionId) return;
      try {
        const resp = await api<ResultsData>(`/interview/${sessionId}/results`, {
          method: "GET",
        });
        setData(resp);
      } catch (err: any) {
        setError(err.message ?? "Failed to load results.");
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, [sessionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500 font-medium">Computing your results…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <p className="text-5xl">📊</p>
          <p className="text-gray-600 font-medium">
            {error || "No results found for this session."}
          </p>
          <button
            onClick={() => navigate("/dashboard")}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const categories = [
    { name: "Resume", score: data.resume_score },
    { name: "Behavioral", score: data.behavioral_score },
    { name: "DSA", score: data.dsa_score },
    { name: "OS", score: data.os_score },
    { name: "DBMS", score: data.dbms_score },
    { name: "CN", score: data.cn_score },
  ];

  const radarData = categories.map((c) => ({ topic: c.name, score: c.score }));

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-extrabold text-gray-900">Interview Results</h1>
          <p className="mt-1 text-gray-500">Session: {sessionId?.slice(0, 8)}…</p>
        </div>
        <button
          onClick={() => navigate("/companies")}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition"
        >
          New Interview
        </button>
      </div>

      {/* Overall score hero */}
      <div className={`rounded-2xl bg-gradient-to-r ${scoreGradient(data.overall_score)} p-8 text-white text-center shadow-lg`}>
        <p className="text-sm font-semibold uppercase tracking-widest opacity-80 mb-2">Overall Score</p>
        <p className="text-7xl font-black">{data.overall_score}%</p>
        <p className="mt-3 text-lg font-medium opacity-90">{scoreLabel(data.overall_score)} Performance</p>
      </div>

      {/* Score cards grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {categories.map((c) => (
          <ScoreCard key={c.name} label={c.name} score={c.score} />
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Category Breakdown</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={categories} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value: number) => [`${value}%`, "Score"]}
                contentStyle={{ borderRadius: "8px", border: "1px solid #e5e7eb" }}
              />
              <Bar dataKey="score" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Radar Chart */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Skill Radar</h2>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#f0f0f0" />
              <PolarAngleAxis dataKey="topic" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9 }} />
              <Radar
                name="Score"
                dataKey="score"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.25}
              />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Strong / Weak topics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strong */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span className="text-green-500">✓</span> Strong Topics
          </h3>
          {data.strong_topics.length ? (
            <div className="flex flex-wrap gap-2">
              {data.strong_topics.map((t) => (
                <span
                  key={t}
                  className="bg-green-100 text-green-700 text-sm font-medium px-3 py-1 rounded-full"
                >
                  {t}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">
              Complete more interviews to identify your strong topics.
            </p>
          )}
        </div>

        {/* Weak */}
        <div className="bg-white rounded-2xl shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <span className="text-red-400">✗</span> Topics to Improve
          </h3>
          {data.weak_topics.length ? (
            <div className="flex flex-wrap gap-2">
              {data.weak_topics.map((t) => (
                <span
                  key={t}
                  className="bg-red-100 text-red-600 text-sm font-medium px-3 py-1 rounded-full"
                >
                  {t}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">
              Great job! No weak areas detected in this session.
            </p>
          )}
        </div>
      </div>

      {/* CTA */}
      <div className="bg-gradient-to-r from-blue-600 to-cyan-500 rounded-2xl p-6 text-white flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <p className="text-lg font-bold">Your next interview will be smarter.</p>
          <p className="text-sm opacity-80">
            The AI will prioritize your weak topics and adapt question difficulty.
          </p>
        </div>
        <button
          id="start-adaptive-interview"
          onClick={() => navigate("/companies")}
          className="shrink-0 px-6 py-3 bg-white text-blue-700 font-bold rounded-xl hover:bg-blue-50 transition"
        >
          Practice Again →
        </button>
      </div>
    </div>
  );
};

export default Results;
