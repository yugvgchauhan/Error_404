'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api, Roadmap, RoadmapMilestone, UserRoadmapResponse } from '@/lib/api';
import { MainLayout } from '@/components/layout/Sidebar';
import {
    Map,
    CheckCircle2,
    Circle,
    Clock,
    ChevronDown,
    ChevronUp,
    BookOpen,
    ExternalLink,
    Play,
    Award,
    ArrowRight,
    Sparkles,
    Target,
    Lock,
} from 'lucide-react';

interface RoadmapSummary {
    id: string;
    name: string;
    description: string;
    icon: string;
    color: string;
    estimatedDuration: string;
    totalMilestones: number;
}

export default function RoadmapPage() {
    const { user, loading: authLoading, userId } = useAuth();
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [hasRoadmap, setHasRoadmap] = useState(false);
    const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
    const [overallProgress, setOverallProgress] = useState(0);
    const [completedMilestones, setCompletedMilestones] = useState(0);
    const [totalMilestones, setTotalMilestones] = useState(0);
    const [availableRoadmaps, setAvailableRoadmaps] = useState<RoadmapSummary[]>([]);
    const [expandedMilestone, setExpandedMilestone] = useState<string | null>(null);
    const [updatingMilestone, setUpdatingMilestone] = useState<string | null>(null);

    useEffect(() => {
        if (!authLoading && !user) {
            router.push('/login');
        } else if (userId) {
            loadUserRoadmap();
        }
    }, [user, authLoading, userId]);

    const loadUserRoadmap = async () => {
        if (!userId) return;
        setLoading(true);
        try {
            const result: UserRoadmapResponse = await api.getUserRoadmap(userId);
            if (result.has_roadmap && result.roadmap) {
                setHasRoadmap(true);
                setRoadmap(result.roadmap);
                setOverallProgress(result.overall_progress);
                setCompletedMilestones(result.completed_milestones);
                setTotalMilestones(result.total_milestones);
            } else {
                setHasRoadmap(false);
                // Load available roadmaps
                const roadmapsResult = await api.roadmap.getAvailable();
                setAvailableRoadmaps(roadmapsResult.roadmaps || []);
            }
        } catch (error) {
            console.error('Failed to load roadmap:', error);
            // Load available roadmaps on error
            try {
                const roadmapsResult = await api.roadmap.getAvailable();
                setAvailableRoadmaps(roadmapsResult.roadmaps || []);
            } catch (e) {
                console.error('Failed to load available roadmaps:', e);
            }
        } finally {
            setLoading(false);
        }
    };

    const selectRoadmap = async (domain: string) => {
        if (!userId) return;
        setLoading(true);
        try {
            await api.roadmap.select(userId, domain);
            await loadUserRoadmap();
        } catch (error) {
            console.error('Failed to select roadmap:', error);
        } finally {
            setLoading(false);
        }
    };

    const updateMilestoneStatus = async (milestoneId: string, status: string) => {
        if (!userId) return;
        setUpdatingMilestone(milestoneId);
        try {
            await api.roadmap.updateProgress(userId, milestoneId, status);
            await loadUserRoadmap();
        } catch (error) {
            console.error('Failed to update milestone:', error);
        } finally {
            setUpdatingMilestone(null);
        }
    };

    const getMilestoneIcon = (status: string, isLocked: boolean) => {
        if (isLocked) return <Lock className="text-gray-300" size={24} />;
        switch (status) {
            case 'completed':
                return <CheckCircle2 className="text-green-500" size={24} />;
            case 'in_progress':
                return <Play className="text-blue-500" size={24} />;
            default:
                return <Circle className="text-gray-300" size={24} />;
        }
    };

    const getStatusColor = (status: string, isLocked: boolean) => {
        if (isLocked) return 'border-gray-200 bg-gray-50';
        switch (status) {
            case 'completed':
                return 'border-green-200 bg-green-50';
            case 'in_progress':
                return 'border-blue-200 bg-blue-50';
            default:
                return 'border-gray-200 bg-white';
        }
    };

    const isMilestoneLocked = (milestone: RoadmapMilestone, milestones: RoadmapMilestone[]) => {
        if (!milestone.prerequisites || milestone.prerequisites.length === 0) return false;
        return milestone.prerequisites.some(prereqId => {
            const prereq = milestones.find(m => m.id === prereqId);
            return prereq && prereq.progress.status !== 'completed';
        });
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

    // Show roadmap selection if no roadmap selected
    if (!hasRoadmap) {
        return (
            <MainLayout>
                <div className="space-y-8 animate-fade-in">
                    <div className="text-center max-w-3xl mx-auto">
                        <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
                            <Map className="text-white" size={32} />
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">Choose Your Career Path</h1>
                        <p className="text-gray-500">
                            Select a career roadmap to start your learning journey. Each path includes
                            structured milestones with skills and courses.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {availableRoadmaps.map((rm) => (
                            <div
                                key={rm.id}
                                className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-lg hover:border-green-200 transition-all cursor-pointer group"
                                onClick={() => selectRoadmap(rm.id)}
                            >
                                <div className="flex items-center gap-4 mb-4">
                                    <div
                                        className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl"
                                        style={{ backgroundColor: rm.color + '20' }}
                                    >
                                        {rm.icon}
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-gray-900 text-lg">{rm.name}</h3>
                                        <p className="text-sm text-gray-500">{rm.estimatedDuration}</p>
                                    </div>
                                </div>
                                <p className="text-gray-600 text-sm mb-4">{rm.description}</p>
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-gray-400">
                                        {rm.totalMilestones} milestones
                                    </span>
                                    <span
                                        className="px-4 py-2 rounded-xl text-sm font-medium group-hover:shadow-md transition-all text-white"
                                        style={{ backgroundColor: rm.color }}
                                    >
                                        Start Path
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </MainLayout>
        );
    }

    // Show roadmap with progress
    return (
        <MainLayout>
            <div className="space-y-8 animate-fade-in">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <div
                            className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl"
                            style={{ backgroundColor: (roadmap?.color || '#3b82f6') + '20' }}
                        >
                            {roadmap?.icon || '📊'}
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">{roadmap?.name}</h1>
                            <p className="text-gray-500">{roadmap?.description}</p>
                        </div>
                    </div>
                    <button
                        onClick={async () => {
                            if (userId) {
                                await api.roadmap.remove(userId);
                                setHasRoadmap(false);
                                loadUserRoadmap();
                            }
                        }}
                        className="px-4 py-2 text-sm text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                    >
                        Change Path
                    </button>
                </div>

                {/* Progress Overview */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900">Your Progress</h2>
                            <p className="text-sm text-gray-500">
                                {completedMilestones} of {totalMilestones} milestones completed
                            </p>
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <Target className="text-green-500" size={20} />
                                <span className="text-2xl font-bold text-gray-900">{overallProgress}%</span>
                            </div>
                        </div>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                        <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                                width: `${overallProgress}%`,
                                backgroundColor: roadmap?.color || '#22c55e',
                            }}
                        />
                    </div>
                    <div className="flex justify-between mt-2 text-xs text-gray-400">
                        <span>Start</span>
                        <span>Complete</span>
                    </div>
                </div>

                {/* Milestones */}
                <div className="space-y-4">
                    {roadmap?.milestones.map((milestone, index) => {
                        const locked = isMilestoneLocked(milestone, roadmap.milestones);
                        const isExpanded = expandedMilestone === milestone.id;

                        return (
                            <div key={milestone.id} className="relative">
                                {/* Connector line */}
                                {index < roadmap.milestones.length - 1 && (
                                    <div
                                        className="absolute left-7 top-20 w-0.5 h-8"
                                        style={{
                                            backgroundColor:
                                                milestone.progress.status === 'completed'
                                                    ? roadmap.color
                                                    : '#e5e7eb',
                                        }}
                                    />
                                )}

                                <div
                                    className={`rounded-2xl border-2 overflow-hidden transition-all ${getStatusColor(
                                        milestone.progress.status,
                                        locked
                                    )} ${locked ? 'opacity-60' : ''}`}
                                >
                                    {/* Milestone Header */}
                                    <div
                                        className={`p-6 ${!locked ? 'cursor-pointer' : ''}`}
                                        onClick={() => !locked && setExpandedMilestone(isExpanded ? null : milestone.id)}
                                    >
                                        <div className="flex items-start gap-4">
                                            <div className="mt-1">
                                                {getMilestoneIcon(milestone.progress.status, locked)}
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex items-start justify-between">
                                                    <div>
                                                        <h3 className="font-semibold text-gray-900 text-lg">
                                                            {milestone.name}
                                                        </h3>
                                                        <p className="text-gray-500 text-sm mt-1">
                                                            {milestone.description}
                                                        </p>
                                                    </div>
                                                    {!locked && (
                                                        <button className="p-1 hover:bg-gray-100 rounded-lg transition-all">
                                                            {isExpanded ? (
                                                                <ChevronUp className="text-gray-400" size={20} />
                                                            ) : (
                                                                <ChevronDown className="text-gray-400" size={20} />
                                                            )}
                                                        </button>
                                                    )}
                                                </div>

                                                {/* Meta info */}
                                                <div className="flex flex-wrap items-center gap-4 mt-3">
                                                    <span className="flex items-center gap-1 text-sm text-gray-500">
                                                        <Clock size={14} />
                                                        {milestone.estimated_weeks || milestone.estimatedWeeks} weeks
                                                    </span>
                                                    <span className="flex items-center gap-1 text-sm text-gray-500">
                                                        <Award size={14} />
                                                        {milestone.skills.length} skills
                                                    </span>
                                                    {milestone.skill_completion > 0 && (
                                                        <span className="flex items-center gap-1 text-sm text-green-600">
                                                            <Sparkles size={14} />
                                                            {milestone.skill_completion}% skills acquired
                                                        </span>
                                                    )}
                                                </div>

                                                {/* Mini progress bar */}
                                                {milestone.progress.status === 'in_progress' && (
                                                    <div className="mt-3 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-blue-500 rounded-full"
                                                            style={{ width: `${milestone.skill_completion}%` }}
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Expanded Content */}
                                    {isExpanded && (
                                        <div className="border-t border-gray-100 p-6 bg-white space-y-6">
                                            {/* Skills */}
                                            <div>
                                                <h4 className="font-medium text-gray-900 mb-3">
                                                    Skills You'll Learn
                                                </h4>
                                                <div className="flex flex-wrap gap-2">
                                                    {(milestone.skill_details || []).map((skill: any, i: number) => (
                                                        <span
                                                            key={i}
                                                            className={`px-3 py-1.5 rounded-full text-sm font-medium ${skill.has_skill
                                                                ? 'bg-green-100 text-green-700'
                                                                : 'bg-gray-100 text-gray-700'
                                                                }`}
                                                        >
                                                            {skill.has_skill && <CheckCircle2 className="inline mr-1" size={12} />}
                                                            {skill.name}
                                                            {skill.has_skill && ` (${skill.proficiency}%)`}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Courses */}
                                            {milestone.courses && milestone.courses.length > 0 && (
                                                <div>
                                                    <h4 className="font-medium text-gray-900 mb-3">
                                                        Recommended Courses
                                                    </h4>
                                                    <div className="grid md:grid-cols-2 gap-3">
                                                        {milestone.courses.map((course, i) => (
                                                            <a
                                                                key={i}
                                                                href={course.url}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 hover:border-green-300 hover:shadow-sm transition-all"
                                                            >
                                                                <BookOpen className="text-gray-400" size={20} />
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="font-medium text-gray-900 truncate">
                                                                        {course.course_name || (course as any).name}
                                                                    </p>
                                                                    <p className="text-sm text-gray-500">
                                                                        {course.platform}
                                                                    </p>
                                                                </div>
                                                                <ExternalLink className="text-gray-300" size={16} />
                                                            </a>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Actions */}
                                            <div className="flex gap-3 pt-2">
                                                {milestone.progress.status === 'not_started' && (
                                                    <button
                                                        onClick={() => updateMilestoneStatus(milestone.id, 'in_progress')}
                                                        disabled={updatingMilestone === milestone.id}
                                                        className="px-6 py-2.5 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-all disabled:opacity-50 flex items-center gap-2"
                                                    >
                                                        <Play size={16} />
                                                        {updatingMilestone === milestone.id ? 'Starting...' : 'Start Milestone'}
                                                    </button>
                                                )}
                                                {milestone.progress.status === 'in_progress' && (
                                                    <button
                                                        onClick={() => updateMilestoneStatus(milestone.id, 'completed')}
                                                        disabled={updatingMilestone === milestone.id}
                                                        className="px-6 py-2.5 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 transition-all disabled:opacity-50 flex items-center gap-2"
                                                    >
                                                        <CheckCircle2 size={16} />
                                                        {updatingMilestone === milestone.id ? 'Completing...' : 'Mark Complete'}
                                                    </button>
                                                )}
                                                {milestone.progress.status === 'completed' && (
                                                    <div className="flex items-center gap-2 text-green-600">
                                                        <CheckCircle2 size={20} />
                                                        <span className="font-medium">Completed!</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Completion Banner */}
                {overallProgress === 100 && (
                    <div className="bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl p-8 text-white text-center">
                        <Award className="mx-auto mb-4" size={48} />
                        <h2 className="text-2xl font-bold mb-2">🎉 Congratulations!</h2>
                        <p className="text-green-100 mb-4">
                            You've completed the {roadmap?.name} roadmap! You're now ready to pursue
                            opportunities in this field.
                        </p>
                        <button
                            onClick={() => router.push('/recommendations')}
                            className="px-6 py-3 bg-white text-green-600 rounded-xl font-medium hover:shadow-lg transition-all"
                        >
                            View More Recommendations <ArrowRight className="inline ml-2" size={16} />
                        </button>
                    </div>
                )}
            </div>
        </MainLayout>
    );
}
