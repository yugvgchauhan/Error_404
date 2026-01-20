'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api, Skill, GapAnalysis, GapItem } from '@/lib/api';
import { MainLayout } from '@/components/layout/Sidebar';
import { TrendingUp, Award, Target, AlertCircle, ChevronRight, BookOpen } from 'lucide-react';
import {
    PieChart,
    Pie,
    Cell,
    ResponsiveContainer,
    Tooltip,
    Legend,
    BarChart,
    Bar,
    XAxis,
    YAxis,
} from 'recharts';

const PROFICIENCY_COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function SkillsPage() {
    const { user, loading: authLoading, userId } = useAuth();
    const router = useRouter();
    const [skills, setSkills] = useState<Skill[]>([]);
    const [gapAnalysis, setGapAnalysis] = useState<GapAnalysis | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!authLoading && !user) {
            router.push('/login');
        } else if (userId) {
            loadData();
        }
    }, [user, authLoading, userId]);

    const loadData = async () => {
        if (!userId) return;
        try {
            const [skillsData, gapData] = await Promise.all([
                api.getUserSkills(userId).catch(() => []),
                api.getGapAnalysis(userId).catch(() => null),
            ]);
            setSkills(skillsData);
            setGapAnalysis(gapData);
        } catch (error) {
            console.error('Failed to load skills:', error);
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

    // Group skills by source
    const skillsBySource: Record<string, Skill[]> = {};
    skills.forEach(skill => {
        let sources: string[] = ['other'];
        if (skill.sources && Array.isArray(skill.sources)) {
            sources = skill.sources;
        }

        sources.forEach(src => {
            // Extract type from "type:id" format (e.g., "resume:0" -> "resume")
            const sourceType = src.split(':')[0] || 'other';
            const source = sourceType.toLowerCase();

            if (!skillsBySource[source]) skillsBySource[source] = [];
            if (!skillsBySource[source].find(s => s.skill_name === skill.skill_name)) {
                skillsBySource[source].push(skill);
            }
        });
    });

    // Prepare chart data
    const sourceChartData = Object.entries(skillsBySource).map(([source, skills], i) => ({
        name: source.charAt(0).toUpperCase() + source.slice(1),
        value: skills.length,
        color: PROFICIENCY_COLORS[i % PROFICIENCY_COLORS.length],
    }));

    const topSkillsData = skills
        .sort((a, b) => b.proficiency - a.proficiency)
        .slice(0, 8)
        .map((skill, i) => ({
            name: skill.skill_name.substring(0, 15),
            proficiency: Math.round(skill.proficiency * 100),
            color: PROFICIENCY_COLORS[i % PROFICIENCY_COLORS.length],
        }));

    return (
        <MainLayout>
            <div className="space-y-8 animate-fade-in">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Skills Analysis</h1>
                    <p className="text-gray-500 mt-1">Analyze your skill portfolio and identify gaps</p>
                </div>

                {/* Stats */}
                <div className="grid md:grid-cols-3 gap-6">
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                                <Award className="text-green-600" size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Total Skills</p>
                                <p className="text-3xl font-bold text-gray-900">{skills.length}</p>
                            </div>
                        </div>
                    </div>
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                                <Target className="text-blue-600" size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Job Match</p>
                                <p className="text-3xl font-bold text-gray-900">
                                    {(gapAnalysis?.overall_readiness ? gapAnalysis.overall_readiness * 100 : 0).toFixed(0)}%
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center">
                                <TrendingUp className="text-amber-600" size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-gray-500">Skills to Learn</p>
                                <p className="text-3xl font-bold text-gray-900">
                                    {((gapAnalysis?.critical_gaps?.length || 0) + (gapAnalysis?.important_gaps?.length || 0))}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Source Distribution */}
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Skills by Source</h2>
                        {sourceChartData.length > 0 ? (
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={sourceChartData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={100}
                                            paddingAngle={2}
                                            dataKey="value"
                                        >
                                            {sourceChartData.map((entry, index) => (
                                                <Cell key={index} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                        <Legend />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="h-80 flex items-center justify-center text-gray-500">
                                No skills data yet
                            </div>
                        )}
                    </div>

                    {/* Top Skills by Proficiency */}
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Skills by Proficiency</h2>
                        {topSkillsData.length > 0 ? (
                            <div className="h-80">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={topSkillsData} layout="vertical">
                                        <XAxis type="number" domain={[0, 100]} tick={{ fill: '#9ca3af' }} />
                                        <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#6b7280', fontSize: 11 }} />
                                        <Tooltip
                                            formatter={(value: number) => [`${value}%`, 'Proficiency']}
                                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                        />
                                        <Bar dataKey="proficiency" radius={[0, 4, 4, 0]}>
                                            {topSkillsData.map((entry, index) => (
                                                <Cell key={index} fill={entry.color} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        ) : (
                            <div className="h-80 flex items-center justify-center text-gray-500">
                                No skills data yet
                            </div>
                        )}
                    </div>
                </div>

                {/* Skill Gaps */}
                {gapAnalysis && ((gapAnalysis.critical_gaps?.length ?? 0) > 0 || (gapAnalysis.important_gaps?.length ?? 0) > 0 || (gapAnalysis.emerging_gaps?.length ?? 0) > 0) && (
                    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h2 className="text-lg font-semibold text-gray-900">🎯 Skills Gap Analysis</h2>
                                <p className="text-sm text-gray-500 mt-1">
                                    Skills you need to learn for your target role
                                </p>
                            </div>
                            <button
                                onClick={() => router.push('/recommendations')}
                                className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-medium hover:shadow-lg transition-all flex items-center gap-2"
                            >
                                <BookOpen size={18} />
                                Get Courses
                                <ChevronRight size={16} />
                            </button>
                        </div>
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {gapAnalysis.critical_gaps?.map((gap: GapItem, index: number) => (
                                <div
                                    key={`critical-${index}`}
                                    className="p-4 rounded-xl border bg-red-50 border-red-200"
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium text-gray-900">{gap.skill}</span>
                                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                                            critical
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-500 mt-1">
                                        Market Importance: {Math.round((gap.market_importance || 0) * 100)}%
                                    </p>
                                    <p className="text-xs text-red-600 mt-1">
                                        Gap Score: {Math.round(gap.gap_score * 100)}%
                                    </p>
                                </div>
                            ))}
                            {gapAnalysis.important_gaps?.map((gap: GapItem, index: number) => (
                                <div
                                    key={`important-${index}`}
                                    className="p-4 rounded-xl border bg-amber-50 border-amber-200"
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium text-gray-900">{gap.skill}</span>
                                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                                            important
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-500 mt-1">
                                        Market Importance: {Math.round((gap.market_importance || 0) * 100)}%
                                    </p>
                                    <p className="text-xs text-amber-600 mt-1">
                                        Gap Score: {Math.round(gap.gap_score * 100)}%
                                    </p>
                                </div>
                            ))}
                            {gapAnalysis.emerging_gaps?.map((gap: GapItem, index: number) => (
                                <div
                                    key={`emerging-${index}`}
                                    className="p-4 rounded-xl border bg-blue-50 border-blue-200"
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="font-medium text-gray-900">{gap.skill}</span>
                                        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                                            emerging
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-500 mt-1">
                                        Market Importance: {Math.round((gap.market_importance || 0) * 100)}%
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* All Skills by Source */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-6">All Your Skills</h2>
                    {Object.keys(skillsBySource).length > 0 ? (
                        <div className="space-y-6">
                            {Object.entries(skillsBySource).map(([source, sourceSkills], i) => (
                                <div key={source}>
                                    <h3
                                        className="text-sm font-semibold mb-3 flex items-center gap-2"
                                        style={{ color: PROFICIENCY_COLORS[i % PROFICIENCY_COLORS.length] }}
                                    >
                                        <span
                                            className="w-3 h-3 rounded-full"
                                            style={{ backgroundColor: PROFICIENCY_COLORS[i % PROFICIENCY_COLORS.length] }}
                                        />
                                        From {source.charAt(0).toUpperCase() + source.slice(1)}
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {sourceSkills.map((skill) => (
                                            <span
                                                key={skill.id}
                                                className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-sm flex items-center gap-2"
                                            >
                                                {skill.skill_name}
                                                <span className="text-xs text-gray-400">
                                                    {Math.round(skill.proficiency * 100)}%
                                                </span>
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-8 text-gray-400">
                            <AlertCircle size={48} className="mx-auto mb-4 opacity-50" />
                            <p>No skills yet. Upload your resume in the Profile page.</p>
                            <button
                                onClick={() => router.push('/profile')}
                                className="mt-4 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                            >
                                Go to Profile
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </MainLayout>
    );
}
