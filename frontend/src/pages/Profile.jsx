import React, { useEffect, useState } from "react";
import { fetchUserProfile, deleteUser } from "../api";
import { useNavigate } from "react-router-dom";

function Profile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (!stored) {
      navigate("/", { replace: true });
      return;
    }
    const u = JSON.parse(stored);
    fetchUserProfile(u.id)
      .then((res) => {
        setUser(res.user);
        setLoading(false);
      })
      .catch((err) => {
        setError("Failed to load profile");
        setLoading(false);
      });
  }, [navigate]);

  const handleDelete = async () => {
    if (
      !window.confirm(
        "Are you sure you want to delete your account? This cannot be undone."
      )
    )
      return;
    try {
      await deleteUser(user.id);
      localStorage.removeItem("user");
      navigate("/", { replace: true });
    } catch (err) {
      setError("Failed to delete account");
    }
  };

  if (loading)
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );
  if (error)
    return (
      <div className="min-h-screen flex items-center justify-center text-red-500">
        {error}
      </div>
    );
  if (!user) return null;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-base-200 px-4 py-10">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-10 max-w-lg w-full flex flex-col items-center">
        <div className="w-32 h-32 rounded-full bg-blue-600 dark:bg-blue-400 flex items-center justify-center text-5xl font-bold text-white mb-6">
          {user.name ? user.name[0] : "?"}
        </div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          {user.name}
        </h2>
        <div className="text-gray-500 dark:text-gray-400 mb-1">
          Email: <span className="font-mono">{user.email}</span>
        </div>
        {user.age && (
          <div className="text-gray-500 dark:text-gray-400 mb-1">
            Age: {user.age}
          </div>
        )}
        {user.phone && (
          <div className="text-gray-500 dark:text-gray-400 mb-4">
            Phone: {user.phone}
          </div>
        )}
        <div className="w-full mt-4 flex flex-col items-center">
          <button className="btn btn-error" onClick={handleDelete}>
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
}

export default Profile;
