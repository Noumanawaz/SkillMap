import React, { useEffect, useRef } from "react";

export const LandingPage: React.FC = () => {
  const sectionRefs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -100px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate-in");
        }
      });
    }, observerOptions);

    // Observe sections
    sectionRefs.current.forEach((ref) => {
      if (ref) observer.observe(ref);
    });

    // Observe individual cards with a slight delay for staggered effect
    const cards = document.querySelectorAll('.animate-on-scroll');
    cards.forEach((card) => {
      observer.observe(card);
    });

    return () => {
      sectionRefs.current.forEach((ref) => {
        if (ref) observer.unobserve(ref);
      });
      cards.forEach((card) => {
        observer.unobserve(card);
      });
    };
  }, []);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">
            Transform Your Workforce with
            <span className="gradient-text"> AI-Powered Skill Development</span>
          </h1>
          <p className="hero-subtitle">
            SkillMap AI is a cognitive workforce development platform that uses advanced AI and 
            psychometric modeling to identify skill gaps, create personalized learning paths, 
            and help organizations build future-ready teams.
          </p>
          <div className="hero-buttons">
            <button 
              className="btn btn-primary btn-large"
              onClick={() => {
                const event = new CustomEvent('navigate', { detail: { page: 'goals' } });
                window.dispatchEvent(event);
              }}
            >
              Get Started →
            </button>
            <button 
              className="btn btn-secondary btn-large"
              onClick={() => scrollToSection('features')}
            >
              Learn More
            </button>
          </div>
        </div>
      </section>

      {/* Problem Statement */}
      <section 
        ref={(el) => (sectionRefs.current[0] = el)}
        className="section problem-section fade-in-section"
      >
        <div className="container">
          <h2 className="section-title">The Challenge</h2>
          <div className="problem-grid">
            <div className="problem-card animate-on-scroll">
              <div className="problem-icon">📊</div>
              <h3>Skill Gaps Are Hard to Identify</h3>
              <p>
                Organizations struggle to understand the exact skills their workforce needs 
                to achieve strategic goals, leading to misaligned training and development efforts.
              </p>
            </div>
            <div className="problem-card animate-on-scroll">
              <div className="problem-icon">⏱️</div>
              <h3>One-Size-Fits-All Learning</h3>
              <p>
                Traditional training programs don't account for individual learning styles, 
                current skill levels, or cognitive profiles, resulting in inefficient learning.
              </p>
            </div>
            <div className="problem-card animate-on-scroll">
              <div className="problem-icon">🎯</div>
              <h3>Strategic Misalignment</h3>
              <p>
                Without clear connections between strategic goals and required skills, 
                organizations can't effectively plan workforce development or measure readiness.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Solution - How It Helps */}
      <section 
        id="features"
        ref={(el) => (sectionRefs.current[1] = el)}
        className="section solution-section fade-in-section"
      >
        <div className="container">
          <h2 className="section-title">How SkillMap AI Helps</h2>
          <div className="features-grid">
            <div className="feature-card animate-on-scroll">
              <div className="feature-icon">🧠</div>
              <h3>Cognitive Profiling</h3>
              <p>
                Uses Item Response Theory (IRT) to create accurate cognitive profiles for each 
                employee, measuring their ability levels across different skills with scientific precision.
              </p>
            </div>
            <div className="feature-card animate-on-scroll">
              <div className="feature-icon">🔍</div>
              <h3>Intelligent Gap Analysis</h3>
              <p>
                Automatically identifies skill gaps between current employee capabilities and 
                strategic goal requirements using AI-powered semantic analysis and vector similarity.
              </p>
            </div>
            <div className="feature-card animate-on-scroll">
              <div className="feature-icon">🎓</div>
              <h3>Personalized Learning Paths</h3>
              <p>
                Generates customized learning paths that adapt to each employee's cognitive profile, 
                learning style, and time constraints, ensuring maximum learning efficiency.
              </p>
            </div>
            <div className="feature-card animate-on-scroll">
              <div className="feature-icon">🤖</div>
              <h3>AI-Powered Content Generation</h3>
              <p>
                Automatically creates learning modules on-demand when content doesn't exist, 
                using OpenAI GPT-3.5 to generate tailored micro-lessons, exercises, and assessments.
              </p>
            </div>
            <div className="feature-card animate-on-scroll">
              <div className="feature-icon">📈</div>
              <h3>Strategic Alignment</h3>
              <p>
                Connects strategic goals directly to required skills, enabling organizations to 
                measure workforce readiness and plan development initiatives with data-driven insights.
              </p>
            </div>
            <div className="feature-card animate-on-scroll">
              <div className="feature-icon">👥</div>
              <h3>Team-Level Insights</h3>
              <p>
                Analyzes skill gaps at both individual and team levels, helping managers understand 
                collective capabilities and plan team development strategies.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section 
        ref={(el) => (sectionRefs.current[2] = el)}
        className="section how-it-works-section fade-in-section"
      >
        <div className="container">
          <h2 className="section-title">How It Works</h2>
          <div className="steps-container">
            <div className="step animate-on-scroll">
              <div className="step-number">1</div>
              <h3>Define Strategic Goals</h3>
              <p>
                Create and manage strategic goals that align with your organization's objectives. 
                Each goal represents a future state your workforce needs to achieve.
              </p>
            </div>
            <div className="step-arrow animate-arrow">→</div>
            <div className="step animate-on-scroll">
              <div className="step-number">2</div>
              <h3>Assess Employee Skills</h3>
              <p>
                Employees complete skill assessments that use IRT modeling to accurately measure 
                their current ability levels across different skill domains.
              </p>
            </div>
            <div className="step-arrow animate-arrow">→</div>
            <div className="step animate-on-scroll">
              <div className="step-number">3</div>
              <h3>Identify Skill Gaps</h3>
              <p>
                The system automatically compares employee capabilities against goal requirements, 
                identifying gaps with precision using AI-powered semantic analysis.
              </p>
            </div>
            <div className="step-arrow animate-arrow">→</div>
            <div className="step animate-on-scroll">
              <div className="step-number">4</div>
              <h3>Generate Learning Paths</h3>
              <p>
                AI creates personalized learning paths that adapt to each employee's profile, 
                generating content on-demand when needed and prioritizing based on time horizons.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section 
        ref={(el) => (sectionRefs.current[3] = el)}
        className="section benefits-section fade-in-section"
      >
        <div className="container">
          <h2 className="section-title">Benefits</h2>
          <div className="benefits-grid">
            <div className="benefit-item animate-on-scroll">
              <h3>For Organizations</h3>
              <ul>
                <li>✓ Data-driven workforce planning</li>
                <li>✓ Strategic goal alignment</li>
                <li>✓ Reduced training costs through targeted learning</li>
                <li>✓ Improved employee readiness metrics</li>
                <li>✓ Better ROI on learning investments</li>
              </ul>
            </div>
            <div className="benefit-item animate-on-scroll">
              <h3>For Employees</h3>
              <ul>
                <li>✓ Personalized learning experiences</li>
                <li>✓ Clear career development paths</li>
                <li>✓ Adaptive content that matches their level</li>
                <li>✓ Transparent skill gap visibility</li>
                <li>✓ Efficient, focused learning</li>
              </ul>
            </div>
            <div className="benefit-item animate-on-scroll">
              <h3>For Managers</h3>
              <ul>
                <li>✓ Team skill gap insights</li>
                <li>✓ Individual development tracking</li>
                <li>✓ Strategic planning support</li>
                <li>✓ Readiness score metrics</li>
                <li>✓ Evidence-based decision making</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section 
        ref={(el) => (sectionRefs.current[4] = el)}
        className="section cta-section fade-in-section"
      >
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Transform Your Workforce?</h2>
            <p>
              Start using SkillMap AI today to build a future-ready workforce with 
              AI-powered skill development and personalized learning paths.
            </p>
            <button 
              className="btn btn-primary btn-large"
              onClick={() => {
                const event = new CustomEvent('navigate', { detail: { page: 'goals' } });
                window.dispatchEvent(event);
              }}
            >
              Get Started Now →
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};

