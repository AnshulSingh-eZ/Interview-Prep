import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../services/api";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
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

const Results: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      if (!sessionId) return;
      try {
        setData(await api<ResultsData>(`/interview/${sessionId}/results`, { method: "GET" }));
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
      <div className="page flex min-h-[50vh] items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page">
        <div className="card mx-auto max-w-lg p-8 text-center">
          <h1 className="text-2xl">Results unavailable</h1>
          <p className="mt-2">{error || "No results found for this session."}</p>
          <button onClick={() => navigate("/dashboard")} className="btn-primary mt-6">
            Back to dashboard
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

  return (
    <div className="page space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl">Interview results</h1>
          <p className="mt-1 text-sm">Session {sessionId?.slice(0, 8)}</p>
        </div>
        <button onClick={() => navigate("/companies")} className="btn-ghost">
          New interview
        </button>
      </div>

      <section className="card bg-gradient-to-r from-indigo-500/25 to-pink-500/20 p-8 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-200">Overall</p>
        <p className="mt-2 text-6xl font-semibold text-white">{data.overall_score}%</p>
      </section>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {categories.map((category) => (
          <div key={category.name} className="card p-4 text-center">
            <p className="text-xs uppercase tracking-wide">{category.name}</p>
            <p className="mt-2 text-2xl font-semibold text-white">{category.score}%</p>
          </div>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="card p-5">
          <h2 className="mb-4 text-lg">Category breakdown</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={categories}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="score" fill="#818cf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-5">
          <h2 className="mb-4 text-lg">Skill radar</h2>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={categories.map((c) => ({ topic: c.name, score: c.score }))}>
              <PolarGrid />
              <PolarAngleAxis dataKey="topic" />
              <PolarRadiusAxis domain={[0, 100]} />
              <Radar dataKey="score" stroke="#818cf8" fill="#818cf8" fillOpacity={0.35} />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="card p-5">
          <h2 className="text-lg">Strong topics</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {data.strong_topics.length ? (
              data.strong_topics.map((topic) => (
                <span key={topic} className="badge badge-success">{topic}</span>
              ))
            ) : (
              <p className="text-sm">None scored high enough yet.</p>
            )}
          </div>
        </div>
        <div className="card p-5">
          <h2 className="text-lg">Topics to improve</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {data.weak_topics.length ? (
              data.weak_topics.map((topic) => (
                <span key={topic} className="badge badge-error">{topic}</span>
              ))
            ) : (
              <p className="text-sm">No weak areas in the categories you answered.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Results;
