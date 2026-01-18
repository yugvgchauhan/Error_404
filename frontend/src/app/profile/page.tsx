'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { api, Skill } from '@/lib/api';
import { MainLayout } from '@/components/layout/Sidebar';
import {
    User,
    Mail,
    GraduationCap,
    Github,
    Linkedin,
    Upload,
    RefreshCw,
    CheckCircle,
    AlertCircle,
    Target,
    MapPin,
    Building,
    Sparkles,
} from 'lucide-react';

export default function ProfilePage() {
    const { user, profile, refreshUser, loading: authLoading, userId } = useAuth();
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [extracting, setExtracting] = useState(false);
    const [skills, setSkills] = useState<Skill[]>([]);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const [formData, setFormData] = useState({
        name: '',
        education: '',
        university: '',
        location: '',
        target_role: '',
        github_url: '',
        linkedin_url: '',
    });

    useEffect(() => {
        if (!authLoading && !user) {
            router.push('/login');
        } else if (user) {
            setFormData({
                name: user.name || '',
                education: user.education || '',
                university: user.university || '',
                location: user.location || '',
                target_role: user.target_role || '',
                github_url: user.github_url || '',
                linkedin_url: user.linkedin_url || '',
            });
            loadSkills();
        }
    }, [user, authLoading]);

    const loadSkills = async () => {
        if (!userId) return;
        try {
            const data = await api.getUserSkills(userId);
            setSkills(data);
        } catch (error) {
            console.error('Failed to load skills:', error);
        }
    };

    const handleSave = async () => {
        if (!userId) return;
        setLoading(true);
        setMessage(null);
        try {
            await api.updateUser(userId, formData);
            await refreshUser();
            setMessage({ type: 'success', text: 'Profile updated successfully!' });
        } catch (error: any) {
            setMessage({ type: 'error', text: error.message || 'Failed to update profile' });
        } finally {
            setLoading(false);
        }
    };

    const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file || !userId) return;

        setLoading(true);
        setMessage(null);
        try {
            await api.uploadResume(userId, file);
            await refreshUser();
            setMessage({
                type: 'success',
                text: 'Resume uploaded successfully! Click "Extract Skills" to analyze it.',
            });
        } catch (error: any) {
            setMessage({ type: 'error', text: error.message || 'Failed to upload resume' });
        } finally {
            setLoading(false);
        }
    };

    const handleExtractSkills = async () => {
        if (!userId) return;
        setExtracting(true);
        setMessage(null);
        try {
            const result = await api.extractSkills(userId);
            await loadSkills();
            setMessage({
                type: 'success',
                text: `Skills extracted! Found ${result.skills_extracted || 'multiple'} skills from your resume and profile.`,
            });
        } catch (error: any) {
            setMessage({ type: 'error', text: error.message || 'Failed to extract skills' });
        } finally {
            setExtracting(false);
        }
    };

    const handleGitHubAnalysis = async () => {
        if (!userId || !formData.github_url) {
            setMessage({ type: 'error', text: 'Please enter a GitHub URL first' });
            return;
        }
        setLoading(true);
        setMessage(null);
        try {
            // First save the GitHub URL
            await api.updateUser(userId, { github_url: formData.github_url });
            // Then analyze
            const result = await api.analyzeGitHub(userId, formData.github_url);
            await loadSkills();
            setMessage({
                type: 'success',
                text: `GitHub analyzed! Found ${result.skills_found || 0} skills from ${result.repos_analyzed || 0} repositories.`,
            });
        } catch (error: any) {
            setMessage({ type: 'error', text: error.message || 'Failed to analyze GitHub' });
        } finally {
            setLoading(false);
        }
    };

    if (authLoading) {
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
        if (typeof skill.sources === 'string') {
            try {
                const parsed = JSON.parse(skill.sources);
                sources = Array.isArray(parsed) ? parsed : [skill.sources];
            } catch {
                sources = skill.sources.split(',').map(s => s.trim());
            }
        } else if (Array.isArray(skill.sources)) {
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

    return (
        <MainLayout>
            <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Profile Settings</h1>
                    <p className="text-gray-500 mt-1">Manage your information and extract skills</p>
                </div>

                {message && (
                    <div
                        className={`p-4 rounded-xl flex items-center gap-3 ${message.type === 'success'
                            ? 'bg-green-50 text-green-700 border border-green-200'
                            : 'bg-red-50 text-red-700 border border-red-200'
                            }`}
                    >
                        {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
                        {message.text}
                    </div>
                )}

                {/* Basic Info */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-6">Basic Information</h2>
                    <div className="grid md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                            <div className="relative">
                                <User className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900"
                                    placeholder="John Doe"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                            <div className="relative">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <input
                                    type="email"
                                    value={user?.email || ''}
                                    disabled
                                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl bg-gray-50 text-gray-500"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Education</label>
                            <div className="relative">
                                <GraduationCap className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <input
                                    type="text"
                                    value={formData.education}
                                    onChange={(e) => setFormData({ ...formData, education: e.target.value })}
                                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900"
                                    placeholder="B.Tech in Computer Science"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">University</label>
                            <div className="relative">
                                <Building className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <input
                                    type="text"
                                    value={formData.university}
                                    onChange={(e) => setFormData({ ...formData, university: e.target.value })}
                                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900"
                                    placeholder="MIT"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Location</label>
                            <div className="relative">
                                <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <input
                                    type="text"
                                    value={formData.location}
                                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900"
                                    placeholder="New York, USA"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Target Role</label>
                            <div className="relative">
                                <Target className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <input
                                    type="text"
                                    value={formData.target_role}
                                    onChange={(e) => setFormData({ ...formData, target_role: e.target.value })}
                                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900"
                                    placeholder="Healthcare Data Analyst"
                                />
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={handleSave}
                        disabled={loading}
                        className="mt-6 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-medium hover:shadow-lg transition-all disabled:opacity-50"
                    >
                        {loading ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>

                {/* Connected Accounts */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-6">Connected Accounts</h2>
                    <div className="space-y-4">
                        <div className="flex items-center gap-4 p-4 border border-gray-200 rounded-xl">
                            <div className="w-12 h-12 bg-gray-900 rounded-xl flex items-center justify-center">
                                <Github className="text-white" size={24} />
                            </div>
                            <div className="flex-1">
                                <input
                                    type="url"
                                    value={formData.github_url}
                                    onChange={(e) => setFormData({ ...formData, github_url: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 text-gray-900"
                                    placeholder="https://github.com/username"
                                />
                            </div>
                            <button
                                onClick={handleGitHubAnalysis}
                                disabled={loading}
                                className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors flex items-center gap-2 disabled:opacity-50"
                            >
                                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                                Analyze
                            </button>
                        </div>
                        <div className="flex items-center gap-4 p-4 border border-gray-200 rounded-xl">
                            <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
                                <Linkedin className="text-white" size={24} />
                            </div>
                            <div className="flex-1">
                                <input
                                    type="url"
                                    value={formData.linkedin_url}
                                    onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                                    placeholder="https://linkedin.com/in/username"
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Resume Upload */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Resume</h2>
                    <p className="text-gray-500 text-sm mb-4">Upload your resume to automatically extract skills</p>

                    <div className="flex flex-col sm:flex-row gap-4">
                        <label className="flex-1 flex items-center justify-center gap-3 p-8 border-2 border-dashed border-gray-200 rounded-xl cursor-pointer hover:border-green-500 hover:bg-green-50/50 transition-colors">
                            <Upload className="text-gray-400" size={24} />
                            <span className="text-gray-600">
                                {user?.has_resume ? 'Replace resume (PDF, DOCX, TXT)' : 'Click to upload resume'}
                            </span>
                            <input
                                type="file"
                                accept=".pdf,.docx,.doc,.txt"
                                onChange={handleResumeUpload}
                                className="hidden"
                            />
                        </label>
                    </div>

                    {user?.has_resume && (
                        <div className="mt-4 p-4 bg-green-50 rounded-xl flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <CheckCircle className="text-green-600" size={20} />
                                <span className="text-green-700">Resume uploaded</span>
                            </div>
                            <button
                                onClick={handleExtractSkills}
                                disabled={extracting}
                                className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50 flex items-center gap-2"
                            >
                                <Sparkles size={16} className={extracting ? 'animate-pulse' : ''} />
                                {extracting ? 'Extracting...' : 'Extract Skills'}
                            </button>
                        </div>
                    )}
                </div>

                {/* Skills */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                        Your Skills ({skills.length})
                    </h2>

                    {skills.length === 0 ? (
                        <div className="text-center py-8 text-gray-400">
                            <Sparkles size={48} className="mx-auto mb-4 opacity-50" />
                            <p>No skills extracted yet. Upload your resume to get started!</p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {Object.entries(skillsBySource).map(([source, sourceSkills]) => (
                                <div key={source}>
                                    <h3 className="text-sm font-medium text-gray-500 mb-3 capitalize">
                                        From {source}
                                    </h3>
                                    <div className="flex flex-wrap gap-2">
                                        {sourceSkills.map((skill) => (
                                            <div
                                                key={skill.id}
                                                className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-full text-sm flex items-center gap-2"
                                            >
                                                <span>{skill.skill_name}</span>
                                                <span className="text-xs text-gray-400">
                                                    {Math.round(skill.proficiency * 100)}%
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </MainLayout>
    );
}
