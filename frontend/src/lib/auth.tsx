'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Types
export interface User {
    id: number;
    email: string;
    name: string;
    current_role?: string;
    target_role?: string;
    location?: string;
    organization?: string;
    education?: string;
    university?: string;
    graduation_year?: number;
    phone?: string;
    target_sector?: string;
    github_url?: string;
    linkedin_url?: string;
    has_resume?: boolean;
    profile_completion?: number;
    total_skills?: number;
    total_projects?: number;
    total_courses?: number;
}

interface AuthContextType {
    user: User | null;
    profile: User | null;
    userId: number | null;
    loading: boolean;
    login: (email: string) => Promise<void>;
    register: (userData: Partial<User>) => Promise<void>;
    logout: () => void;
    updateUser: (userData: Partial<User>) => void;
    refreshUser: () => Promise<void>;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// AuthProvider component
export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // Check for existing session on mount
    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (error) {
                console.error('Failed to parse stored user:', error);
                localStorage.removeItem('user');
            }
        }
        setLoading(false);
    }, []);

    // Login function
    const login = async (email: string) => {
        try {
            // First, try to get user by email
            const response = await fetch(`${API_BASE_URL}/api/users/email/${encodeURIComponent(email)}`);

            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
                localStorage.setItem('user', JSON.stringify(userData));
            } else if (response.status === 404) {
                throw new Error('No account found with this email. Please register first.');
            } else {
                throw new Error('Login failed. Please try again.');
            }
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    };

    // Register function
    const register = async (userData: Partial<User>) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/users/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData),
            });

            if (response.ok) {
                const newUser = await response.json();
                setUser(newUser);
                localStorage.setItem('user', JSON.stringify(newUser));
            } else {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Registration failed. Please try again.');
            }
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    };

    // Logout function
    const logout = () => {
        setUser(null);
        localStorage.removeItem('user');
    };

    // Update user function
    const updateUser = (userData: Partial<User>) => {
        if (user) {
            const updatedUser = { ...user, ...userData };
            setUser(updatedUser);
            localStorage.setItem('user', JSON.stringify(updatedUser));
        }
    };

    // Refresh user function - reload user data from backend
    const refreshUser = async () => {
        if (user?.id) {
            try {
                const response = await fetch(`${API_BASE_URL}/api/users/${user.id}`);
                if (response.ok) {
                    const userData = await response.json();
                    setUser(userData);
                    localStorage.setItem('user', JSON.stringify(userData));
                }
            } catch (error) {
                console.error('Failed to refresh user:', error);
            }
        }
    };

    const value: AuthContextType = {
        user,
        profile: user,
        userId: user?.id || null,
        loading,
        login,
        register,
        logout,
        updateUser,
        refreshUser,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// useAuth hook
export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
