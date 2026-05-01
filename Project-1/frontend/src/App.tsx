import { useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { ChatContainer } from "./components/chat/ChatContainer";
import { useAuthStore } from "./lib/authStore";
import Login from "./pages/Login";
import Register from "./pages/Register";
import AuthCallback from "./pages/AuthCallback";

export default function App() {
  const { user, loading, hydrate } = useAuthStore();

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 text-sm text-gray-500 dark:bg-gray-950 dark:text-gray-400">
        Loading…
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/"
        element={<Navigate to={user ? "/chat" : "/login"} replace />}
      />
      <Route
        path="/login"
        element={user ? <Navigate to="/chat" replace /> : <Login />}
      />
      <Route
        path="/register"
        element={user ? <Navigate to="/chat" replace /> : <Register />}
      />
      <Route
        path="/chat"
        element={user ? <ChatContainer /> : <Navigate to="/login" replace />}
      />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route
        path="*"
        element={<Navigate to={user ? "/chat" : "/login"} replace />}
      />
    </Routes>
  );
}
