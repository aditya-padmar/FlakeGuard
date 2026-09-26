import React, { createContext, useContext, useState, useEffect } from 'react';

export interface User {
  name: string;
  email: string;
  organization?: string;
  avatar?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, name?: string) => void;
  signup: (name: string, email: string, organization?: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'flakeguard_user';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      const profile = saved ? JSON.parse(saved) : null;
      return profile && typeof profile.name === 'string' && typeof profile.email === 'string' ? profile as User : null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    try {
      if (user) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // Restricted storage must not prevent an in-memory demo session.
    }
  }, [user]);

  const login = (email: string, name?: string) => {
    const derivedName = name || email.split('@')[0].replace(/[._]/g, ' ') || 'Developer';
    const formattedName = derivedName
      .split(' ')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');

    const newUser: User = {
      email,
      name: formattedName,
      organization: 'Engineering Team',
      avatar: formattedName.charAt(0).toUpperCase(),
    };
    setUser(newUser);
  };

  const signup = (name: string, email: string, organization?: string) => {
    const newUser: User = {
      name,
      email,
      organization: organization || 'Engineering Team',
      avatar: name.charAt(0).toUpperCase(),
    };
    setUser(newUser);
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
