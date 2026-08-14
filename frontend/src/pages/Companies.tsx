import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

interface Company {
  id: string;
  name: string;
  focus_topics: string[];
  weight_distribution: {
    behavioral: number;
    resume: number;
    dsa: number;
    cs_fundamentals: number;
  };
  created_at: string;
}

// Map backend flat response to nested weight_distribution
function mapCompany(raw: any): Company {
  return {
    id: String(raw.id),
    name: raw.name,
    focus_topics: Array.isArray(raw.focus_topics) ? raw.focus_topics : [],
    weight_distribution: {
      behavioral: raw.weight_distribution?.behavioral ?? raw.behavioral_weight ?? 0,
      resume: raw.weight_distribution?.resume ?? raw.resume_weight ?? 0,
      dsa: raw.weight_distribution?.dsa ?? raw.dsa_weight ?? 0,
      cs_fundamentals: raw.weight_distribution?.cs_fundamentals ?? raw.cs_weight ?? 0,
    },
    created_at: raw.created_at ?? "",
  };
}

const COMPANY_COLORS: Record<string, string> = {
  Amazon: "from-orange-500 to-yellow-400",
  Google: "from-blue-500 to-green-400",
  Microsoft: "from-blue-600 to-cyan-400",
  Adobe: "from-red-600 to-orange-400",
  Atlassian: "from-blue-700 to-blue-400",
  Uber: "from-gray-800 to-gray-600",
  Walmart: "from-blue-500 to-yellow-400",
  Apple: "from-gray-700 to-gray-400",
  "Goldman Sachs": "from-sky-700 to-sky-400",
  Flipkart: "from-yellow-500 to-orange-400",
};

const Companies: React.FC = () => {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState<string | null>(null); // company id being started (unused now)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const data = await api<any[]>("/companies/", { method: "GET" });
        setCompanies(data.map(mapCompany));
      } catch (err: any) {
        setError(err.message || "Failed to load companies. Please try again.");
      } finally {
        setLoading(false);
      }
    };
    fetchCompanies();
  }, []);

  const startInterview = async () => {
    if (selectedIds.size === 0) {
      setError("Select at least one company to start the interview.");
      return;
    }
    setStarting("starting");
    setError(null);
    try {
      const result = await api<{ session_id: string; questions: any[] }>(
        "/interview/start",
        {
          method: "POST",
          body: JSON.stringify({ company_ids: Array.from(selectedIds) }),
        }
      );
      localStorage.setItem("session_id", result.session_id);
      localStorage.setItem(
        `questions_${result.session_id}`,
        JSON.stringify(result.questions)
      );
      navigate(`/interview/${result.session_id}`);
    } catch (err: any) {
      setStarting(null);
      setError(err.message || "Failed to start interview. Please try again.");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500 font-medium">Loading companies…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-extrabold text-gray-900">Select a Company</h1>
        <p className="mt-2 text-gray-500 text-lg">
          Choose a company to start an AI-powered mock interview tailored to their hiring style.
        </p>
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 flex items-center gap-2">
          <span className="text-red-500">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {/* Empty state */}
      {!companies.length && !error && (
        <div className="text-center py-20 text-gray-400">
          <p className="text-6xl mb-4">🏢</p>
          <p className="text-xl font-medium">No companies found.</p>
          <p className="text-sm mt-2">Contact your admin to seed company profiles.</p>
        </div>
      )}

      {/* Company Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {companies.map((c) => {
          const gradient = COMPANY_COLORS[c.name] || "from-gray-500 to-gray-400";
          const isSelected = selectedIds.has(c.id);

          return (
            <div
              key={c.id}
              className={`card ${isSelected ? "border-4 border-indigo-500" : ""}`}
              onClick={() => {
                const newSet = new Set(selectedIds);
                if (newSet.has(c.id)) newSet.delete(c.id);
                else newSet.add(c.id);
                setSelectedIds(newSet);
              }}
            >
              {/* Card header gradient */}
              <div className={`h-2 w-full bg-gradient-to-r ${gradient}`} />

              <div className="p-6 flex flex-col flex-1 gap-4">
                {/* Company name */}
                <h2 className="text-2xl font-bold text-gray-900">{c.name}</h2>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Global Start Interview button */}
      <div className="flex justify-center mt-6">
        <button
          onClick={startInterview}
          disabled={starting !== null || selectedIds.size === 0}
          className={"btn-primary w-48" + (starting ? " opacity-70" : "")}
        >
          {starting ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Starting…
            </span>
          ) : (
            "Start Interview →"
          )}
        </button>
      </div>
    </div>
  );
};

export default Companies;
