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
        graduation_year: '',
        location: '',
        target_role: '',
        phone: '',
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
                graduation_year: user.graduation_year?.toString() || '',
                location: user.location || '',
                target_role: user.target_role || '',
                phone: user.phone || '',
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
            const dataToSave = {
                ...formData,
                graduation_year: formData.graduation_year ? parseInt(formData.graduation_year) : undefined,
            };
            await api.updateUser(userId, dataToSave);
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
            await refreshUser(); // Refresh to update completion score
            setMessage({
                type: 'success',
                text: `Skills extracted! Found ${result.total_skills_extracted || 'multiple'} skills from your resume and profile.`,
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
            await refreshUser(); // Refresh to update completion score
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

    const handleLinkedInAnalysis = async () => {
        if (!userId || !formData.linkedin_url) {
            setMessage({ type: 'error', text: 'Please enter a LinkedIn URL first' });
            return;
        }
        setLoading(true);
        setMessage(null);
        try {
            // First save the LinkedIn URL
            await api.updateUser(userId, { linkedin_url: formData.linkedin_url });
            // Then analyze
            const result = await api.analyzeLinkedIn(userId, formData.linkedin_url);
            await loadSkills();
            await refreshUser(); // Refresh to update completion score
            setMessage({
                type: 'success',
                text: `LinkedIn analyzed! Found ${result.skills_found || 0} skills from your profile.`,
            });
        } catch (error: any) {
            setMessage({ type: 'error', text: error.message || 'Failed to analyze LinkedIn' });
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
        if (skill.sources) {
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

    const completion = user?.profile_completion || 0;

    return (
        <MainLayout>
            <div className="max-w-4xl mx-auto space-y-8 animate-fade-in pb-12">
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 border-b-4 border-green-500 w-fit pb-1">Profile Settings</h1>
                        <p className="text-gray-500 mt-2">Manage your professional identity and skills</p>
                    </div>
                    <div className="bg-white p-4 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-4 min-w-[240px]">
                        <div className="relative w-16 h-16">
                            <svg className="w-full h-full transform -rotate-90">
                                <circle
                                    cx="32"
                                    cy="32"
                                    r="28"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                    fill="transparent"
                                    className="text-gray-100"
                                />
                                <circle
                                    cx="32"
                                    cy="32"
                                    r="28"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                    fill="transparent"
                                    strokeDasharray={28 * 2 * Math.PI}
                                    strokeDashoffset={28 * 2 * Math.PI * (1 - completion / 100)}
                                    className="text-green-500 transition-all duration-1000 ease-out"
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <span className="text-sm font-bold text-gray-900">{Math.round(completion)}%</span>
                            </div>
                        </div>
                        <div>
                            <p className="text-sm font-semibold text-gray-900">Profile Completion</p>
                            <p className="text-xs text-gray-500">Increase score by adding info</p>
                        </div>
                    </div>
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
                    <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                        <User className="text-green-500" size={20} />
                        Basic Information
                    </h2>
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
                            <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
                            <div className="relative">
                                <CheckCircle className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <input
                                    type="tel"
                                    value={formData.phone}
                                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900"
                                    placeholder="+1 (555) 000-0000"
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
                    </div>
                </div>

                {/* Education & Career */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                        <GraduationCap className="text-green-500" size={20} />
                        Education & Career
                    </h2>
                    <div className="grid md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Degree / Major</label>
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
                            <label className="block text-sm font-medium text-gray-700 mb-2">University / College</label>
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
                            <label className="block text-sm font-medium text-gray-700 mb-2">Graduation Year</label>
                            <div className="relative">
                                <Target className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <input
                                    type="number"
                                    value={formData.graduation_year}
                                    onChange={(e) => setFormData({ ...formData, graduation_year: e.target.value })}
                                    className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent text-gray-900"
                                    placeholder="2024"
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
                        {loading ? 'Saving...' : 'Save Profile Details'}
                    </button>
                </div>

                {/* Connected Accounts */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                        <RefreshCw className="text-green-500" size={20} />
                        Connected Accounts
                    </h2>
                    <div className="space-y-4">
                        <div className="flex flex-col sm:flex-row items-center gap-4 p-4 border border-gray-200 rounded-xl">
                            <div className="w-12 h-12 bg-gray-900 rounded-xl flex items-center justify-center shrink-0">
                                <Github className="text-white" size={24} />
                            </div>
                            <div className="flex-1 w-full">
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
                                className="w-full sm:w-auto px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                                Analyze GitHub
                            </button>
                        </div>
                        <div className="flex flex-col sm:flex-row items-center gap-4 p-4 border border-gray-200 rounded-xl">
                            <div className="w-12 h-12 bg-[#0077b5] rounded-xl flex items-center justify-center shrink-0">
                                <Linkedin className="text-white" size={24} />
                            </div>
                            <div className="flex-1 w-full">
                                <input
                                    type="url"
                                    value={formData.linkedin_url}
                                    onChange={(e) => setFormData({ ...formData, linkedin_url: e.target.value })}
                                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0077b5] text-gray-900"
                                    placeholder="https://linkedin.com/in/username"
                                />
                            </div>
                            <button
                                onClick={handleLinkedInAnalysis}
                                disabled={loading}
                                className="w-full sm:w-auto px-4 py-2 bg-[#0077b5] text-white rounded-lg hover:bg-[#006396] transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                                Analyze LinkedIn
                            </button>
                        </div>
                    </div>
                </div>

                {/* Resume Upload */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                        <Upload className="text-green-500" size={20} />
                        Resume Analysis
                    </h2>
                    <p className="text-gray-500 text-sm mb-4">Upload your resume to automatically extract skills, projects, and work experience</p>

                    <div className="flex flex-col sm:flex-row gap-4">
                        <label className="flex-1 flex items-center justify-center gap-3 p-8 border-2 border-dashed border-gray-200 rounded-xl cursor-pointer hover:border-green-500 hover:bg-green-50/50 transition-colors">
                            <Upload className="text-gray-400" size={24} />
                            <span className="text-gray-600 font-medium">
                                {user?.has_resume ? 'Replace current resume' : 'Click to upload resume (PDF, DOCX, TXT)'}
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
                        <div className="mt-4 p-4 bg-green-50 rounded-xl flex items-center justify-between border border-green-100">
                            <div className="flex items-center gap-3">
                                <CheckCircle className="text-green-600" size={20} />
                                <span className="text-green-700 font-medium">Resume detected and ready for extraction</span>
                            </div>
                            <button
                                onClick={handleExtractSkills}
                                disabled={extracting}
                                className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-medium hover:shadow-lg transition-all disabled:opacity-50 flex items-center gap-2"
                            >
                                <Sparkles size={16} className={extracting ? 'animate-pulse' : ''} />
                                {extracting ? 'Extracting...' : 'Extract All Skills'}
                            </button>
                        </div>
                    )}
                </div>

                {/* Skills Display */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                    <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center gap-2">
                        <Sparkles className="text-green-500" size={20} />
                        Your Intelligence Quotient ({skills.length} Skills)
                    </h2>

                    {skills.length === 0 ? (
                        <div className="text-center py-12 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
                            <Sparkles size={48} className="mx-auto mb-4 text-gray-300" />
                            <p className="text-gray-500 font-medium">No skills extracted yet.</p>
                            <p className="text-sm text-gray-400 mt-1">Upload your resume or connect accounts to see your skill profile.</p>
                        </div>
                    ) : (
                        <div className="space-y-8">
                            {Object.entries(skillsBySource).sort().map(([source, sourceSkills]) => (
                                <div key={source} className="group">
                                    <div className="flex items-center gap-2 mb-4">
                                        <div className={`w-2 h-2 rounded-full ${source === 'resume' ? 'bg-green-500' :
                                            source === 'github' ? 'bg-gray-900' :
                                                source === 'linkedin' ? 'bg-blue-600' :
                                                    'bg-purple-500'
                                            }`} />
                                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
                                            Extracted from {source}
                                        </h3>
                                        <span className="text-xs text-gray-400 ml-auto">
                                            {sourceSkills.length} skills found
                                        </span>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {sourceSkills.map((skill) => (
                                            <div
                                                key={`${source}-${skill.skill_name}`}
                                                className="px-4 py-2 bg-gray-50 border border-gray-100 text-gray-700 rounded-xl text-sm flex items-center gap-3 hover:border-green-200 hover:bg-white hover:shadow-sm transition-all cursor-default"
                                            >
                                                <span className="font-semibold">{skill.skill_name}</span>
                                                <div className="w-px h-3 bg-gray-200" />
                                                <span className="text-xs font-bold text-green-600">
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
