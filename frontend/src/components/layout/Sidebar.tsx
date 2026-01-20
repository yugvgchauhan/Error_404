'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import {
    Home,
    User,
    BarChart3,
    BookOpen,
    LogOut,
    Menu,
    X,
    Briefcase,
    Sparkles,
    Map,
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: '/profile', label: 'Profile', icon: User },
    { href: '/skills', label: 'Skills', icon: BarChart3 },
    { href: '/roadmap', label: 'Roadmap', icon: Map },
    { href: '/recommendations', label: 'Courses', icon: BookOpen },
];

export function Sidebar() {
    const pathname = usePathname();
    const { user, profile, logout } = useAuth();
    const [mobileOpen, setMobileOpen] = useState(false);

    const profileCompletion = profile?.profile_completion || 0;

    return (
        <>
            {/* Mobile menu button */}
            <button
                className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-lg"
                onClick={() => setMobileOpen(!mobileOpen)}
            >
                {mobileOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Overlay */}
            {mobileOpen && (
                <div
                    className="lg:hidden fixed inset-0 bg-black/50 z-40"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
          fixed left-0 top-0 h-full w-64 bg-gradient-to-b from-gray-900 to-gray-800 
          text-white z-40 transform transition-transform duration-300 ease-in-out
          lg:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
            >
                {/* Logo */}
                <div className="p-6 border-b border-gray-700">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-r from-green-400 to-emerald-500 rounded-lg flex items-center justify-center">
                            <Sparkles size={24} />
                        </div>
                        <div>
                            <h1 className="font-bold text-lg">SkillPath</h1>
                            <p className="text-xs text-gray-400">Career Intelligence</p>
                        </div>
                    </div>
                </div>

                {/* User info */}
                {user && (
                    <div className="p-4 mx-4 mt-4 bg-gray-800/50 rounded-lg">
                        <p className="font-medium text-sm truncate">
                            {user.name || 'User'}
                        </p>
                        <p className="text-xs text-gray-400 truncate">{user.email}</p>
                        <div className="mt-2">
                            <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
                                <span>Profile</span>
                                <span>{Math.round(profileCompletion)}%</span>
                            </div>
                            <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all"
                                    style={{ width: `${profileCompletion}%` }}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* Navigation */}
                <nav className="p-4 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                onClick={() => setMobileOpen(false)}
                                className={`
                  flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
                  ${isActive
                                        ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg'
                                        : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                                    }
                `}
                            >
                                <Icon size={20} />
                                <span className="font-medium">{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                {/* Logout */}
                <div className="absolute bottom-0 left-0 right-0 p-4">
                    <button
                        onClick={logout}
                        className="flex items-center gap-3 px-4 py-3 w-full text-gray-300 hover:bg-red-500/20 hover:text-red-400 rounded-lg transition-colors"
                    >
                        <LogOut size={20} />
                        <span className="font-medium">Logout</span>
                    </button>
                </div>
            </aside>
        </>
    );
}

export function MainLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="min-h-screen bg-gray-50">
            <Sidebar />
            <main className="lg:ml-64 min-h-screen">
                <div className="p-6 lg:p-8">{children}</div>
            </main>
        </div>
    );
}
