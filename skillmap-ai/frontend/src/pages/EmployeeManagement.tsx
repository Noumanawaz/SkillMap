import React, { useEffect, useState, Fragment } from "react";
import { apiGet, apiPost } from "../api/client";

interface Employee {
  employee_id: string;
  email: string;
  name: string;
  description?: string;
  role_id?: string;
  manager_id?: string;
  hire_date?: string;
  location?: string;
}

interface EmployeeSkill {
  skill_id: string;
  name: string;
  category?: string;
  domain?: string;
  proficiency_level: number;
  theta: number;
  alpha: number;
}

interface EmployeeSkillsResponse {
  employee_id: string;
  employee_name: string;
  skills: EmployeeSkill[];
  total_skills: number;
}

export const EmployeeManagement: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [viewingSkillsId, setViewingSkillsId] = useState<string | null>(null);
  const [employeeSkills, setEmployeeSkills] = useState<EmployeeSkillsResponse | null>(null);
  const [loadingSkills, setLoadingSkills] = useState(false);
  const [assessmentHistory, setAssessmentHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [formData, setFormData] = useState<Partial<Employee>>({
    email: "",
    name: "",
    description: "",
    location: "",
    hire_date: "",
  });

  useEffect(() => {
    loadEmployees();
    
    // Check for refresh flag on mount (after assessment completion)
    const refreshEmployeeId = sessionStorage.getItem('refresh_employee_skills');
    if (refreshEmployeeId) {
      // Auto-load skills for this employee after a short delay
      setTimeout(() => {
        loadEmployeeSkills(refreshEmployeeId);
      }, 500);
    }
  }, []);

  async function loadEmployees() {
    try {
      const data = await apiGet<Employee[]>("/v1/profiles");
      setEmployees(data);
    } catch (err: any) {
      setError("Failed to load employees");
      console.error(err);
    }
  }

  async function handleCreate() {
    if (!formData.email || !formData.name) {
      setError("Email and name are required");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await apiPost("/v1/profiles", formData);
      setSuccess("Employee created successfully! Skills extracted from description if provided.");
      setFormData({ email: "", name: "", description: "", location: "", hire_date: "" });
      await loadEmployees();
      // Clear skills view if it was open
      setViewingSkillsId(null);
      setEmployeeSkills(null);
    } catch (err: any) {
      setError(err.message || "Failed to create employee");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdate(id: string) {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await apiPost(`/v1/profiles/${id}`, formData, "PUT");
      setSuccess("Employee updated successfully! Skills re-extracted from description if changed.");
      setEditingId(null);
      setFormData({ email: "", name: "", description: "", location: "", hire_date: "" });
      await loadEmployees();
      // Refresh skills view if it was open
      if (viewingSkillsId === editingId) {
        await loadEmployeeSkills(editingId);
      }
    } catch (err: any) {
      setError(err.message || "Failed to update employee");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Are you sure you want to delete this employee?")) return;
    setLoading(true);
    setError(null);
    try {
      await apiPost(`/v1/profiles/${id}`, {}, "DELETE");
      setSuccess("Employee deleted successfully!");
      await loadEmployees();
    } catch (err: any) {
      setError(err.message || "Failed to delete employee");
    } finally {
      setLoading(false);
    }
  }

  function startEdit(emp: Employee) {
    setEditingId(emp.employee_id);
    setFormData({
      email: emp.email,
      name: emp.name,
      description: emp.description || "",
      location: emp.location || "",
      hire_date: emp.hire_date || "",
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setFormData({ email: "", name: "", description: "", location: "", hire_date: "" });
  }

  async function loadAssessmentHistory(employeeId: string) {
    setLoadingHistory(true);
    try {
      const history = await apiGet<any[]>(`/v1/assessments/history/${employeeId}`);
      setAssessmentHistory(history);
    } catch (err) {
      console.error("Failed to load assessment history", err);
      setAssessmentHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  }

  async function loadEmployeeSkills(employeeId: string) {
    if (viewingSkillsId === employeeId && employeeSkills) {
      setViewingSkillsId(null);
      setEmployeeSkills(null);
      setAssessmentHistory([]);
      return;
    }
    
    setLoadingSkills(true);
    setError(null);
    try {
      const data = await apiGet<EmployeeSkillsResponse>(`/v1/profiles/${employeeId}/skills`);
      setEmployeeSkills(data);
      setViewingSkillsId(employeeId);
      // Also load assessment history
      await loadAssessmentHistory(employeeId);
      
      // Clear refresh flag if this was a refresh after assessment
      if (sessionStorage.getItem('refresh_employee_skills') === employeeId) {
        sessionStorage.removeItem('refresh_employee_skills');
        setSuccess(`✅ Skills updated! Your assessment results have been applied to your profile.`);
        setTimeout(() => setSuccess(null), 5000);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load employee skills");
      setViewingSkillsId(null);
      setEmployeeSkills(null);
    } finally {
      setLoadingSkills(false);
    }
  }

  return (
    <div className="card">
      <h2>Employee Management</h2>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="card" style={{ marginBottom: "2rem" }}>
        <h3>{editingId ? "Edit Employee" : "Add New Employee"}</h3>
        <div className="grid">
          <div className="form-group">
            <label>Email *</label>
            <input
              type="email"
              value={formData.email || ""}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              disabled={!!editingId}
            />
          </div>
          <div className="form-group">
            <label>Name *</label>
            <input
              type="text"
              value={formData.name || ""}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>
          <div className="form-group" style={{ gridColumn: "1 / -1" }}>
            <label>
              <strong>Description / Bio</strong> 
              <span style={{ color: "#666", fontSize: "0.9rem", fontWeight: "normal", marginLeft: "0.5rem" }}>
                (Skills will be extracted automatically using AI)
              </span>
            </label>
            <textarea
              rows={5}
              value={formData.description || ""}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="e.g., Senior DevOps engineer with expertise in CI/CD pipelines, containerization, and infrastructure automation. Proficient in Docker, Kubernetes, and cloud platforms."
              style={{ 
                width: "100%", 
                padding: "0.75rem", 
                fontSize: "0.95rem", 
                fontFamily: "inherit",
                border: "2px solid #e0e0e0",
                borderRadius: "8px",
                resize: "vertical"
              }}
            />
            <small style={{ color: "#666", fontSize: "0.85rem", display: "block", marginTop: "0.5rem" }}>
              💡 Enter employee's skills, experience, or bio. AI will automatically extract and store skills from this description.
            </small>
          </div>
          <div className="form-group">
            <label>Location</label>
            <input
              type="text"
              value={formData.location || ""}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Hire Date</label>
            <input
              type="date"
              value={formData.hire_date || ""}
              onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
            />
          </div>
        </div>
        <div className="flex">
          {editingId ? (
            <>
              <button
                className="btn btn-primary"
                onClick={() => handleUpdate(editingId)}
                disabled={loading}
              >
                {loading ? "⏳ Updating..." : "💾 Update Employee"}
              </button>
              <button className="btn btn-secondary" onClick={cancelEdit}>
                Cancel
              </button>
            </>
          ) : (
            <button
              className="btn btn-primary"
              onClick={() => void handleCreate()}
              disabled={loading || !formData.email || !formData.name}
            >
              {loading ? "⏳ Creating..." : "➕ Add Employee"}
            </button>
          )}
        </div>
      </div>

      <h3>All Employees ({employees.length})</h3>
      {employees.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">👥</div>
          <p>No employees yet. Add one to get started.</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Description</th>
                <th>Location</th>
                <th>Hire Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((emp) => (
                <Fragment key={emp.employee_id}>
                  <tr>
                    <td><strong>{emp.name}</strong></td>
                    <td>{emp.email}</td>
                    <td style={{ maxWidth: "300px", fontSize: "0.9rem", color: "#666" }}>
                      {emp.description ? (
                        <span title={emp.description}>
                          {emp.description.length > 80 
                            ? `${emp.description.substring(0, 80)}...` 
                            : emp.description}
                        </span>
                      ) : (
                        <span style={{ color: "#999", fontStyle: "italic" }}>No description</span>
                      )}
                    </td>
                    <td>{emp.location || "-"}</td>
                    <td>{emp.hire_date || "-"}</td>
                    <td>
                      <div className="flex">
                        <button
                          className="btn btn-secondary"
                          onClick={() => startEdit(emp)}
                          style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
                        >
                          ✏️ Edit
                        </button>
                        <button
                          className="btn btn-info"
                          onClick={() => void loadEmployeeSkills(emp.employee_id)}
                          style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
                          disabled={loadingSkills}
                        >
                          {loadingSkills && viewingSkillsId === emp.employee_id
                            ? "⏳"
                            : viewingSkillsId === emp.employee_id
                            ? "👁️ Hide Skills"
                            : "🔍 View Skills"}
                        </button>
                        <button
                          className="btn btn-danger"
                          onClick={() => void handleDelete(emp.employee_id)}
                          style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
                        >
                          🗑️ Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                  {viewingSkillsId === emp.employee_id && employeeSkills && (
                    <tr>
                      <td colSpan={6} style={{ padding: "1rem", background: "#f9f9f9" }}>
                        <div style={{ marginTop: "1rem" }}>
                          <h4 style={{ marginBottom: "1rem" }}>
                            Skills for {employeeSkills.employee_name} ({employeeSkills.total_skills} skills)
                          </h4>
                          {employeeSkills.skills.length === 0 ? (
                            <div className="empty-state" style={{ padding: "2rem" }}>
                              <div className="empty-state-icon">📋</div>
                              <p>No skills found. Add a description to extract skills automatically.</p>
                            </div>
                          ) : (
                            <div className="table-container">
                              <table>
                                <thead>
                                  <tr>
                                    <th>Skill Name</th>
                                    <th>Category</th>
                                    <th>Domain</th>
                                    <th>Proficiency Level</th>
                                    <th>Theta</th>
                                    <th>Actions</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {employeeSkills.skills.map((skill) => (
                                    <tr key={skill.skill_id}>
                                      <td><strong>{skill.name}</strong></td>
                                      <td>{skill.category || "-"}</td>
                                      <td>{skill.domain || "-"}</td>
                                      <td>
                                        <span className={`badge ${
                                          skill.proficiency_level >= 4
                                            ? "badge-success"
                                            : skill.proficiency_level >= 3
                                            ? "badge-warning"
                                            : "badge-secondary"
                                        }`}>
                                          {skill.proficiency_level.toFixed(1)}/5
                                        </span>
                                      </td>
                                      <td>{skill.theta.toFixed(2)}</td>
                                      <td>
                                        <button
                                          className="btn btn-info"
                                          onClick={() => {
                                            // Store in sessionStorage for the assessment page to pick up
                                            sessionStorage.setItem('assessment_employee_id', viewingSkillsId || '');
                                            sessionStorage.setItem('assessment_skill_id', skill.skill_id);
                                            sessionStorage.setItem('assessment_skill_name', skill.name);
                                            sessionStorage.setItem('auto_start_assessment', 'true');
                                            // Navigate to assessment page
                                            window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'assessment' } }));
                                          }}
                                          style={{ fontSize: "0.875rem", padding: "0.5rem 1rem" }}
                                        >
                                          📝 Take Assessment
                                        </button>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}
                          {assessmentHistory.length > 0 && (
                            <div style={{ marginTop: "2rem" }}>
                              <h4 style={{ marginBottom: "1rem" }}>Assessment History</h4>
                              <div className="table-container">
                                <table>
                                  <thead>
                                    <tr>
                                      <th>Skill</th>
                                      <th>Score</th>
                                      <th>Status</th>
                                      <th>Date</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {assessmentHistory.map((assessment) => (
                                      <tr key={assessment.assessment_id}>
                                        <td><strong>{assessment.skill_name}</strong></td>
                                        <td>
                                          <span className={`badge ${
                                            assessment.score >= 4
                                              ? "badge-success"
                                              : assessment.score >= 3
                                              ? "badge-warning"
                                              : "badge-secondary"
                                          }`}>
                                            {assessment.score?.toFixed(1) || "N/A"}/5.0
                                          </span>
                                        </td>
                                        <td>
                                          <span className={`badge ${
                                            assessment.status === "completed"
                                              ? "badge-success"
                                              : assessment.status === "in_progress"
                                              ? "badge-warning"
                                              : "badge-secondary"
                                          }`}>
                                            {assessment.status}
                                          </span>
                                        </td>
                                        <td>
                                          {assessment.completed_at
                                            ? new Date(assessment.completed_at).toLocaleDateString()
                                            : new Date(assessment.created_at).toLocaleDateString()}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )}
                          {assessmentHistory.length === 0 && !loadingHistory && (
                            <div style={{ marginTop: "1rem", padding: "1rem", background: "#f0f0f0", borderRadius: "4px" }}>
                              <p style={{ margin: 0, color: "#666" }}>
                                No assessment history. Take a test from the Skill Assessment page to measure proficiency.
                              </p>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

