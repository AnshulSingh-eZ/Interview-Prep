import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import * as authService from "../services/auth";

const Register: React.FC = () => {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authService.register(name, email, password);
      setSuccess(true);
      setTimeout(() => navigate("/login"), 1200);
    } catch (err: any) {
      setError(err.message || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page flex justify-center pt-10">
      <div className="card w-full max-w-md p-8">
        <h1 className="text-3xl">Create account</h1>
        <p className="mt-2 mb-6 text-sm">Save your resume and interview history.</p>
        {error && <div className="alert alert-error mb-4">{error}</div>}
        {success && <div className="alert alert-success mb-4">Account created. Taking you to login…</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="name">Name</label>
            <input id="name" type="text" required value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label htmlFor="email">Email</label>
            <input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label htmlFor="password">Password</label>
            <input id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? "Creating…" : "Create account"}
          </button>
        </form>
        <p className="mt-5 text-center text-sm">
          Already registered?{" "}
          <Link to="/login" className="text-gradient font-semibold">
            Login
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
