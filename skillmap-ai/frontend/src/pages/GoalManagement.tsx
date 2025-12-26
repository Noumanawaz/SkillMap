import React, { useEffect, useState } from "react";
import { apiGet, apiPost } from "../api/client";

interface Goal {
  goal_id: string;
  title: string;
  description?: string;
  time_horizon_year?: number;
  business_unit?: string;
  priority?: number;
  created_at: string;
}

export const GoalManagement: React.FC = () => {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<Goal>>({
    title: "",
    description: "",
    time_horizon_year: new Date().getFullYear() + 3,
    business_unit: "",
    priority: 3,
  });

  useEffect(() => {
    loadGoals();
  }, []);

  async function loadGoals() {
    try {
      const data = await apiGet<Goal[]>("/v1/strategy/goals");
      setGoals(data);
    } catch (err: any) {
      setError("Failed to load goals");
      console.error(err);
    }
  }

  async function handleCreate() {
    if (!formData.title) {
      setError("Title is required");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await apiPost("/v1/strategy/goals", formData);
      setSuccess("Goal created successfully!");
      setFormData({
        title: "",
        description: "",
        time_horizon_year: new Date().getFullYear() + 3,
        business_unit: "",
        priority: 3,
      });
      await loadGoals();
    } catch (err: any) {
      setError(err.message || "Failed to create goal");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdate(id: string) {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await apiPost(`/v1/strategy/goals/${id}`, formData, "PUT");
      setSuccess("Goal updated successfully!");
      setEditingId(null);
      setFormData({
        title: "",
        description: "",
        time_horizon_year: new Date().getFullYear() + 3,
        business_unit: "",
        priority: 3,
      });
      await loadGoals();
    } catch (err: any) {
      setError(err.message || "Failed to update goal");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Are you sure you want to delete this goal?")) return;
    setLoading(true);
    setError(null);
    try {
      await apiPost(`/v1/strategy/goals/${id}`, {}, "DELETE");
      setSuccess("Goal deleted successfully!");
      await loadGoals();
    } catch (err: any) {
      setError(err.message || "Failed to delete goal");
    } finally {
      setLoading(false);
    }
  }

  function startEdit(goal: Goal) {
    setEditingId(goal.goal_id);
    setFormData({
      title: goal.title,
      description: goal.description || "",
      time_horizon_year: goal.time_horizon_year,
      business_unit: goal.business_unit || "",
      priority: goal.priority,
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setFormData({
      title: "",
      description: "",
      time_horizon_year: new Date().getFullYear() + 3,
      business_unit: "",
      priority: 3,
    });
  }

  return (
    <div className="card">
      <h2>Goal Management</h2>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="card" style={{ marginBottom: "2rem" }}>
        <h3>{editingId ? "Edit Goal" : "Add New Goal"}</h3>
        <div className="grid">
          <div className="form-group">
            <label>Title *</label>
            <input
              type="text"
              value={formData.title || ""}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Business Unit</label>
            <input
              type="text"
              value={formData.business_unit || ""}
              onChange={(e) => setFormData({ ...formData, business_unit: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Time Horizon Year</label>
            <input
              type="number"
              value={formData.time_horizon_year || ""}
              onChange={(e) =>
                setFormData({ ...formData, time_horizon_year: parseInt(e.target.value) || undefined })
              }
            />
          </div>
          <div className="form-group">
            <label>Priority (1-5)</label>
            <input
              type="number"
              min="1"
              max="5"
              value={formData.priority || 3}
              onChange={(e) =>
                setFormData({ ...formData, priority: parseInt(e.target.value) || 3 })
              }
            />
          </div>
        </div>
        <div className="form-group">
          <label>Description</label>
          <textarea
            value={formData.description || ""}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={3}
          />
        </div>
        <div className="flex">
          {editingId ? (
            <>
              <button
                className="btn btn-primary"
                onClick={() => handleUpdate(editingId)}
                disabled={loading}
              >
                {loading ? "⏳ Updating..." : "💾 Update Goal"}
              </button>
              <button className="btn btn-secondary" onClick={cancelEdit}>
                Cancel
              </button>
            </>
          ) : (
            <button
              className="btn btn-primary"
              onClick={() => void handleCreate()}
              disabled={loading || !formData.title}
            >
              {loading ? "⏳ Creating..." : "➕ Add Goal"}
            </button>
          )}
        </div>
      </div>

      <h3>All Goals ({goals.length})</h3>
      {goals.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🎯</div>
          <p>No goals yet. Add one to get started.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Description</th>
                <th>Business Unit</th>
                <th>Horizon</th>
                <th>Priority</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {goals.map((goal) => (
                <tr key={goal.goal_id}>
                  <td><strong>{goal.title}</strong></td>
                  <td style={{ maxWidth: "300px", fontSize: "0.9rem" }}>
                    {goal.description || "-"}
                  </td>
                  <td>{goal.business_unit || "-"}</td>
                  <td>
                    {goal.time_horizon_year ? (
                      <span className="badge badge-primary">{goal.time_horizon_year}</span>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td>
                    {goal.priority ? (
                      <span
                        className={`badge ${
                          goal.priority <= 2
                            ? "badge-danger"
                            : goal.priority === 3
                            ? "badge-warning"
                            : "badge-success"
                        }`}
                      >
                        {goal.priority}
                      </span>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td>
                    <div className="flex">
                      <button
                        className="btn btn-secondary"
                        onClick={() => startEdit(goal)}
                        style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
                      >
                        ✏️ Edit
                      </button>
                      <button
                        className="btn btn-danger"
                        onClick={() => void handleDelete(goal.goal_id)}
                        style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

