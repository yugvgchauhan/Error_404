'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api } from '@/lib/api';
import { MainLayout } from '@/components/layout/Sidebar';
import { BookOpen, ExternalLink, Clock, Search, Star, AlertCircle, RefreshCw, Sparkles } from 'lucide-react';

interface CourseRecommendation {
    skill: string;
    gap_priority?: string;
    courses: Array<{
        title?: string;
        course_name?: string;
        platform: string;
        url: string;
        rating?: number;
        duration?: string;
        description?: string;
        cost?: string;
    }>;
}

export default function RecommendationsPage() {
    const { user, loading: authLoading, userId } = useAuth();
    const router = useRouter();
    const [recommendations, setRecommendations] = useState<CourseRecommendation[]>([]);
    const [searchSkill, setSearchSkill] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searching, setSearching] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [hasSkills, setHasSkills] = useState(true);

    useEffect(() => {
        if (!authLoading && !user) {
            router.push('/login');
        } else if (userId) {
            loadRecommendations();
        }
    }, [user, authLoading, userId]);

    const loadRecommendations = async () => {
        if (!userId) return;
        setLoading(true);
        setError(null);
        try {
            // First check if user has skills
            const skills = await api.getUserSkills(userId).catch(() => []);
            if (!skills || skills.length === 0) {
                setHasSkills(false);
                setLoading(false);
                return;
            }
            setHasSkills(true);

            const result = await api.getRecommendedCourses(userId);
            console.log('Recommendations response:', result);

            // Transform the response
            const recs: CourseRecommendation[] = [];
            const recsData = result.recommendations || [];

            for (const item of recsData) {
                if (item.courses && item.courses.length > 0) {
                    recs.push({
                        skill: item.skill || 'General',
                        gap_priority: item.gap_priority,
                        courses: item.courses,
                    });
                }
            }

            setRecommendations(recs);
        } catch (err: any) {
            console.error('Failed to load recommendations:', err);
            setError(err.message || 'Failed to load recommendations');
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async () => {
        if (!searchSkill.trim()) return;
        setSearching(true);
        try {
            const result = await api.searchCoursesForSkill(searchSkill.trim());
            setSearchResults(result.courses || []);
        } catch (err) {
            console.error('Failed to search courses:', err);
        } finally {
            setSearching(false);
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

    // No skills yet
    if (!hasSkills) {
        return (
            <MainLayout>
                <div className="space-y-8 animate-fade-in">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Course Recommendations</h1>
                        <p className="text-gray-500 mt-1">Personalized courses based on your skill gaps</p>
                    </div>

                    <div className="bg-white rounded-2xl p-12 shadow-sm border border-gray-100 text-center">
                        <Sparkles size={48} className="mx-auto text-amber-400 mb-4" />
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">Extract Skills First</h3>
                        <p className="text-gray-500 mb-6">
                            Upload your resume and extract skills to get personalized course recommendations based on your skill gaps.
                        </p>
                        <button
                            onClick={() => router.push('/profile')}
                            className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
                        >
                            Go to Profile
                        </button>
                    </div>

                    {/* Search Box - always available */}
                    <SearchBox
                        searchSkill={searchSkill}
                        setSearchSkill={setSearchSkill}
                        handleSearch={handleSearch}
                        searching={searching}
                        searchResults={searchResults}
                    />
                </div>
            </MainLayout>
        );
    }

    return (
        <MainLayout>
            <div className="space-y-8 animate-fade-in">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Course Recommendations</h1>
                        <p className="text-gray-500 mt-1">Personalized courses based on your skill gaps</p>
                    </div>
                    <button
                        onClick={loadRecommendations}
                        className="px-4 py-2 text-green-600 hover:bg-green-50 rounded-xl flex items-center gap-2 transition-all"
                    >
                        <RefreshCw size={16} />
                        Refresh
                    </button>
                </div>

                {/* Search Box */}
                <SearchBox
                    searchSkill={searchSkill}
                    setSearchSkill={setSearchSkill}
                    handleSearch={handleSearch}
                    searching={searching}
                    searchResults={searchResults}
                />

                {/* Error State */}
                {error && (
                    <div className="bg-red-50 border border-red-200 rounded-2xl p-6 text-center">
                        <AlertCircle size={32} className="mx-auto text-red-400 mb-2" />
                        <p className="text-red-700">{error}</p>
                        <button
                            onClick={loadRecommendations}
                            className="mt-4 px-4 py-2 text-red-600 hover:bg-red-100 rounded-lg transition-all"
                        >
                            Try Again
                        </button>
                    </div>
                )}

                {/* Recommendations by Skill Gap */}
                {recommendations.length > 0 ? (
                    <div className="space-y-8">
                        {recommendations.map((rec, idx) => (
                            <div key={idx} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                                <div className="flex items-center gap-3 mb-6">
                                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${rec.gap_priority === 'critical'
                                            ? 'bg-gradient-to-r from-red-500 to-orange-500'
                                            : 'bg-gradient-to-r from-purple-500 to-pink-500'
                                        }`}>
                                        <BookOpen className="text-white" size={20} />
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-semibold text-gray-900">
                                            Learn {rec.skill}
                                        </h2>
                                        <div className="flex items-center gap-2">
                                            <p className="text-sm text-gray-500">
                                                {rec.courses.length} course{rec.courses.length !== 1 ? 's' : ''} recommended
                                            </p>
                                            {rec.gap_priority === 'critical' && (
                                                <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full font-medium">
                                                    Critical Gap
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {rec.courses.map((course, cidx) => (
                                        <CourseCard key={cidx} course={course} />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                ) : !error && (
                    <div className="bg-white rounded-2xl p-12 shadow-sm border border-gray-100 text-center">
                        <AlertCircle size={48} className="mx-auto text-gray-300 mb-4" />
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Skill Gaps Found</h3>
                        <p className="text-gray-500 mb-6">
                            Great news! You don't have any critical skill gaps. Use the search above to find courses for any skill you want to learn.
                        </p>
                        <button
                            onClick={() => router.push('/roadmap')}
                            className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
                        >
                            View Career Roadmaps
                        </button>
                    </div>
                )}
            </div>
        </MainLayout>
    );
}

// Search Box Component
function SearchBox({ searchSkill, setSearchSkill, handleSearch, searching, searchResults }: {
    searchSkill: string;
    setSearchSkill: (v: string) => void;
    handleSearch: () => void;
    searching: boolean;
    searchResults: any[];
}) {
    return (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Search Courses by Skill</h2>
            <div className="flex gap-4">
                <div className="flex-1 relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                    <input
                        type="text"
                        value={searchSkill}
                        onChange={(e) => setSearchSkill(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 text-gray-900"
                        placeholder="Search for a skill (e.g., Python, Machine Learning, SQL)"
                    />
                </div>
                <button
                    onClick={handleSearch}
                    disabled={searching}
                    className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
                >
                    {searching ? 'Searching...' : 'Search'}
                </button>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
                <div className="mt-6">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">
                        Search Results for "{searchSkill}"
                    </h3>
                    <div className="grid md:grid-cols-2 gap-4">
                        {searchResults.map((course, idx) => (
                            <CourseCard key={idx} course={course} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// Platform logos/colors for visual distinction
const PLATFORM_CONFIG: Record<string, { color: string; icon: string }> = {
    'Coursera': { color: '#0056D2', icon: '📘' },
    'edX': { color: '#02262B', icon: '🎓' },
    'Udemy': { color: '#A435F0', icon: '📚' },
    'LinkedIn Learning': { color: '#0077B5', icon: '💼' },
    'Udacity': { color: '#02B3E4', icon: '🚀' },
    'Pluralsight': { color: '#F15B2A', icon: '🔧' },
    'Unknown': { color: '#6B7280', icon: '📖' },
};

function CourseCard({ course }: { course: any }) {
    const platform = course.platform || 'Unknown';
    const config = PLATFORM_CONFIG[platform] || PLATFORM_CONFIG['Unknown'];
    const title = course.course_name || course.title || 'Course';

    return (
        <div className="p-4 border border-gray-200 rounded-xl hover:border-green-300 hover:shadow-md transition-all bg-white">
            {/* Platform Badge */}
            <div className="flex items-center gap-2 mb-3">
                <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-lg"
                    style={{ backgroundColor: config.color + '15' }}
                >
                    {config.icon}
                </div>
                <span
                    className="text-xs font-semibold px-2 py-1 rounded-full"
                    style={{ backgroundColor: config.color + '15', color: config.color }}
                >
                    {platform}
                </span>
            </div>

            {/* Course Title */}
            <h4 className="font-semibold text-gray-900 mb-2 line-clamp-2 leading-tight">
                {title}
            </h4>

            {/* Description */}
            {course.description && (
                <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                    {course.description}
                </p>
            )}

            {/* Meta Info */}
            <div className="flex items-center flex-wrap gap-2 text-xs text-gray-500 mb-3">
                {course.duration && (
                    <span className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded">
                        <Clock size={12} />
                        {course.duration}
                    </span>
                )}
                {course.rating && (
                    <span className="flex items-center gap-1 bg-yellow-50 px-2 py-1 rounded text-yellow-700">
                        <Star size={12} className="text-yellow-500 fill-yellow-500" />
                        {course.rating}
                    </span>
                )}
                {course.cost && (
                    <span className="text-green-600 bg-green-50 px-2 py-1 rounded">
                        {course.cost.split('/')[0]}
                    </span>
                )}
            </div>

            {/* CTA Button */}
            {course.url && (
                <a
                    href={course.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 w-full py-2.5 rounded-lg font-medium text-sm text-white transition-all hover:opacity-90"
                    style={{ backgroundColor: config.color }}
                >
                    View Course
                    <ExternalLink size={14} />
                </a>
            )}
        </div>
    );
}
