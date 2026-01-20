'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api, Skill, GapAnalysis } from '@/lib/api';
import { MainLayout } from '@/components/layout/Sidebar';
import {
    TrendingUp,
    Target,
    BookOpen,
    Award,
    ArrowRight,
    ChevronRight,
    FileText,
    Briefcase,
} from 'lucide-react';
import {
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Radar,
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    Cell,
} from 'recharts';

interface DashboardData {
    profile_completion: number;
    total_skills: number;
    total_projects: number;
    total_courses: number;
    skills: Skill[];
    gapAnalysis: GapAnalysis | null;
}

const SKILL_COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function DashboardPage() {
    const { user, profile, loading: authLoading, userId } = useAuth();
    const router = useRouter();
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!authLoading && !user) {
            router.push('/login');
        }
    }, [user, authLoading, router]);

    useEffect(() => {
        if (userId) {
            loadDashboard();
        }
    }, [userId]);

    const loadDashboard = async () => {
        if (!userId) return;

        try {
            const [skills, gapAnalysis] = await Promise.all([
                api.getUserSkills(userId).catch(() => []),
                api.getGapAnalysis(userId).catch(() => null),
            ]);

            setData({
                profile_completion: profile?.profile_completion || 0,
                total_skills: profile?.total_skills || skills.length,
                total_projects: profile?.total_projects || 0,
                total_courses: profile?.total_courses || 0,
                skills,
                gapAnalysis,
            });
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        } finally {
            setLoading(false);
        }
    };

    if (authLoading || loading) {
        return (
            <MainLayout>
                <div className="flex items-center justify-center h-96">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-green-500 border-t-transparent"></div>
                </div>
            </MainLayout>
        );
    }

    const skillsData = data?.skills.slice(0, 8).map((s, i) => ({
        name: s.skill_name,
        proficiency: Math.round(s.proficiency * 100),
        color: SKILL_COLORS[i % SKILL_COLORS.length],
    })) || [];

    const radarData = data?.skills.slice(0, 6).map(s => ({
        skill: s.skill_name.substring(0, 10),
        value: Math.round(s.proficiency * 100),
        fullMark: 100,
    })) || [];

    const matchPercentage = data?.gapAnalysis?.overall_readiness ? data.gapAnalysis.overall_readiness * 100 : 0;

    // Combine critical and important gaps for the "Skills to Learn" section
    const displayGaps = [
        ...(data?.gapAnalysis?.critical_gaps || []),
        ...(data?.gapAnalysis?.important_gaps || [])
    ].slice(0, 10);

    return (
        <MainLayout>
            <div className="space-y-8 animate-fade-in">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">
                            Welcome back, {user?.name?.split(' ')[0] || 'there'}! 👋
                        </h1>
                        <p className="text-gray-500 mt-1">Track your career readiness and progress</p>
                    </div>
                    {(data?.total_skills || 0) === 0 && (
                        <button
                            onClick={() => router.push('/profile')}
                            className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl font-medium hover:shadow-lg transition-all flex items-center gap-2"
                        >
                            Upload Resume
                            <ArrowRight size={20} />
                        </button>
                    )}
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 card-hover">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500">Profile Completion</p>
                                <p className="text-3xl font-bold text-gray-900 mt-1">
                                    {data?.profile_completion?.toFixed(0) || 0}%
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                                <TrendingUp className="text-green-600" size={24} />
                            </div>
                        </div>
                        <div className="mt-4 h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-green-400 to-emerald-500 rounded-full transition-all duration-500"
                                style={{ width: `${data?.profile_completion || 0}%` }}
                            />
                        </div>
                    </div>

                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 card-hover">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500">Skills Identified</p>
                                <p className="text-3xl font-bold text-gray-900 mt-1">{data?.total_skills || 0}</p>
                            </div>
                            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                                <Award className="text-blue-600" size={24} />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 card-hover">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500">Projects</p>
                                <p className="text-3xl font-bold text-gray-900 mt-1">{data?.total_projects || 0}</p>
                            </div>
                            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                                <Briefcase className="text-purple-600" size={24} />
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 card-hover">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500">Job Match</p>
                                <p className="text-3xl font-bold text-gray-900 mt-1">
                                    {matchPercentage.toFixed(0)}%
                                </p>
                            </div>
                            <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                                <Target className="text-amber-600" size={24} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Charts Row */}
                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Radar Chart */}
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Skill Overview</h2>
                        {radarData.length > 0 ? (
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <RadarChart data={radarData}>
                                        <PolarGrid stroke="#e5e7eb" />
                                        <PolarAngleAxis dataKey="skill" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#9ca3af' }} />
                                        <Radar
                                            name="Proficiency"
                                            dataKey="value"
                                            stroke="#22c55e"
                                            fill="#22c55e"
                                            fillOpacity={0.3}
                                            strokeWidth={2}
                                        />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="h-80 flex items-center justify-center text-gray-400">
                                <div className="text-center">
                                    <FileText size={48} className="mx-auto mb-4 opacity-50" />
                                    <p>Upload your resume to see skill analysis</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Bar Chart */}
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Skills Proficiency</h2>
                        {skillsData.length > 0 ? (
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={skillsData} layout="vertical">
                                        <XAxis type="number" domain={[0, 100]} tick={{ fill: '#9ca3af' }} />
                                        <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#6b7280', fontSize: 11 }} />
                                        <Tooltip
                                            formatter={(value: number) => [`${value}%`, 'Proficiency']}
                                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                        />
                                        <Bar dataKey="proficiency" radius={[0, 4, 4, 0]}>
                                            {skillsData.map((entry, index) => (
                                                <Cell key={index} fill={entry.color} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="h-80 flex items-center justify-center text-gray-400">
                                <div className="text-center">
                                    <Award size={48} className="mx-auto mb-4 opacity-50" />
                                    <p>No skills extracted yet</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Skills Gap Section */}
                {displayGaps.length > 0 && (
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-900">Skills to Learn</h2>
                            <button
                                onClick={() => router.push('/recommendations')}
                                className="text-green-600 hover:text-green-700 text-sm font-medium flex items-center gap-1"
                            >
                                View Courses <ChevronRight size={16} />
                            </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {displayGaps.map((gap, i) => (
                                <span
                                    key={i}
                                    className={`px-3 py-1.5 rounded-full text-sm font-medium ${gap.priority === 'critical'
                                        ? 'bg-red-100 text-red-700'
                                        : gap.priority === 'important'
                                            ? 'bg-amber-100 text-amber-700'
                                            : 'bg-blue-100 text-blue-700'
                                        }`}
                                >
                                    {gap.skill}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {/* Quick Actions */}
                <div className="grid md:grid-cols-3 gap-6">
                    <button
                        onClick={() => router.push('/skills')}
                        className="p-6 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl text-white text-left hover:shadow-lg hover:shadow-blue-500/30 transition-all group"
                    >
                        <h3 className="font-semibold text-lg mb-1">Analyze Skills Gap</h3>
                        <p className="text-blue-100 text-sm">See what skills you need to learn</p>
                        <ArrowRight className="mt-4 group-hover:translate-x-2 transition-transform" size={20} />
                    </button>

                    <button
                        onClick={() => router.push('/recommendations')}
                        className="p-6 bg-gradient-to-r from-purple-500 to-pink-600 rounded-2xl text-white text-left hover:shadow-lg hover:shadow-purple-500/30 transition-all group"
                    >
                        <h3 className="font-semibold text-lg mb-1">Get Recommendations</h3>
                        <p className="text-purple-100 text-sm">Courses, projects, certifications</p>
                        <ArrowRight className="mt-4 group-hover:translate-x-2 transition-transform" size={20} />
                    </button>

                    <button
                        onClick={() => router.push('/profile')}
                        className="p-6 bg-gradient-to-r from-orange-500 to-red-600 rounded-2xl text-white text-left hover:shadow-lg hover:shadow-orange-500/30 transition-all group"
                    >
                        <h3 className="font-semibold text-lg mb-1">Update Profile</h3>
                        <p className="text-orange-100 text-sm">Upload resume, add projects</p>
                        <ArrowRight className="mt-4 group-hover:translate-x-2 transition-transform" size={20} />
                    </button>
                </div>
            </div>
        </MainLayout>
    );
}
