import React, { useState, useEffect } from "react";
import { apiGet } from "../api/client";
import { SkillGap3D } from "../components/SkillGap3D";

interface EmployeeGapResponse {
  employee_id: string;
  goal_id: string;
  scalar_gaps: Record<string, number>;
  skill_names?: Record<string, string>;
  similarity: number;
  gap_index: number;
  message?: string;
  ai_insights?: {
    readiness_score?: number;
    summary?: string;
    detailed_report?: string;
    key_gaps?: string[];
    matches_found?: number;
    missing_skills_count?: number;
    gap_breakdown?: Array<{
      skill_name: string;
      current_level: number;
      required_level: number;
      gap_value: number;
      severity: string;
      explanation: string;
    }>;
  };
  processing_info?: {
    skills_analyzed?: number;
    skills_extracted?: boolean;
    employee_skills_found?: number;
    total_gaps?: number;
    critical_gaps?: number;
    ai_analysis_used?: boolean;
  };
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

export const SkillGapExplorer: React.FC = () => {
  const [goalId, setGoalId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [result, setResult] = useState<EmployeeGapResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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

  async function handleFetch() {
    if (!goalId || !employeeId) {
      setError("Please select both a Goal and an Employee");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const data = await apiGet<EmployeeGapResponse>(
        `/v1/gaps/by-goal/${goalId}/employee/${employeeId}`
      );
      setResult(data);
      if (data.message) {
        setError(data.message);
      }
    } catch (e: any) {
      setError(e.message || "Failed to fetch gap analysis. Make sure skills are extracted for this goal.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const getGapSeverity = (gap: number) => {
    if (gap >= 3) return { label: "Critical", class: "badge-danger" };
    if (gap >= 2) return { label: "High", class: "badge-warning" };
    if (gap >= 1) return { label: "Moderate", class: "badge-primary" };
    return { label: "Low", class: "badge-success" };
  };

  return (
    <div className="card">
      <h2>Skill Gap Explorer</h2>
      <p style={{ color: "#666", marginBottom: "1.5rem" }}>
        Analyze skill gaps between an employee's current capabilities and strategic goal requirements.
      </p>

      <div className="grid">
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
      </div>

      <button
        className="btn btn-primary"
        onClick={() => void handleFetch()}
        disabled={loading || !goalId || !employeeId}
      >
        {loading ? "⏳ Analyzing..." : "🔍 Analyze Gaps"}
      </button>

      {error && <div className="alert alert-error mt-2">{error}</div>}

      {result && (
        <div className="mt-3">
          {result.processing_info && (
            <div className="alert alert-info" style={{ marginBottom: "1rem", fontSize: "0.9rem" }}>
              <strong>Analysis Complete:</strong> Analyzed {result.processing_info.skills_analyzed || 0} skills,
              found {result.processing_info.employee_skills_found || 0} existing skills,
              identified {result.processing_info.total_gaps || 0} gaps
              ({result.processing_info.critical_gaps || 0} critical).
              {result.processing_info.skills_extracted && " Skills were automatically extracted from the goal."}
              {result.processing_info.ai_analysis_used && " 🤖 AI-powered semantic analysis was used to identify skill relationships."}
            </div>
          )}

          {result.scalar_gaps && Object.keys(result.scalar_gaps).length > 0 && (
            <div className="card" style={{ marginBottom: "1.5rem", padding: "1.5rem" }}>
              <h3 style={{ marginBottom: "1.5rem", color: "#333" }}>📋 Skills Overview</h3>

              {(() => {
                const allSkills = Object.entries(result.scalar_gaps).map(([skillId, gap]) => {
                  const skillName = result.skill_names?.[skillId] || skillId.substring(0, 8) + "...";
                  const gapBreakdown = result.ai_insights?.gap_breakdown?.find(
                    (g) => g.skill_name === skillName
                  );
                  const hasGap = gap > 0.1;

                  return {
                    skillId,
                    skillName,
                    gap,
                    hasGap,
                    severity: gapBreakdown?.severity || (gap >= 3 ? "critical" : gap >= 2 ? "high" : gap >= 1 ? "moderate" : "low"),
                  };
                });

                const presentSkills = allSkills.filter(s => !s.hasGap || s.gap < 0.1);
                const missingSkills = allSkills.filter(s => s.hasGap && s.gap >= 0.1).sort((a, b) => b.gap - a.gap);

                return (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.5rem" }}>
                    <div style={{ padding: "1.5rem", background: "linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)", borderRadius: "12px", border: "2px solid #4caf50" }}>
                      <div style={{ display: "flex", alignItems: "center", marginBottom: "1rem" }}>
                        <span style={{ fontSize: "2rem", marginRight: "0.5rem" }}>✅</span>
                        <h4 style={{ margin: 0, color: "#2e7d32", fontSize: "1.2rem", fontWeight: "700" }}>Skills Present ({presentSkills.length})</h4>
                      </div>
                      {presentSkills.length === 0 ? <p style={{ color: "#666", fontStyle: "italic" }}>No skills currently meet the requirements.</p> : (
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                          {presentSkills.map((skill) => (
                            <div key={skill.skillId} style={{ padding: "0.75rem", background: "white", borderRadius: "8px", border: "1px solid #4caf50" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <strong style={{ color: "#2e7d32" }}>{skill.skillName}</strong>
                                <span className="badge badge-success">Met</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div style={{ padding: "1.5rem", background: "linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%)", borderRadius: "12px", border: "2px solid #f44336" }}>
                      <div style={{ display: "flex", alignItems: "center", marginBottom: "1rem" }}>
                        <span style={{ fontSize: "2rem", marginRight: "0.5rem" }}>⚠️</span>
                        <h4 style={{ margin: 0, color: "#c62828", fontSize: "1.2rem", fontWeight: "700" }}>Skills Missing ({missingSkills.length})</h4>
                      </div>
                      {missingSkills.length === 0 ? <p style={{ color: "#666", fontStyle: "italic" }}>All required skills are present!</p> : (
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                          {missingSkills.map((skill) => {
                            const severityColors: Record<string, string> = { critical: "#c62828", high: "#f57c00", moderate: "#fbc02d", low: "#388e3c" };
                            const severityLabels: Record<string, string> = { critical: "Critical", high: "High", moderate: "Moderate", low: "Low" };
                            return (
                              <div key={skill.skillId} style={{ padding: "0.75rem", background: "white", borderRadius: "8px", border: `2px solid ${severityColors[skill.severity] || "#ccc"}` }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                                  <strong style={{ color: "#333" }}>{skill.skillName}</strong>
                                  <span className="badge" style={{ backgroundColor: severityColors[skill.severity] || "#ccc", color: "white", padding: "0.25rem 0.5rem", borderRadius: "4px", fontSize: "0.75rem", textTransform: "uppercase", fontWeight: "600" }}>
                                    {severityLabels[skill.severity] || skill.severity}
                                  </span>
                                </div>
                                <div style={{ padding: "0.5rem", background: "#f5f5f5", borderRadius: "4px", fontSize: "0.85rem" }}>
                                  <strong style={{ color: severityColors[skill.severity] || "#000" }}>Gap: {skill.gap.toFixed(1)}</strong>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {result.ai_insights && (
            <>
              <div className="card" style={{ marginBottom: "1rem", padding: "1.5rem", background: "#f0f7ff", border: "2px solid #4a90e2" }}>
                <h4 style={{ marginBottom: "1rem", color: "#2c5aa0" }}>🤖 AI-Powered Gap Analysis</h4>
                <div style={{ marginBottom: "1rem" }}>
                  <p style={{ marginBottom: "0.5rem", fontSize: "0.95rem" }}>
                    <strong>Readiness Score:</strong> <span style={{ fontSize: "1.2rem", fontWeight: "bold", color: (result.ai_insights.readiness_score ?? 0) >= 0.7 ? "#28a745" : (result.ai_insights.readiness_score ?? 0) >= 0.5 ? "#ffc107" : "#dc3545" }}>
                      {((result.ai_insights.readiness_score ?? 0) * 100).toFixed(1)}%
                    </span>
                  </p>
                  {result.ai_insights.summary && <p style={{ marginBottom: "0.5rem", fontSize: "0.95rem" }}><strong>Quick Assessment:</strong> {result.ai_insights.summary}</p>}
                </div>
                {result.ai_insights.detailed_report && (
                  <div style={{ marginTop: "1rem", padding: "1rem", background: "white", borderRadius: "8px", border: "1px solid #d0e5ff" }}>
                    <h5 style={{ marginBottom: "0.75rem", color: "#2c5aa0", fontSize: "1rem" }}>📋 Detailed Gap Analysis Report</h5>
                    <div style={{ fontSize: "0.95rem", lineHeight: "1.6", whiteSpace: "pre-wrap" }}>{result.ai_insights.detailed_report}</div>
                  </div>
                )}
                {result.ai_insights.key_gaps && result.ai_insights.key_gaps.length > 0 && (
                  <div style={{ marginTop: "1rem" }}>
                    <strong>Key Critical Gaps:</strong>
                    <ul style={{ marginTop: "0.5rem", marginLeft: "1.5rem" }}>
                      {result.ai_insights.key_gaps.map((gap, idx) => <li key={idx} style={{ fontSize: "0.9rem", marginBottom: "0.25rem" }}>{gap}</li>)}
                    </ul>
                  </div>
                )}
              </div>

              {result.ai_insights.gap_breakdown && result.ai_insights.gap_breakdown.length > 0 && (
                <div className="card" style={{ marginBottom: "1rem", padding: "1.5rem" }}>
                  <h4 style={{ marginBottom: "1rem" }}>📊 Detailed Gap Breakdown</h4>
                  <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                    {result.ai_insights.gap_breakdown.map((gap, idx) => {
                      const severityColors: Record<string, string> = { critical: "#dc3545", high: "#fd7e14", moderate: "#ffc107", low: "#28a745" };
                      const severityBg: Record<string, string> = { critical: "#fee", high: "#fff4e6", moderate: "#fffbf0", low: "#f0fdf4" };
                      return (
                        <div key={idx} style={{ padding: "1rem", borderRadius: "8px", border: `2px solid ${severityColors[gap.severity] || "#ccc"}`, background: severityBg[gap.severity] || "#fff" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                            <h5 style={{ margin: 0, fontSize: "1rem", fontWeight: "bold" }}>{gap.skill_name}</h5>
                            <span className="badge" style={{ backgroundColor: severityColors[gap.severity] || "#ccc", color: "white", padding: "0.25rem 0.75rem", borderRadius: "4px", fontSize: "0.85rem", textTransform: "uppercase" }}>
                              {gap.severity}
                            </span>
                          </div>
                          <div style={{ padding: "0.75rem", background: "white", borderRadius: "4px", fontSize: "0.9rem", lineHeight: "1.5", marginBottom: "0.5rem" }}>
                            <strong>Gap:</strong> <span style={{ color: severityColors[gap.severity] || "#000", fontWeight: "bold" }}>{gap.gap_value.toFixed(1)}</span>
                          </div>
                          <div style={{ padding: "0.75rem", background: "white", borderRadius: "4px", fontSize: "0.9rem", lineHeight: "1.5" }}>
                            <strong>Explanation:</strong> {gap.explanation}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}

          <h3 className="mt-3">3D Skill Gap Visualization</h3>
          {Object.keys(result.scalar_gaps).length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">✅</div><p>No skill gaps detected! Employee is ready for this goal.</p></div>
          ) : (
            <div style={{ marginTop: "1rem" }}>
              <SkillGap3D
                gaps={Object.entries(result.scalar_gaps).map(([sid, gap]) => {
                  const severity = getGapSeverity(gap);
                  const skillName = result.skill_names?.[sid] || sid.substring(0, 8) + "...";
                  const gapBreakdown = result.ai_insights?.gap_breakdown?.find(g => g.skill_name === skillName);
                  return {
                    skill_id: sid,
                    skill_name: skillName,
                    gap_value: gap,
                    severity: severity.label.toLowerCase() as "critical" | "high" | "moderate" | "low",
                    current_level: gapBreakdown?.current_level ?? 0,
                    required_level: gapBreakdown?.required_level ?? 0,
                  };
                }).sort((a, b) => b.gap_value - a.gap_value)}
                similarity={result.similarity}
                gap_index={result.gap_index}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
