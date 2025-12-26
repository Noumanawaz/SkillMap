import React, { useEffect, useState } from "react";
import { apiGet, apiPost } from "../api/client";

interface StrategicGoal {
  goal_id: string;
  title: string;
  description?: string;
  time_horizon_year?: number;
  business_unit?: string;
  priority?: number;
  created_at?: string;
  skills_count?: number;
}

export const StrategyDashboard: React.FC = () => {
  const [goals, setGoals] = useState<StrategicGoal[]>([]);
  const [rawText, setRawText] = useState("");
  const [businessUnit, setBusinessUnit] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [extractingSkills, setExtractingSkills] = useState<string | null>(null);

  async function loadGoals() {
    try {
      const data = await apiGet<StrategicGoal[]>("/v1/strategy/goals");
      // Fetch skill counts for each goal
      const goalsWithCounts = await Promise.all(
        data.map(async (goal) => {
          try {
            const countData = await apiGet<{ skills_count: number }>(
              `/v1/strategy/goals/${goal.goal_id}/skills-count`
            );
            return { ...goal, skills_count: countData.skills_count };
          } catch {
            return { ...goal, skills_count: 0 };
          }
        })
      );
      setGoals(goalsWithCounts);
    } catch (err) {
      setError("Failed to load goals");
      console.error(err);
    }
  }

  useEffect(() => {
    void loadGoals();
  }, []);

  async function handleIngest() {
    if (!rawText.trim()) {
      setError("Please enter strategy text");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const goals = await apiPost("/v1/strategy/ingest", {
        raw_text: rawText,
        source_name: "Manual Input",
        business_unit: businessUnit || undefined,
      });
      setRawText("");
      setBusinessUnit("");
      setSuccess(`Strategy ingested successfully! ${goals.length} goal(s) extracted using AI. Click "Extract Skills" on each goal to identify required skills.`);
      await loadGoals();
    } catch (err: any) {
      setError(err.message || "Failed to ingest strategy");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleExtractSkills(goalId: string) {
    setExtractingSkills(goalId);
    setError(null);
    setSuccess(null);
    try {
      const result = await apiPost(`/v1/strategy/goals/${goalId}/extract-skills`, {});
      setSuccess(result.message || `Extracted ${result.skills_extracted} skills for this goal using AI!`);
      await loadGoals();
    } catch (err: any) {
      setError(err.message || "Failed to extract skills. Make sure OpenAI API key is configured.");
      console.error(err);
    } finally {
      setExtractingSkills(null);
    }
  }

  return (
    <div className="card">
      <h2>Strategy Dashboard</h2>
      
      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="form-group">
        <label>Business Unit (Optional)</label>
        <input
          type="text"
          placeholder="e.g., Technology, Sales, Operations"
          value={businessUnit}
          onChange={(e) => setBusinessUnit(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Strategy Document Text</label>
        <textarea
          placeholder="Paste your strategy document here. The AI will extract strategic goals, time horizons, and priorities automatically.

Example:
1. Expand into quantum computing services by 2028
2. Build AI-powered customer support platform by 2026
3. Achieve carbon neutrality by 2030"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
      </div>

      <button
        className="btn btn-primary"
        onClick={() => void handleIngest()}
        disabled={loading || !rawText.trim()}
      >
        {loading ? "⏳ Processing with AI..." : "🚀 Ingest Strategy"}
      </button>

      <h3 className="mt-3">Strategic Goals ({goals.length})</h3>
      {goals.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <p>No strategic goals yet. Ingest a strategy document to get started.</p>
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
              {goals.map((g) => (
                <tr key={g.goal_id}>
                  <td><strong>{g.title}</strong></td>
                  <td>{g.description || "-"}</td>
                  <td>{g.business_unit || "-"}</td>
                  <td>
                    {g.time_horizon_year ? (
                      <span className="badge badge-primary">{g.time_horizon_year}</span>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td>
                    {g.priority ? (
                      <span className={`badge ${
                        g.priority <= 2 ? "badge-danger" :
                        g.priority === 3 ? "badge-warning" : "badge-success"
                      }`}>
                        {g.priority}
                      </span>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td>
                    {g.skills_count && g.skills_count > 0 ? (
                      <span className="badge badge-success" style={{ marginRight: "8px" }}>
                        {g.skills_count} skill{g.skills_count !== 1 ? "s" : ""}
                      </span>
                    ) : (
                      <span className="badge badge-warning" style={{ marginRight: "8px" }}>
                        No skills
                      </span>
                    )}
                    <button
                      className="btn btn-secondary"
                      onClick={() => void handleExtractSkills(g.goal_id)}
                      disabled={extractingSkills === g.goal_id}
                      style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
                    >
                      {extractingSkills === g.goal_id ? "⏳" : "🔍"} Extract Skills
                    </button>
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
