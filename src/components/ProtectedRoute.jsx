/* ═══════════════════════════════════════════════════════════════
   LABMIND AI — Protected Route Wrapper
   ═══════════════════════════════════════════════════════════════
   Wraps routes that require authentication.
   - If auth is still bootstrapping → shows nothing (loading)
   - If authenticated → renders children
   - If NOT authenticated → redirects to /login
   ═══════════════════════════════════════════════════════════════ */

import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
    const { currentUser, isBootstrapping } = useAuth();

    // Still checking if we have a stored JWT — show nothing yet
    if (isBootstrapping) return null;

    // Not logged in → redirect to login
    if (!currentUser) return <Navigate to="/login" replace />;

    // Authenticated → render the actual screen
    return children;
}
