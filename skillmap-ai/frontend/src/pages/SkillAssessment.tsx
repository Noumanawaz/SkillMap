import React, { useState, useEffect, useCallback } from "react";
import { apiGet, apiPost } from "../api/client";

interface MCQOption {
  option_id: string;
  text: string;
}

interface MCQQuestion {
  question_id: string;
  question: string;
  options: MCQOption[];
  correct_answer_id?: string;
  difficulty?: number;
  explanation?: string;
  user_answer?: string;
  is_correct?: boolean;
}

interface Assessment {
  assessment_id: string;
  skill_id: string;
  skill_name: string;
  questions: MCQQuestion[];
  difficulty_level: number;
  estimated_duration_minutes: number;
  status: string;
  created_at?: string;
  completed_at?: string;
}

interface AssessmentResult {
  assessment_id: string;
  skill_id: string;
  skill_name: string;
  score: number;
  percentage_correct: number;
  total_questions: number;
  correct_answers: number;
  questions_with_feedback: MCQQuestion[];
  updated_proficiency?: number;
}

interface Employee {
  employee_id: string;
  name: string;
  email: string;
}

interface Skill {
  skill_id: string;
  name: string;
  description?: string;
}

export const SkillAssessment: React.FC = () => {
  const [employeeId, setEmployeeId] = useState("");
  const [skillId, setSkillId] = useState("");
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [readinessScore, setReadinessScore] = useState<number | null>(null);

  async function loadEmployees() {
    try {
      const data = await apiGet<Employee[]>("/v1/profiles");
      setEmployees(data);
    } catch (err) {
      console.error("Failed to load employees", err);
    }
  }

  async function loadSkills() {
    try {
      const data = await apiGet<Skill[]>("/v1/skills");
      setSkills(data);
    } catch (err) {
      console.error("Failed to load skills", err);
    }
  }

  const generateTest = useCallback(async () => {
    if (!employeeId || !skillId) {
      setError("Please select an employee and skill");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setAnswers({});

    try {
      // Find skill details - check both skills list and sessionStorage for skill name
      const skillFromList = skills.find((s) => s.skill_id === skillId);
      const skillName = skillFromList?.name || sessionStorage.getItem('assessment_skill_name') || '';
      const skillDescription = skillFromList?.description;
      
      const response = await apiPost<
        {
          skill_id: string;
          skill_name?: string;
          skill_description?: string;
          readiness_score?: number | null;
          num_questions: number;
        },
        Assessment
      >(
        `/v1/assessments/generate?employee_id=${employeeId}`,
        {
          skill_id: skillId,
          skill_name: skillName,
          skill_description: skillDescription,
          readiness_score: readinessScore,
          num_questions: 10,
        }
      );
      setAssessment(response);
    } catch (err: any) {
      setError(err.message || "Failed to generate assessment");
    } finally {
      setLoading(false);
    }
  }, [employeeId, skillId, skills, readinessScore]);

  useEffect(() => {
    loadEmployees();
    loadSkills();
  }, []);

  // Separate effect to handle auto-start after navigation
  useEffect(() => {
    const preSelectedEmployeeId = sessionStorage.getItem('assessment_employee_id');
    const preSelectedSkillId = sessionStorage.getItem('assessment_skill_id');
    const autoStart = sessionStorage.getItem('auto_start_assessment') === 'true';
    
    if (preSelectedEmployeeId && preSelectedSkillId && !employeeId && !skillId) {
      setEmployeeId(preSelectedEmployeeId);
      setSkillId(preSelectedSkillId);
      
      // Clear session storage immediately
      sessionStorage.removeItem('assessment_employee_id');
      sessionStorage.removeItem('assessment_skill_id');
      sessionStorage.removeItem('assessment_skill_name');
      sessionStorage.removeItem('auto_start_assessment');
    }
  }, [employeeId, skillId]);

  // Auto-start test after employee and skill are set
  useEffect(() => {
    const autoStart = sessionStorage.getItem('auto_start_assessment') === 'true';
    
    if (autoStart && employeeId && skillId && skills.length > 0 && !loading && !assessment) {
      // Clear the flag
      sessionStorage.removeItem('auto_start_assessment');
      
      // Wait a bit for everything to be ready, then generate
      const timer = setTimeout(() => {
        if (employeeId && skillId && generateTest) {
          generateTest();
        }
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [employeeId, skillId, skills.length, loading, assessment, generateTest]);

  async function submitTest() {
    if (!assessment) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiPost<
        { assessment_id: string; answers: Record<string, string> },
        AssessmentResult
      >(
        `/v1/assessments/submit?employee_id=${employeeId}`,
        {
          assessment_id: assessment.assessment_id,
          answers,
        }
      );
      setResult(response);
      setAssessment(null);
    } catch (err: any) {
      setError(err.message || "Failed to submit assessment");
    } finally {
      setLoading(false);
    }
  }

  function handleAnswerChange(questionId: string, optionId: string) {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
  }

  const selectedSkill = skills.find((s) => s.skill_id === skillId);
  const allQuestionsAnswered =
    assessment &&
    assessment.questions.every((q) => answers[q.question_id] !== undefined);

  // Safety check - ensure component always renders
  if (typeof window === 'undefined') {
    return null;
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <h1>Skill Assessment Test</h1>
      <p style={{ color: "#666", marginBottom: "2rem" }}>
        Take a dynamic AI-generated test to measure your proficiency in a skill. Each test is unique and tailored to your readiness level.
      </p>

      {!assessment && !result && (
        <div style={{ background: "#f5f5f5", padding: "2rem", borderRadius: "8px" }}>
          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "bold" }}>
              Select Employee
            </label>
            <select
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value)}
              style={{
                width: "100%",
                padding: "0.75rem",
                fontSize: "1rem",
                borderRadius: "4px",
                border: "1px solid #ddd",
              }}
            >
              <option value="">-- Select Employee --</option>
              {employees.map((emp) => (
                <option key={emp.employee_id} value={emp.employee_id}>
                  {emp.name} ({emp.email})
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "bold" }}>
              Select Skill to Test
            </label>
            <select
              value={skillId}
              onChange={(e) => setSkillId(e.target.value)}
              style={{
                width: "100%",
                padding: "0.75rem",
                fontSize: "1rem",
                borderRadius: "4px",
                border: "1px solid #ddd",
              }}
            >
              <option value="">-- Select Skill --</option>
              {skills.map((skill) => (
                <option key={skill.skill_id} value={skill.skill_id}>
                  {skill.name}
                </option>
              ))}
            </select>
            {selectedSkill?.description && (
              <p style={{ marginTop: "0.5rem", color: "#666", fontSize: "0.9rem" }}>
                {selectedSkill.description}
              </p>
            )}
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: "bold" }}>
              Readiness Score (Optional)
            </label>
            <input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={readinessScore || ""}
              onChange={(e) =>
                setReadinessScore(e.target.value ? parseFloat(e.target.value) : null)
              }
              placeholder="0.0 - 1.0 (determines test difficulty)"
              style={{
                width: "100%",
                padding: "0.75rem",
                fontSize: "1rem",
                borderRadius: "4px",
                border: "1px solid #ddd",
              }}
            />
            <p style={{ marginTop: "0.5rem", color: "#666", fontSize: "0.85rem" }}>
              Leave empty to auto-detect based on current proficiency. Lower scores = easier questions.
            </p>
          </div>

          <button
            onClick={generateTest}
            disabled={loading || !employeeId || !skillId}
            style={{
              padding: "0.75rem 2rem",
              fontSize: "1rem",
              background: loading ? "#ccc" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Generating Test..." : "Generate Dynamic Test"}
          </button>
        </div>
      )}

      {error && (
        <div
          style={{
            background: "#fee",
            color: "#c33",
            padding: "1rem",
            borderRadius: "4px",
            marginTop: "1rem",
          }}
        >
          {error}
        </div>
      )}

      {assessment && !result && (
        <div style={{ marginTop: "2rem" }}>
          <div
            style={{
              background: "#e3f2fd",
              padding: "1rem",
              borderRadius: "4px",
              marginBottom: "2rem",
            }}
          >
            <h2 style={{ margin: "0 0 0.5rem 0" }}>Test: {assessment.skill_name}</h2>
            <p style={{ margin: "0", color: "#666" }}>
              {assessment.questions.length} questions • Estimated time:{" "}
              {assessment.estimated_duration_minutes} minutes • Difficulty:{" "}
              {assessment.difficulty_level.toFixed(1)}/5.0
            </p>
          </div>

          {assessment.questions.map((question, idx) => (
            <div
              key={question.question_id}
              style={{
                background: "white",
                padding: "1.5rem",
                borderRadius: "8px",
                marginBottom: "1.5rem",
                border: "1px solid #ddd",
              }}
            >
              <h3 style={{ marginTop: 0 }}>
                Question {idx + 1} of {assessment.questions.length}
              </h3>
              <p style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>{question.question}</p>
              <div>
                {question.options.map((option) => (
                  <label
                    key={option.option_id}
                    style={{
                      display: "block",
                      padding: "0.75rem",
                      marginBottom: "0.5rem",
                      background: answers[question.question_id] === option.option_id ? "#e3f2fd" : "#f5f5f5",
                      borderRadius: "4px",
                      cursor: "pointer",
                      border:
                        answers[question.question_id] === option.option_id
                          ? "2px solid #007bff"
                          : "1px solid #ddd",
                    }}
                  >
                    <input
                      type="radio"
                      name={question.question_id}
                      value={option.option_id}
                      checked={answers[question.question_id] === option.option_id}
                      onChange={() => handleAnswerChange(question.question_id, option.option_id)}
                      style={{ marginRight: "0.75rem" }}
                    />
                    <strong>{option.option_id.toUpperCase()}.</strong> {option.text}
                  </label>
                ))}
              </div>
            </div>
          ))}

          <div style={{ textAlign: "center", marginTop: "2rem" }}>
            <button
              onClick={submitTest}
              disabled={loading || !allQuestionsAnswered}
              style={{
                padding: "1rem 3rem",
                fontSize: "1.1rem",
                background: loading || !allQuestionsAnswered ? "#ccc" : "#28a745",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: loading || !allQuestionsAnswered ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Submitting..." : "Submit Test"}
            </button>
            {!allQuestionsAnswered && (
              <p style={{ color: "#c33", marginTop: "0.5rem" }}>
                Please answer all questions before submitting
              </p>
            )}
          </div>
        </div>
      )}

      {result && (
        <div style={{ marginTop: "2rem" }}>
          <div
            style={{
              background: "#d4edda",
              padding: "2rem",
              borderRadius: "8px",
              marginBottom: "2rem",
              textAlign: "center",
            }}
          >
            <h2 style={{ margin: "0 0 1rem 0" }}>Test Results</h2>
            <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#155724" }}>
              {result.percentage_correct.toFixed(1)}%
            </div>
            <p style={{ margin: "0.5rem 0", fontSize: "1.2rem" }}>
              Assessment Score: {result.score.toFixed(1)}/5.0
            </p>
            <p style={{ margin: "0.5rem 0", color: "#666" }}>
              {result.correct_answers} out of {result.total_questions} questions correct
            </p>
            {result.updated_proficiency !== undefined && (
              <div style={{ marginTop: "1rem", padding: "1rem", background: "white", borderRadius: "8px", border: "2px solid #28a745" }}>
                <p style={{ margin: "0.5rem 0", color: "#155724", fontWeight: "bold", fontSize: "1.1rem" }}>
                  ✅ Skill Proficiency Updated!
                </p>
                <p style={{ margin: "0.5rem 0", fontSize: "1.2rem", fontWeight: "bold", color: "#28a745" }}>
                  New Proficiency Level: {result.updated_proficiency.toFixed(1)}/5.0
                </p>
                <p style={{ margin: "0.5rem 0", color: "#666", fontSize: "0.9rem" }}>
                  Your skill level has been updated based on your assessment performance. 
                  This will be reflected in your employee profile and skill gap analysis.
                </p>
              </div>
            )}
          </div>

          <h3>Question Review</h3>
          {result.questions_with_feedback.map((question, idx) => (
            <div
              key={question.question_id}
              style={{
                background: question.is_correct ? "#d4edda" : "#f8d7da",
                padding: "1.5rem",
                borderRadius: "8px",
                marginBottom: "1rem",
                border: `2px solid ${question.is_correct ? "#28a745" : "#dc3545"}`,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <h4 style={{ margin: 0 }}>Question {idx + 1}</h4>
                <span
                  style={{
                    background: question.is_correct ? "#28a745" : "#dc3545",
                    color: "white",
                    padding: "0.25rem 0.75rem",
                    borderRadius: "4px",
                    fontSize: "0.9rem",
                  }}
                >
                  {question.is_correct ? "✓ Correct" : "✗ Incorrect"}
                </span>
              </div>
              <p style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>{question.question}</p>
              <div style={{ marginBottom: "1rem" }}>
                <p>
                  <strong>Your Answer:</strong> {question.user_answer?.toUpperCase()}
                </p>
                <p>
                  <strong>Correct Answer:</strong> {question.correct_answer_id?.toUpperCase()}
                </p>
              </div>
              {question.explanation && (
                <div
                  style={{
                    background: "white",
                    padding: "1rem",
                    borderRadius: "4px",
                    marginTop: "1rem",
                  }}
                >
                  <strong>Explanation:</strong>
                  <p style={{ margin: "0.5rem 0 0 0" }}>{question.explanation}</p>
                </div>
              )}
            </div>
          ))}

            <div style={{ textAlign: "center", marginTop: "2rem" }}>
            <button
              onClick={() => {
                setResult(null);
                setAssessment(null);
                setAnswers({});
                setSkillId("");
                // Refresh employee skills if we came from employee management
                if (sessionStorage.getItem('assessment_employee_id')) {
                  // Trigger a page refresh or reload employee skills
                  window.location.reload();
                }
              }}
              style={{
                padding: "0.75rem 2rem",
                fontSize: "1rem",
                background: "#007bff",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                marginRight: "1rem",
              }}
            >
              Take Another Test
            </button>
            <button
              onClick={() => {
                // Store employee ID for auto-refresh
                if (employeeId) {
                  sessionStorage.setItem('refresh_employee_skills', employeeId);
                }
                // Dispatch custom event to trigger navigation
                window.dispatchEvent(new CustomEvent('navigate', { detail: { page: 'employees' } }));
              }}
              style={{
                padding: "0.75rem 2rem",
                fontSize: "1rem",
                background: "#28a745",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              View Updated Skills
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

