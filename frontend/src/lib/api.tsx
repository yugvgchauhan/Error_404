// API client for the SkillPath backend
import { User } from './auth';

// API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Exporting user from auth to maintain consistency
export type { User };

// Types
export interface Skill {
    id: number;
    user_id: number;
    skill_name: string;
    proficiency: number;
    confidence: number;
    source_count?: number;
    sources?: string[]; // Backend returns parsed JSON array
    created_at?: string;
}

export interface Course {
    id?: number;
    user_id?: number;
    course_name: string;
    platform: string;
    instructor?: string;
    grade?: string;
    completion_date?: string;
    duration?: string;
    description?: string;
    certificate_url?: string;
    skills_extracted?: string[];
}

export interface Project {
    id?: number;
    user_id?: number;
    project_name: string;
    description: string;
    tech_stack: string[];
    role?: string;
    team_size?: number;
    duration?: string;
    github_link?: string;
    deployed_link?: string;
    project_type?: string;
    impact?: string;
    skills_extracted?: string[];
    created_at?: string;
}

export interface Recommendation {
    skill: string;
    gap_priority: 'critical' | 'important';
    courses: Array<{
        title: string;
        platform: string;
        url: string;
        duration?: string;
        level?: string;
        rating?: number;
    }>;
}

export interface GapItem {
    skill: string;
    user_proficiency: number;
    market_importance: number;
    gap_score: number;
    priority: 'critical' | 'important' | 'emerging';
}

export interface GapAnalysis {
    message: string;
    user_id: number;
    target_role: string;
    user_skills_count: number;
    market_skills_count: number;
    overall_readiness: number;
    summary: {
        interpretation: string;
        top_3_priorities: string[];
        status: string;
    };
    critical_gaps: GapItem[];
    important_gaps: GapItem[];
    emerging_gaps: GapItem[];
    strengths: any[];
}

export interface RoadmapMilestone {
    id: string;
    title: string;
    description: string;
    skills: string[];
    duration: string;
    resources: Array<{
        title: string;
        type: string;
        url: string;
    }>;
    progress: {
        status: 'not_started' | 'in_progress' | 'completed';
        started_at: string | null;
        completed_at: string | null;
    };
    skillCompletion: number;
    skillDetails: Array<{
        name: string;
        hasSkill: boolean;
        proficiency: number;
    }>;
}

export interface Roadmap {
    id: string;
    name: string;
    description: string;
    icon: string;
    color: string;
    estimatedDuration: string;
    milestones: RoadmapMilestone[];
}

export interface UserRoadmapResponse {
    message: string;
    has_roadmap: boolean;
    domain?: string;
    started_at?: string;
    overall_progress: number;
    completed_milestones: number;
    total_milestones: number;
    roadmap: Roadmap | null;
}

// Helper function for API calls
async function apiCall<T>(
    endpoint: string,
    options?: RequestInit
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers,
            },
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API call failed: ${endpoint}`, error);
        throw error;
    }
}

// API object with all endpoints
export const api = {
    // User endpoints
    users: {
        getByEmail: (email: string) =>
            apiCall<User>(`/api/users/email/${encodeURIComponent(email)}`),

        getById: (userId: number) =>
            apiCall<User>(`/api/users/${userId}`),

        create: (userData: Partial<User>) =>
            apiCall<User>('/api/users/register', {
                method: 'POST',
                body: JSON.stringify(userData),
            }),

        update: (userId: number, userData: Partial<User>) =>
            apiCall<User>(`/api/users/${userId}`, {
                method: 'PUT',
                body: JSON.stringify(userData),
            }),

        delete: (userId: number) =>
            apiCall<{ message: string }>(`/api/users/${userId}`, {
                method: 'DELETE',
            }),
    },

    // Skills endpoints
    skills: {
        getByUser: (userId: number) =>
            apiCall<Skill[]>(`/api/skills/users/${userId}`),

        add: (skillData: Partial<Skill>) =>
            apiCall<Skill>('/api/skills/', {
                method: 'POST',
                body: JSON.stringify(skillData),
            }),

        update: (skillId: number, skillData: Partial<Skill>) =>
            apiCall<Skill>(`/api/skills/${skillId}`, {
                method: 'PUT',
                body: JSON.stringify(skillData),
            }),

        extract: (userId: number) =>
            apiCall<{ message: string; total_skills_extracted: number; skills: any }>(`/api/skills/extract/${userId}`, {
                method: 'POST',
            }),

        delete: (userId: number) =>
            apiCall<{ message: string }>(`/api/skills/users/${userId}`, {
                method: 'DELETE',
            }),
    },

    // Courses endpoints
    courses: {
        getByUser: (userId: number) =>
            apiCall<Course[]>(`/api/users/${userId}/courses`),

        search: (skill: string) =>
            apiCall<any[]>(`/api/courses/search/${encodeURIComponent(skill)}`),

        add: (userId: number, courseData: Partial<Course>) =>
            apiCall<Course>(`/api/users/${userId}/courses`, {
                method: 'POST',
                body: JSON.stringify(courseData),
            }),
    },

    // Projects endpoints
    projects: {
        getByUser: (userId: number) =>
            apiCall<Project[]>(`/api/users/${userId}/projects`),

        add: (userId: number, projectData: Partial<Project>) =>
            apiCall<Project>(`/api/users/${userId}/projects`, {
                method: 'POST',
                body: JSON.stringify(projectData),
            }),

        analyzeGithub: (userId: number, githubUrl: string) =>
            apiCall<{ skills: string[]; skills_found?: number; repos_analyzed?: number }>('/api/projects/analyze-github', {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, github_url: githubUrl }),
            }),
    },

    // Resume endpoints
    resume: {
        upload: (userId: number, file: File) => {
            const formData = new FormData();
            formData.append('file', file);

            return fetch(`${API_BASE_URL}/api/users/${userId}/resume/upload`, {
                method: 'POST',
                body: formData,
            }).then(async (response) => {
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || 'Resume upload failed');
                }
                return response.json();
            });
        },
        uploadText: (userId: number, resumeText: string) =>
            apiCall<any>(`/api/users/${userId}/resume/upload-text`, {
                method: 'POST',
                body: JSON.stringify({ resume_text: resumeText }),
            }),
    },

    // Analysis endpoints
    analysis: {
        getGapAnalysis: (userId: number, jobTitle?: string, location?: string) => {
            const params = new URLSearchParams();
            if (jobTitle) params.append('job_title', jobTitle);
            if (location) params.append('location', location);
            const queryString = params.toString() ? `?${params.toString()}` : '';
            return apiCall<GapAnalysis>(`/api/users/${userId}/gap-analysis${queryString}`);
        },
        getRecommendedCourses: (userId: number) =>
            apiCall<{ recommendations: Recommendation[] }>(`/api/users/${userId}/recommended-courses`),

        analyzeGitHub: async (userId: number, githubUrl: string) => {
            const response = await fetch(`${API_BASE_URL}/api/users/${userId}/analyze-github?github_url=${encodeURIComponent(githubUrl)}`, {
                method: 'POST',
            });
            if (!response.ok) throw new Error('GitHub analysis failed');
            return response.json();
        },

        analyzeLinkedIn: async (userId: number, linkedinUrl: string) => {
            const response = await fetch(`${API_BASE_URL}/api/users/${userId}/analyze-linkedin?linkedin_url=${encodeURIComponent(linkedinUrl)}`, {
                method: 'POST',
            });
            if (!response.ok) throw new Error('LinkedIn analysis failed');
            return response.json();
        },
        completeAnalysis: (userId: number, targetJob?: string, location?: string) => {
            const params = new URLSearchParams();
            if (targetJob) params.append('target_job', targetJob);
            if (location) params.append('location', location);
            const queryString = params.toString() ? `?${params.toString()}` : '';
            return apiCall<any>(`/api/users/${userId}/complete-analysis${queryString}`, {
                method: 'POST',
            });
        },
    },

    // Roadmap endpoints
    roadmap: {
        getAvailable: () =>
            apiCall<{ roadmaps: any[] }>('/api/roadmaps'),

        getUserRoadmap: (userId: number) =>
            apiCall<UserRoadmapResponse>(`/api/users/${userId}/roadmap`),

        select: (userId: number, domain: string) =>
            apiCall<any>(`/api/users/${userId}/roadmap/select`, {
                method: 'POST',
                body: JSON.stringify({ domain }),
            }),

        updateProgress: (userId: number, milestoneId: string, status: string) =>
            apiCall<any>(`/api/users/${userId}/roadmap/progress`, {
                method: 'PUT',
                body: JSON.stringify({ milestone_id: milestoneId, status }),
            }),

        remove: (userId: number) =>
            apiCall<any>(`/api/users/${userId}/roadmap`, {
                method: 'DELETE',
            }),
    },

    // Jobs endpoints
    jobs: {
        search: (title?: string, location?: string) => {
            const params = new URLSearchParams();
            if (title) params.append('title', title);
            if (location) params.append('location', location);
            return apiCall<any>(`/api/jobs/search?${params.toString()}`);
        },
    },

    // Recommendations endpoints
    recommendations: {
        get: (userId: number) =>
            apiCall<{ recommendations: Recommendation[] }>(`/api/users/${userId}/recommendations`),
    },

    // Convenience methods (maintain backward compatibility where possible but update implementation)
    getUserSkills: (userId: number) => api.skills.getByUser(userId),
    getGapAnalysis: (userId: number, jobTitle?: string) => api.analysis.getGapAnalysis(userId, jobTitle),
    updateUser: (userId: number, userData: Partial<User>) => api.users.update(userId, userData),
    uploadResume: (userId: number, file: File) => api.resume.upload(userId, file),
    extractSkills: (userId: number) => api.skills.extract(userId),
    analyzeGitHub: (userId: number, githubUrl: string) => api.analysis.analyzeGitHub(userId, githubUrl),
    analyzeLinkedIn: (userId: number, linkedinUrl: string) => api.analysis.analyzeLinkedIn(userId, linkedinUrl),
    getRecommendedCourses: (userId: number) => api.analysis.getRecommendedCourses(userId),
    searchCoursesForSkill: (skill: string) => apiCall<{ courses: any[] }>(`/api/courses/search/${encodeURIComponent(skill)}`),
    getUserRoadmap: (userId: number) => api.roadmap.getUserRoadmap(userId),
    getRoadmaps: () => api.roadmap.getAvailable(),
    selectRoadmap: (userId: number, domain: string) => api.roadmap.select(userId, domain),
    updateMilestoneProgress: (userId: number, milestoneId: string, status: string) => api.roadmap.updateProgress(userId, milestoneId, status),
    removeUserRoadmap: (userId: number) => api.roadmap.remove(userId),
};
