import React, { useState } from 'react';
import APIClient from '@/lib/services/api';
import { useAuth } from '@hooks/useAuth';

interface User {
  user_id: string;
  email: string;
  role: string;
  created_at: string;
}

interface UserFormData {
  email: string;
  role: string;
}

export const UserManagementTable: React.FC = () => {
  const { user: authUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    role: 'viewer',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!authUser?.tenant_id) {
      setError('No tenant ID found. Please log in.');
      return;
    }

    if (!formData.email.trim()) {
      setError('Email is required');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError('Invalid email format');
      return;
    }

    setIsSubmitting(true);

    try {
      const client = new APIClient();
      const response = await client.createUser(
        authUser.tenant_id,
        formData.email,
        formData.role
      );

      const newUser: User = {
        user_id: response.data.user_id,
        email: formData.email,
        role: formData.role,
        created_at: new Date().toISOString(),
      };

      setUsers((prev) => [newUser, ...prev]);
      setSuccess(`User ${formData.email} created successfully!`);
      setFormData({ email: '', role: 'viewer' });
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to create user. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof UserFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="card">
      <h3 className="text-xl font-bold text-carbon-black mb-4">User Management</h3>

      <form onSubmit={handleSubmit} className="space-y-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="user-email" className="block text-sm font-medium text-charcoal-brown mb-2">
              Email *
            </label>
            <input
              id="user-email"
              type="email"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              className="w-full border border-subtle rounded px-3 py-2 text-carbon-black focus:outline-none focus:ring-2 focus:ring-charcoal-brown"
              placeholder="user@example.com"
              required
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="user-role" className="block text-sm font-medium text-charcoal-brown mb-2">
              Role *
            </label>
            <select
              id="user-role"
              value={formData.role}
              onChange={(e) => handleChange('role', e.target.value)}
              className="w-full border border-subtle rounded px-3 py-2 text-carbon-black focus:outline-none focus:ring-2 focus:ring-charcoal-brown"
              disabled={isSubmitting}
            >
              <option value="viewer">Viewer</option>
              <option value="operator">Operator</option>
              <option value="admin">Admin</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-blood-red rounded p-3">
            <p className="text-sm text-blood-red">{error}</p>
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-500 rounded p-3">
            <p className="text-sm text-green-700">{success}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting || !authUser?.tenant_id}
          className="btn-primary px-6 py-2 rounded font-medium disabled:opacity-50 flex items-center gap-2"
        >
          {isSubmitting && (
            <div className="animate-spin h-4 w-4 border-2 border-floral-white border-t-transparent rounded-full" />
          )}
          {isSubmitting ? 'Creating...' : 'Add User'}
        </button>
      </form>

      {users.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="border-b border-subtle">
                <th className="text-left py-3 px-4 text-sm font-medium text-charcoal-brown">Email</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-charcoal-brown">Role</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-charcoal-brown">User ID</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-charcoal-brown">Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id} className="border-b border-subtle hover:bg-floral-white">
                  <td className="py-3 px-4 text-sm text-carbon-black">{u.email}</td>
                  <td className="py-3 px-4">
                    <span className="badge-review">{u.role}</span>
                  </td>
                  <td className="py-3 px-4 font-mono text-xs text-charcoal-brown">
                    {u.user_id.substring(0, 8)}...
                  </td>
                  <td className="py-3 px-4 text-sm text-charcoal-brown">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {users.length === 0 && (
        <div className="text-center py-8 text-charcoal-brown">
          No users created yet. Add your first user above.
        </div>
      )}
    </div>
  );
};
