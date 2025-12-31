import React, { useState, useEffect } from "react";
import { apiGet, apiPost } from "../api/client";

interface PathItem {
  skill_id: string;
  module_id: string;
  title: string;
  description?: string;
  order: number;
  expected_gain: number;
  duration_minutes?: number;
  is_generated?: boolean;
}

interface LearningPath {
  employee_id: string;
  goal_id: string;
  items: PathItem[];
  total_hours: number;
  meta: Record<string, any>;
}

interface Employee {
  employee_id: string;
  name: string;
  email: string;
}

interface Goal {
  goal_id: string;
  title: string;
}

export const EmployeeLearningCockpit: React.FC = () => {
  const [employeeId, setEmployeeId] = useState("");
  const [goalId, setGoalId] = useState("");
  const [maxHours, setMaxHours] = useState("40");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [path, setPath] = useState<LearningPath | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [cognitiveSummary, setCognitiveSummary] = useState<any>(null);
  const [showCognitive, setShowCognitive] = useState(false);

  useEffect(() => {
    loadEmployees();
    loadGoals();
  }, []);

  async function loadEmployees() {
    try {
      const data = await apiGet<Employee[]>("/v1/profiles");
      setEmployees(data);
    } catch (err) {
      console.error("Failed to load employees", err);
    }
  }

  async function loadGoals() {
    try {
      const data = await apiGet<Goal[]>("/v1/strategy/goals");
      setGoals(data);
    } catch (err) {
      console.error("Failed to load goals", err);
    }
  }

  async function handleGenerate() {
    if (!employeeId || !goalId) {
      setError("Please select both an Employee and a Goal");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const data = await apiPost<any, LearningPath>("/v1/learning-path", {
        employee_id: employeeId,
        goal_id: goalId,
        max_hours: parseFloat(maxHours) || 40,
      });
      setPath(data);
      // Check if there's an error message in meta
      if (data.items.length === 0 && data.meta?.message) {
        // Only surface an error when the backend explicitly tells us why
        setError(data.meta.message as string);
      }
    } catch (e: any) {
      const errorMsg = e.message || "Failed to generate learning path";
      if (errorMsg.includes("No skills") || errorMsg.includes("skills extracted")) {
        setError(`${errorMsg}. Please extract skills for this goal first.`);
      } else {
        setError(errorMsg);
      }
      setPath(null);
    } finally {
      setLoading(false);
    }
  }

  async function loadCognitiveSummary() {
    if (!employeeId) {
      setError("Please select an Employee");
      return;
    }
    setError(null);
    try {
      const data = await apiGet<any>(`/v1/profiles/${employeeId}/cognitive-summary`);
      setCognitiveSummary(data);
      setShowCognitive(true);
    } catch (e: any) {
      setError(e.message || "Failed to load cognitive summary");
    }
  }

  return (
    <div>
      <div className="card">
        <h2>Employee Learning Cockpit</h2>
        <p style={{ color: "#666", marginBottom: "1.5rem" }}>
          Generate personalized learning paths based on skill gaps and cognitive profile.
        </p>

        <div className="grid">
          <div className="form-group">
            <label>Employee</label>
            <select
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              style={{ width: "100%", padding: "0.75rem", border: "2px solid #e0e0e0", borderRadius: "8px" }}
            >
              <option value="">Select an employee...</option>
              {employees.map((e) => (
                <option key={e.employee_id} value={e.employee_id}>
                  {e.name} ({e.email})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Strategic Goal</label>
            <select
              value={goalId}
              onChange={(e) => setGoalId(e.target.value)}
              style={{ width: "100%", padding: "0.75rem", border: "2px solid #e0e0e0", borderRadius: "8px" }}
            >
              <option value="">Select a goal...</option>
              {goals.map((g) => (
                <option key={g.goal_id} value={g.goal_id}>
                  {g.title}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Max Hours</label>
            <input
              type="number"
              placeholder="40"
              value={maxHours}
              onChange={(e) => setMaxHours(e.target.value)}
              min="1"
              max="200"
            />
          </div>
        </div>

        <div className="flex" style={{ marginTop: "1rem" }}>
          <button
            className="btn btn-primary"
            onClick={() => void handleGenerate()}
            disabled={loading || !employeeId || !goalId}
          >
            {loading ? "⏳ Generating Path..." : "🎓 Generate Learning Path"}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => void loadCognitiveSummary()}
            disabled={!employeeId}
          >
            🧠 View Cognitive Profile
          </button>
        </div>

        {error && <div className="alert alert-error mt-2">{error}</div>}
      </div>

      {path && (
        <div className="card">
          <div className="flex-between mb-2">
            <h3>Personalized Learning Path</h3>
            <div>
              <span className="badge badge-primary" style={{ fontSize: "1.1rem", padding: "0.5rem 1rem" }}>
                {path.total_hours.toFixed(1)} hours total
              </span>
            </div>
          </div>

          <div className="grid mb-3">
            <div>
              <strong>Years to Goal:</strong>{" "}
              <span className="badge badge-info">
                {path.meta.years_left?.toFixed(1) || "N/A"}
              </span>
            </div>
          </div>

          {path.items.length === 0 ? (
            <div className="empty-state">
              {path.meta?.message ? (
                <>
                  <div className="empty-state-icon">
                    {path.meta.gap_index && path.meta.gap_index >= 1 ? "⚠️" : "✅"}
                  </div>
                  <p>{path.meta.message}</p>
                  {typeof path.meta.message === "string" &&
                    (path.meta.message as string).toLowerCase().includes("extract skills") && (
                  <p style={{ marginTop: "1rem", fontSize: "0.9rem", color: "#666" }}>
                    Please extract skills for this goal first.
                  </p>
                    )}
                </>
              ) : (
                <>
                  <div className="empty-state-icon">✅</div>
                  <p>No learning items needed. Employee is ready for this goal!</p>
                </>
              )}
            </div>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Module Title</th>
                    <th>Description</th>
                    <th>Duration</th>
                    <th>Expected Gain</th>
                    <th>Type</th>
                  </tr>
                </thead>
                <tbody>
                  {path.items.map((item) => (
                    <tr key={`${item.module_id}-${item.order}`}>
                      <td><strong>{item.order}</strong></td>
                      <td>{item.title}</td>
                      <td style={{ maxWidth: "300px", fontSize: "0.9rem", color: "#666" }}>
                        {item.description || "-"}
                      </td>
                      <td>
                        {item.duration_minutes ? (
                          <span className="badge badge-primary">
                            {Math.round(item.duration_minutes / 60 * 10) / 10}h
                          </span>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td>
                        <span className="badge badge-success">
                          +{item.expected_gain.toFixed(1)}
                        </span>
                      </td>
                      <td>
                        {item.is_generated ? (
                          <span className="badge badge-primary" title="Generated">
                            📚 Generated
                          </span>
                        ) : (
                          <span className="badge badge-primary">📚 Curated</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {showCognitive && cognitiveSummary && (
        <div className="card">
          <div className="flex-between mb-2">
            <h3>Cognitive Profile</h3>
            <button
              className="btn btn-secondary"
              onClick={() => setShowCognitive(false)}
              style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
            >
              Close
            </button>
          </div>
          <pre style={{
            background: "#f5f5f5",
            padding: "1rem",
            borderRadius: "8px",
            overflow: "auto",
            maxHeight: "400px",
            fontSize: "0.9rem"
          }}>
            {JSON.stringify(cognitiveSummary, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
