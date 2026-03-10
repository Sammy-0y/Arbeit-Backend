import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Briefcase, 
  FileText, 
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  TrendingUp,
  Users
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ClientDashboard = () => {
  const { user, logout, token } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    jobs: 0,
    candidates: 0,
    interviews: null
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const [jobsRes, interviewStatsRes] = await Promise.all([
        axios.get(`${API}/jobs`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/interviews/stats/pipeline`, { headers: { Authorization: `Bearer ${token}` } })
      ]);

      setStats({
        jobs: jobsRes.data.length,
        candidates: jobsRes.data.reduce((sum, job) => sum + (job.candidates_count || 0), 0),
        interviews: interviewStatsRes.data
      });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen ">
      <div className="w-full max-w-7xl mx-auto px-6 py-4">
        <Card className="shadow-lg mb-0 rounded-2xl">
          <CardContent className="p-8">
            <div className="border-l-4 border-teal-500 pl-4">
              <h2 className="text-2xl font-semibold text-blue-900 mb-2">
                Welcome, {user?.name}!
              </h2>
              <p className="text-gray-600 text-lg">
                Full system access enabled. Manage clients, jobs, candidates, and interviews.
              </p>
            </div>
          </CardContent>
        </Card>
          <CardContent className="p-8">
            <div className="space-y-6">
              
              {/* Quick Stats */}
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 mt-2">
                <div className="bg-teal-50 border-2 border-teal-500 rounded-xl p-4 text-center hover:shadow-lg transition">
                  <Briefcase className="h-8 w-8 mx-auto mb-2 text-teal-600" />
                  <p className="text-2xl font-bold text-teal-900">{stats.jobs}</p>
                  <p className="text-sm text-gray-600">Active Jobs</p>
                </div>
                <div className="bg-purple-50 border-2 border-purple-500 rounded-xl p-4 text-center hover:shadow-lg transition">
                  <Users className="h-8 w-8 mx-auto mb-2 text-purple-600" />
                  <p className="text-2xl font-bold text-purple-900">{stats.candidates}</p>
                  <p className="text-sm text-gray-600">Candidates</p>
                </div>
                <div className="bg-amber-50 border-2 border-amber-500 rounded-xl p-4 text-center hover:shadow-lg transition">
                  <Calendar className="h-8 w-8 mx-auto mb-2 text-amber-600" />
                  <p className="text-2xl font-bold text-amber-900">{stats.interviews?.total_interviews || 0}</p>
                  <p className="text-sm text-gray-600">Interviews</p>
                </div>
                <div className="bg-green-50 border-2 border-green-500 rounded-xl p-4 text-center hover:shadow-lg transition">
                  <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-600" />
                  <p className="text-2xl font-bold text-green-900">{stats.interviews?.completed || 0}</p>
                  <p className="text-sm text-gray-600">Completed</p>
                </div>
              </div>
              

              {/* Navigation Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                <Card 
                  className="border-2 border-blue-200 hover:shadow-lg transition-shadow cursor-pointer" 
                  data-testid="client-feature-jobs"
                  onClick={() => navigate('/jobs')}
                >
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-blue-900 mb-2">My Job Requirements</h3>
                    <p className="text-gray-600 text-sm">Create and manage job postings</p>
                    <div className="flex justify-end mt-6">
                    <span className="text-blue-700 font-semibold">
                       Manage →
                    </span>
                    </div>
                  </CardContent>
                </Card>

                <Card 
                  className="border-2 border-blue-200 hover:shadow-lg transition-shadow cursor-pointer" 
                  data-testid="client-feature-candidates"
                  onClick={() => navigate('/candidates')}
                >
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-blue-900 mb-2">Review Candidates</h3>
                    <p className="text-gray-600 text-sm">Review and approve candidates</p>
                    <div className="flex justify-end mt-6">
                    <span className="text-blue-700 font-semibold">
                     Review → 
                    </span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-2 border-blue-200 hover:shadow-lg transition-shadow" data-testid="client-feature-history">
                  <CardContent className="p-6">
                    <h3 className="text-lg font-semibold text-blue-900 mb-2">Hiring History</h3>
                    <p className="text-gray-600 text-sm">Coming soon</p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        

        {/* Interview Pipeline Widget */}
        {stats.interviews && stats.interviews.total_interviews > 0 && (
          <Card className="shadow-xl" data-testid="interview-pipeline-card">
            <CardHeader className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
              <CardTitle className="text-xl flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Interview Pipeline
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                <div className="text-center p-3 bg-amber-50 rounded-lg">
                  <Clock className="h-6 w-6 mx-auto mb-1 text-amber-600" />
                  <p className="text-2xl font-bold text-amber-800">{stats.interviews.awaiting_confirmation}</p>
                  <p className="text-xs text-gray-600">Awaiting</p>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <CheckCircle className="h-6 w-6 mx-auto mb-1 text-blue-600" />
                  <p className="text-2xl font-bold text-blue-800">{stats.interviews.confirmed}</p>
                  <p className="text-xs text-gray-600">Confirmed</p>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <Calendar className="h-6 w-6 mx-auto mb-1 text-green-600" />
                  <p className="text-2xl font-bold text-green-800">{stats.interviews.scheduled}</p>
                  <p className="text-xs text-gray-600">Scheduled</p>
                </div>
                <div className="text-center p-3 bg-teal-50 rounded-lg">
                  <CheckCircle className="h-6 w-6 mx-auto mb-1 text-teal-600" />
                  <p className="text-2xl font-bold text-teal-800">{stats.interviews.completed}</p>
                  <p className="text-xs text-gray-600">Completed</p>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <XCircle className="h-6 w-6 mx-auto mb-1 text-red-600" />
                  <p className="text-2xl font-bold text-red-800">{stats.interviews.no_shows}</p>
                  <p className="text-xs text-gray-600">No Shows</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <XCircle className="h-6 w-6 mx-auto mb-1 text-gray-600" />
                  <p className="text-2xl font-bold text-gray-800">{stats.interviews.cancelled}</p>
                  <p className="text-xs text-gray-600">Cancelled</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
