import React, { useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { useCandidateAuth } from '../../contexts/CandidateAuthContext';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { toast } from 'sonner';
import logo from "@/assets/logo.png";
import { User, Mail, Lock, Phone, Linkedin, Building, Calendar, Key, AlertTriangle } from 'lucide-react';

export const CandidateLogin = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, changePassword } = useCandidateAuth();
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [passwordChangeData, setPasswordChangeData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    phone: '',
    linkedin_url: '',
    current_company: '',
    experience_years: ''
  });

  // Get redirect URL if present
  const redirectTo = searchParams.get('redirect') || '/candidate/dashboard';

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const result = await login(formData.email, formData.password);
      
      // Check if password change is required
      if (result.must_change_password) {
        setShowPasswordChange(true);
        setPasswordChangeData(prev => ({ ...prev, currentPassword: formData.password }));
        toast.info('Please change your password to continue');
      } else {
        toast.success('Login successful!');
        navigate(redirectTo);
      }
    } catch (error) {
      toast.error(error.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (passwordChangeData.newPassword !== passwordChangeData.confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    
    if (passwordChangeData.newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setLoading(true);
    
    try {
      await changePassword(passwordChangeData.currentPassword, passwordChangeData.newPassword);
      toast.success('Password changed successfully!');
      navigate(redirectTo);
    } catch (error) {
      toast.error(error.message || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/candidate-portal/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          experience_years: formData.experience_years ? parseInt(formData.experience_years) : null
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Registration failed');
      }

      toast.success('Registration successful! Please login.');
      setIsRegister(false);
      setFormData(prev => ({ ...prev, password: '' }));
    } catch (error) {
      toast.error(error.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Password Change Modal
  if (showPasswordChange) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center p-4">
      
          <Card className="border-0 shadow-2xl">
            <CardHeader className="text-center pb-2">
              <div className="mx-auto w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
                <Key className="h-8 w-8 text-amber-600" />
              </div>
              <CardTitle className="text-2xl font-bold text-gray-900">Change Your Password</CardTitle>
              <p className="text-gray-500 mt-2">For security, please set a new password</p>
            </CardHeader>
            <CardContent>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-amber-800">First-time login detected</p>
                    <p className="text-sm text-amber-700 mt-1">You must change your temporary password before accessing the portal.</p>
                  </div>
                </div>
              </div>
              
              <form onSubmit={handlePasswordChange} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="newPassword">New Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="newPassword"
                      type="password"
                      placeholder="Enter new password"
                      className="pl-10"
                      value={passwordChangeData.newPassword}
                      onChange={(e) => setPasswordChangeData(prev => ({ ...prev, newPassword: e.target.value }))}
                      required
                      minLength={6}
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm New Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      id="confirmPassword"
                      type="password"
                      placeholder="Confirm new password"
                      className="pl-10"
                      value={passwordChangeData.confirmPassword}
                      onChange={(e) => setPasswordChangeData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                      required
                      minLength={6}
                    />
                  </div>
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700"
                  disabled={loading}
                >
                  {loading ? 'Changing Password...' : 'Set New Password'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
        );
}
return (

  <div className="min-h-screen relative flex flex-col lg:flex-row">

    {/* ===== Mobile Background Image ===== */}
    <div
      className="lg:hidden absolute inset-0 bg-cover bg-center"
      style={{
        backgroundImage: `url(${process.env.PUBLIC_URL}/candidate-portal.png)`
      }}
    />

    {/* ===== Dark Overlay For Mobile ===== */}
    <div className="lg:hidden absolute inset-0 bg-black/40" />

    {/* ===== LEFT SIDE (Desktop Only) ===== */}
    <div
      className="hidden lg:block lg:w-1/2 bg-cover bg-center"
      style={{
        backgroundImage: `url(${process.env.PUBLIC_URL}/candidate-portal.png)`
      }}
    />

    {/* ===== RIGHT SIDE ===== */}
    <div className="relative flex w-full lg:w-1/2 items-center justify-center p-6 lg:p-8">

    

{/* Glass Card Effect */}
<div className="w-full max-w-md bg-white/90 backdrop-blur-md rounded-3xl p-8 shadow-xl">
<div className="flex justify-center mb-6">
  <img 
    src={logo} 
    alt="Arbeit Logo" 
    className="h-16 w-auto object-contain"
  />
</div>
        <h1 className="text-3xl lg:text-4xl font-bold text-center mb-2">
          Welcome To the Future
        </h1>

        <p className="text-gray-600 text-center mb-8">
          Please login to your account
        </p>

        <form
          onSubmit={isRegister ? handleRegister : handleLogin}
          className="space-y-6"
        >
          <Input
            type="email"
            placeholder="Email address"
            className="h-14 rounded-2xl bg-gray-100 border-none"
            value={formData.email}
            onChange={(e) => updateField("email", e.target.value)}
            required
          />

          <Input
            type="password"
            placeholder="Password"
            className="h-14 rounded-2xl bg-gray-100 border-none"
            value={formData.password}
            onChange={(e) => updateField("password", e.target.value)}
            required
          />

          <Button
            type="submit"
            className="w-full h-14 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white text-lg font-semibold"
          >
            Login
          </Button>
        </form>

      </div>
    </div>
</div>
);
};