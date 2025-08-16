import React, { useEffect, useState } from "react";
import { fetchUserProfile, deleteUser } from "../api";
import { useNavigate } from "react-router-dom";

function Profile() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    // Extract userId from JWT token
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/", { replace: true });
      return;
    }
    let userId = "";
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = payload.user_id;
    } catch {}
    if (!userId) {
      navigate("/", { replace: true });
      return;
    }
    fetchUserProfile(userId)
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
  localStorage.removeItem("token");
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

  // Use email prefix as display name
  const displayName = user && user.email ? user.email.split("@")[0] : "User";
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-base-200 px-4 py-10">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-10 max-w-lg w-full flex flex-col items-center">
        <div className="w-32 h-32 rounded-full bg-blue-600 dark:bg-blue-400 flex items-center justify-center text-5xl font-bold text-white mb-6">
          {displayName[0]}
        </div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          {displayName}
        </h2>
        <div className="text-gray-500 dark:text-gray-400 mb-1">
          Email: <span className="font-mono">{user.email}</span>
        </div>
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
