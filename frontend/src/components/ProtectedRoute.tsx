import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

/**
 * ProtectedRoute ensures that a user is authenticated before granting access
 * to child routes. It checks for a JWT token stored in localStorage.
 */
const ProtectedRoute: React.FC = () => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    // Not authenticated – redirect to login page
    return <Navigate to="/login" replace />;
  }
  // Authenticated – render child routes
  return <Outlet />;
};

export default ProtectedRoute;
