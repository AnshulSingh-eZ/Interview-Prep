import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
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
}

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
  };
}

const Companies: React.FC = () => {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [readingFile, setReadingFile] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [jobDescription, setJobDescription] = useState("");

  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        const data = await api<any[]>("/companies/", { method: "GET" });
        setCompanies(data.map(mapCompany));
      } catch (err: any) {
        setError(err.message || "Failed to load companies.");
      } finally {
        setLoading(false);
      }
    };
    fetchCompanies();
  }, []);

  const onJdFile = async (file: File) => {
    setReadingFile(true);
    setError(null);
    try {
      const isPdf = file.name.toLowerCase().endsWith(".pdf");
      if (isPdf) {
        const formData = new FormData();
        formData.append("file", file);
        const result = await api<{ text: string }>("/interview/jd/extract", {
          method: "POST",
          body: formData,
        });
        setJobDescription(result.text);
      } else {
        setJobDescription(await file.text());
      }
    } catch (err: any) {
      setError(err.message || "Could not read that job description.");
    } finally {
      setReadingFile(false);
    }
  };

  const startInterview = async () => {
    if (!selectedId) {
      setError("Select one company.");
      return;
    }
    if (jobDescription.trim().length < 40) {
      setError("Add a job description before starting.");
      return;
    }
    setStarting(true);
    setError(null);
    try {
      const result = await api<{ session_id: string; questions: any[] }>("/interview/start", {
        method: "POST",
        body: JSON.stringify({
          company_id: selectedId,
          job_description: jobDescription.trim(),
        }),
      });
      localStorage.setItem("session_id", result.session_id);
      navigate(`/interview/${result.session_id}`);
    } catch (err: any) {
      setError(err.message || "Failed to start interview.");
      setStarting(false);
    }
  };

  if (loading) {
    return (
      <div className="page flex min-h-[50vh] flex-col items-center justify-center gap-4">
        <div className="spinner" />
        <p>Loading companies…</p>
      </div>
    );
  }

  const selected = companies.find((company) => company.id === selectedId);

  return (
    <div className="page space-y-8">
      <div>
        <h1 className="text-4xl">Set up the interview</h1>
        <p className="mt-2 max-w-2xl">
          Choose a company, then paste or upload the job description. Questions are generated from your resume, this JD, and the company profile.
        </p>
        <p className="mt-2 text-sm">
          Resume not uploaded yet? <Link to="/resume" className="text-indigo-300">Upload it first.</Link>
        </p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {companies.map((company) => {
          const active = company.id === selectedId;
          return (
            <button
              key={company.id}
              onClick={() => setSelectedId(company.id)}
              className={`card p-5 text-left ${active ? "border-indigo-400/70 shadow-[0_0_0_1px_rgba(129,140,248,0.5)]" : ""}`}
            >
              <h2 className="text-xl">{company.name}</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {company.focus_topics.slice(0, 4).map((topic) => (
                  <span key={topic} className="badge badge-primary">
                    {topic}
                  </span>
                ))}
              </div>
            </button>
          );
        })}
      </div>

      <section className="card space-y-4 p-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl">Job description</h2>
            <p className="mt-1 text-sm">
              {selected ? `Preparing for ${selected.name}.` : "Select a company above."}
            </p>
          </div>
          <label className="btn-ghost cursor-pointer">
            {readingFile ? "Reading file…" : "Upload JD"}
            <input
              type="file"
              accept=".pdf,.txt,.md,text/plain"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) onJdFile(file);
              }}
            />
          </label>
        </div>
        <textarea
          rows={8}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Paste the role summary, responsibilities, and required skills."
        />
        <button onClick={startInterview} disabled={starting || !selectedId} className="btn-primary sm:w-auto sm:px-8">
          {starting ? "Building your question set…" : "Start interview"}
        </button>
      </section>
    </div>
  );
};

export default Companies;
