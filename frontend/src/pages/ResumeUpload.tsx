import React, { useState } from "react";
import { api } from "../services/api";

interface ParsedResume {
  skills?: string[];
  projects?: Array<{ name: string; description?: string }>; // simple shape
  experience?: Array<{ role: string; company: string; period?: string; description?: string }>;
  education?: Array<{ institution: string; degree: string; period?: string }>;
}

const ResumeUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);
  const [parsed, setParsed] = useState<ParsedResume | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a PDF file first.");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      const formData = new FormData();
      formData.append("file", file);
      // The api wrapper will automatically attach the JWT token.
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
    <div className="max-w-3xl mx-auto p-4 md:p-8 space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">Upload Your Resume</h1>

      {/* Upload form */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-100 file:text-primary-800 hover:file:bg-primary-200"
        />
        <button
          onClick={handleUpload}
          disabled={loading}
          className="mt-4 w-full bg-primary text-white py-2 rounded hover:bg-primary-dark transition-colors disabled:opacity-50"
        >
          {loading ? "Uploading…" : "Upload Resume"}
        </button>
      </div>

      {/* Feedback messages */}
      {error && <p className="text-red-600">{error}</p>}
      {success && <p className="text-green-600">Resume uploaded successfully.</p>}

      {/* Parsed resume display */}
      {parsed && (
        <div className="space-y-6">
          {/* Skills */}
          {parsed.skills && parsed.skills.length > 0 && (
            <section className="bg-white rounded-xl shadow p-4">
              <h2 className="text-xl font-semibold mb-2 text-gray-800">Skills</h2>
              <ul className="list-disc list-inside">
                {parsed.skills.map((skill, idx) => (
                  <li key={idx} className="text-gray-700">
                    {skill}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Projects */}
          {parsed.projects && parsed.projects.length > 0 && (
            <section className="bg-white rounded-xl shadow p-4">
              <h2 className="text-xl font-semibold mb-2 text-gray-800">Projects</h2>
              <div className="grid gap-4">
                {parsed.projects.map((proj, idx) => (
                  <div key={idx} className="border rounded p-3">
                    <h3 className="font-medium text-gray-800">{proj.name}</h3>
                    {proj.description && (
                      <p className="text-gray-600 text-sm mt-1">{proj.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Experience */}
          {parsed.experience && parsed.experience.length > 0 && (
            <section className="bg-white rounded-xl shadow p-4">
              <h2 className="text-xl font-semibold mb-2 text-gray-800">Experience</h2>
              <div className="space-y-3">
                {parsed.experience.map((exp, idx) => (
                  <div key={idx} className="border-b pb-2 last:border-b-0">
                    <p className="font-medium text-gray-800">
                      {exp.role} @ {exp.company}
                    </p>
                    {exp.period && <p className="text-gray-600 text-sm">{exp.period}</p>}
                    {exp.description && (
                      <p className="text-gray-600 text-sm mt-1">{exp.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Education */}
          {parsed.education && parsed.education.length > 0 && (
            <section className="bg-white rounded-xl shadow p-4">
              <h2 className="text-xl font-semibold mb-2 text-gray-800">Education</h2>
              <ul className="list-disc list-inside">
                {parsed.education.map((edu, idx) => (
                  <li key={idx} className="text-gray-700">
                    {edu.degree} – {edu.institution}{" "}
                    {edu.period && <span className="text-gray-600">({edu.period})</span>}
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
