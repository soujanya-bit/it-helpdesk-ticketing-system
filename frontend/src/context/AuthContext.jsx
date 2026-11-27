
import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import api from "../api/axios";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch the authenticated user's profile.
  const fetchCurrentUser = async () => {
    try {
      const response = await api.get("/auth/me");
      setUser(response.data);
      return response.data;
    } catch (error) {
      localStorage.removeItem("access_token");
      setUser(null);
      return null;
    }
  };

  // Check for an existing login when the app loads.
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem("access_token");

      if (token) {
        await fetchCurrentUser();
      }

      setLoading(false);
    };

    initializeAuth();
  }, []);

  // Authenticate the user.
  const login = async (email, password) => {
    const formData = new URLSearchParams();

    formData.append("username", email);
    formData.append("password", password);

    const response = await api.post("/auth/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    const { access_token } = response.data;

    localStorage.setItem("access_token", access_token);

    const currentUser = await fetchCurrentUser();

    if (!currentUser) {
      throw new Error("Unable to retrieve user profile.");
    }

    return currentUser;
  };

  // Register a new employee account.
  const register = async (userData) => {
    const response = await api.post("/auth/register", userData);
    return response.data;
  };

  // End the current session.
  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook for accessing authentication.
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside an AuthProvider"
    );
  }

  return context;
}
