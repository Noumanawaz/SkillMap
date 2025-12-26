import React, { useState } from "react";
import { StrategyDashboard } from "./pages/StrategyDashboard";
import { SkillGapExplorer } from "./pages/SkillGapExplorer";
import { EmployeeLearningCockpit } from "./pages/EmployeeLearningCockpit";
import { EmployeeManagement } from "./pages/EmployeeManagement";
import { GoalManagement } from "./pages/GoalManagement";
import { SkillAssessment } from "./pages/SkillAssessment";
import "./App.css";

type Page = "strategy" | "gaps" | "learning" | "employees" | "goals" | "assessment";

const App: React.FC = () => {
  const [page, setPage] = useState<Page>("strategy");

  // Listen for navigation events from child components
  React.useEffect(() => {
    const handleNavigate = (event: CustomEvent) => {
      if (event.detail && event.detail.page) {
        setPage(event.detail.page as Page);
      }
    };

    window.addEventListener('navigate', handleNavigate as EventListener);
    return () => {
      window.removeEventListener('navigate', handleNavigate as EventListener);
    };
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>SkillMap AI</h1>
        <p className="subtitle">Cognitive Workforce Development Platform</p>
      </header>
      <nav className="app-nav">
        <button
          className={page === "strategy" ? "active" : ""}
          onClick={() => setPage("strategy")}
        >
          📊 Strategy Dashboard
        </button>
        <button
          className={page === "gaps" ? "active" : ""}
          onClick={() => setPage("gaps")}
        >
          🔍 Skill Gap Explorer
        </button>
        <button
          className={page === "learning" ? "active" : ""}
          onClick={() => setPage("learning")}
        >
          🎓 Learning Cockpit
        </button>
        <button
          className={page === "employees" ? "active" : ""}
          onClick={() => setPage("employees")}
        >
          👥 Employees
        </button>
        <button
          className={page === "goals" ? "active" : ""}
          onClick={() => setPage("goals")}
        >
          🎯 Goals
        </button>
        <button
          className={page === "assessment" ? "active" : ""}
          onClick={() => setPage("assessment")}
        >
          📝 Skill Assessment
        </button>
      </nav>
      <main className="app-main">
        {page === "strategy" && <StrategyDashboard />}
        {page === "gaps" && <SkillGapExplorer />}
        {page === "learning" && <EmployeeLearningCockpit />}
        {page === "employees" && <EmployeeManagement />}
        {page === "goals" && <GoalManagement />}
        {page === "assessment" && <SkillAssessment />}
      </main>
    </div>
  );
};

export default App;
