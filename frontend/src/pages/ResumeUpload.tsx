import React, { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";

interface ParsedResume {
  skills?: string[];
  projects?: Array<{ name?: string; description?: string } | string>;
  experience?: Array<{ role?: string; company?: string; period?: string; description?: string } | string>;
  education?: Array<{ institution?: string; degree?: string; period?: string } | string>;
}

const asText = (value: unknown) => (typeof value === "string" ? value : "");

const ResumeUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [parsed, setParsed] = useState<ParsedResume | null>(null);

  const handleUpload = async () => {
    if (!file) {
      setError("Choose a PDF resume first.");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await api<ParsedResume>("/resume/upload", {
        method: "POST",
        body: formData,
      });
      setParsed(response);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message ?? "Failed to upload resume.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page max-w-3xl space-y-6">
      <div>
        <h1 className="text-4xl">Upload your resume</h1>
        <p className="mt-2">We extract skills, projects, and experience, then use them when generating questions.</p>
      </div>

      <div className="card space-y-4 p-6">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        {file && <p className="text-sm text-slate-300">{file.name}</p>}
        <button onClick={handleUpload} disabled={loading} className="btn-primary">
          {loading ? "Reading resume…" : "Upload resume"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && (
        <div className="alert alert-success">
          Resume saved.
          <Link to="/companies" className="ml-2 font-semibold text-white underline">
            Add a job description
          </Link>
        </div>
      )}

      {parsed && (
        <div className="space-y-4">
          {!!parsed.skills?.length && (
            <section className="card p-5">
              <h2 className="text-lg">Skills</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {parsed.skills.map((skill, idx) => (
                  <span key={idx} className="badge badge-primary">
                    {skill}
                  </span>
                ))}
              </div>
            </section>
          )}

          {!!parsed.projects?.length && (
            <section className="card p-5">
              <h2 className="text-lg">Projects</h2>
              <div className="mt-3 space-y-3">
                {parsed.projects.map((project, idx) => (
                  <div key={idx}>
                    <p className="text-slate-100">
                      {typeof project === "string" ? project : project.name || "Project"}
                    </p>
                    {typeof project !== "string" && project.description && (
                      <p className="text-sm">{project.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {!!parsed.experience?.length && (
            <section className="card p-5">
              <h2 className="text-lg">Experience</h2>
              <div className="mt-3 space-y-3">
                {parsed.experience.map((item, idx) => (
                  <div key={idx}>
                    <p className="text-slate-100">
                      {typeof item === "string"
                        ? item
                        : `${asText(item.role) || "Role"}${item.company ? ` · ${item.company}` : ""}`}
                    </p>
                    {typeof item !== "string" && item.description && <p className="text-sm">{item.description}</p>}
                  </div>
                ))}
              </div>
            </section>
          )}

          {!!parsed.education?.length && (
            <section className="card p-5">
              <h2 className="text-lg">Education</h2>
              <ul className="mt-3 space-y-2">
                {parsed.education.map((item, idx) => (
                  <li key={idx}>
                    {typeof item === "string"
                      ? item
                      : `${item.degree || "Degree"}${item.institution ? ` · ${item.institution}` : ""}`}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </div>
  );
};

export default ResumeUpload;
