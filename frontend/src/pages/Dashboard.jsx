import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import API from "../api";
import Header from "../components/Header";

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);
      fetchUserStats(parsedUser.id);
    }
  }, []);

  const fetchUserStats = async (userId) => {
    try {
      const response = await API.get(`/tasks/results/${userId}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const cognitiveModules = [
    {
      id: 1,
      title: "Memory Recall",
      description: "Test your working memory with word sequences",
      icon: "🧩",
      color: "#667eea",
      status: "Available",
      link: "/memory-test",
    },
    {
      id: 2,
      title: "Attention Test",
      description: "Measure focus and reaction time",
      icon: "🎯",
      color: "#f093fb",
      status: "Available",
      link: "/attention-test",
    },
    {
      id: 3,
      title: "Processing Speed",
      description: "Quick symbol matching exercises",
      icon: "⚡",
      color: "#4facfe",
      status: "Coming Soon",
    },
    {
      id: 4,
      title: "Executive Function",
      description: "Problem-solving and decision tasks",
      icon: "🧠",
      color: "#43e97b",
      status: "Coming Soon",
    },
  ];

  return (
    <div style={styles.page}>
      <Header />
      
      <div style={styles.container}>
        <div style={styles.welcomeSection}>
          <h2 style={styles.welcomeTitle}>
            Welcome back, {user?.email?.split('@')[0] || 'User'}! 👋
          </h2>
          <p style={styles.subtitle}>
            Track your cognitive health journey with personalized training modules
          </p>
        </div>

        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <div style={styles.statNumber}>{stats?.total_sessions || 0}</div>
            <div style={styles.statLabel}>Sessions Completed</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statNumber}>{Object.keys(stats?.tasks_by_type || {}).length}</div>
            <div style={styles.statLabel}>Tasks Available</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statNumber}>
              {stats?.average_score ? `${stats.average_score}%` : '-'}
            </div>
            <div style={styles.statLabel}>Average Score</div>
          </div>
          <div style={styles.statCard}>
            <div style={styles.statNumber}>
              {stats?.total_sessions ? Math.min(stats.total_sessions, 7) : 0}
            </div>
            <div style={styles.statLabel}>Day Streak</div>
          </div>
        </div>

        <h3 style={styles.sectionTitle}>Cognitive Training Modules</h3>
        
        <div style={styles.modulesGrid}>
          {cognitiveModules.map((module) => (
            <div 
              key={module.id} 
              style={{...styles.moduleCard, borderTop: `4px solid ${module.color}`}}
            >
              <div style={styles.moduleIcon}>{module.icon}</div>
              <h4 style={styles.moduleTitle}>{module.title}</h4>
              <p style={styles.moduleDescription}>{module.description}</p>
              <button 
                style={{...styles.moduleBtn, background: module.color}}
                disabled={module.status === "Coming Soon"}
                onClick={() => module.link && navigate(module.link)}
              >
                {module.status === "Coming Soon" ? "Coming Soon" : "Start Training"}
              </button>
            </div>
          ))}
        </div>

        {stats && stats.recent_scores && stats.recent_scores.length > 0 && (
          <>
            <h3 style={styles.sectionTitle}>Performance Trends</h3>
            <div style={styles.chartCard}>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={stats.recent_scores.reverse()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="score" 
                    stroke="#667eea" 
                    strokeWidth={3}
                    dot={{ fill: '#667eea', r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <h3 style={styles.sectionTitle}>Recent Sessions</h3>
            <div style={styles.tableCard}>
              <table style={styles.table}>
                <thead>
                  <tr style={styles.tableHeader}>
                    <th style={styles.th}>Date</th>
                    <th style={styles.th}>Task</th>
                    <th style={styles.th}>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_scores.slice(0, 5).map((session, index) => (
                    <tr key={index} style={styles.tableRow}>
                      <td style={styles.td}>{session.date}</td>
                      <td style={styles.td}>
                        <span style={styles.taskBadge}>
                          {session.task_type === 'memory' ? '🧩 Memory' : 
                           session.task_type === 'attention' ? '🎯 Attention' : 
                           session.task_type}
                        </span>
                      </td>
                      <td style={styles.td}>
                        <span style={{
                          ...styles.scoreBadge,
                          background: session.score >= 70 ? '#d4edda' : session.score >= 50 ? '#fff3cd' : '#f8d7da',
                          color: session.score >= 70 ? '#155724' : session.score >= 50 ? '#856404' : '#721c24'
                        }}>
                          {session.score.toFixed(1)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}

        <div style={styles.infoBox}>
          <h4 style={styles.infoTitle}>📊 Your Progress Journey</h4>
          <p style={styles.infoText}>
            Complete cognitive tasks regularly to track your mental fitness over time. 
            Your personalized dashboard will show improvement trends, insights, and recommendations.
          </p>
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#f5f7fa",
  },
  container: {
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "40px 20px",
  },
  welcomeSection: {
    textAlign: "center",
    marginBottom: "40px",
  },
  welcomeTitle: {
    fontSize: "32px",
    color: "#333",
    marginBottom: "10px",
  },
  subtitle: {
    fontSize: "16px",
    color: "#666",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    gap: "20px",
    marginBottom: "50px",
  },
  statCard: {
    background: "white",
    padding: "30px",
    borderRadius: "10px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
    textAlign: "center",
  },
  statNumber: {
    fontSize: "36px",
    fontWeight: "bold",
    color: "#667eea",
    marginBottom: "10px",
  },
  statLabel: {
    fontSize: "14px",
    color: "#666",
    textTransform: "uppercase",
    letterSpacing: "1px",
  },
  sectionTitle: {
    fontSize: "24px",
    color: "#333",
    marginBottom: "30px",
  },
  modulesGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
    gap: "25px",
    marginBottom: "40px",
  },
  moduleCard: {
    background: "white",
    padding: "30px",
    borderRadius: "10px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
    textAlign: "center",
    transition: "transform 0.3s, box-shadow 0.3s",
  },
  moduleIcon: {
    fontSize: "48px",
    marginBottom: "15px",
  },
  moduleTitle: {
    fontSize: "20px",
    color: "#333",
    marginBottom: "10px",
  },
  moduleDescription: {
    fontSize: "14px",
    color: "#666",
    marginBottom: "20px",
    lineHeight: "1.5",
  },
  moduleBtn: {
    width: "100%",
    padding: "12px",
    border: "none",
    borderRadius: "5px",
    color: "white",
    fontSize: "14px",
    fontWeight: "bold",
    cursor: "pointer",
    transition: "opacity 0.3s",
  },
  infoBox: {
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    color: "white",
    padding: "30px",
    borderRadius: "10px",
    marginTop: "40px",
  },
  infoTitle: {
    fontSize: "20px",
    marginBottom: "10px",
  },
  infoText: {
    fontSize: "14px",
    lineHeight: "1.6",
    opacity: 0.9,
  },
  chartCard: {
    background: "white",
    padding: "30px",
    borderRadius: "10px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
    marginBottom: "40px",
  },
  tableCard: {
    background: "white",
    borderRadius: "10px",
    boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
    overflow: "hidden",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
  },
  tableHeader: {
    background: "#f5f7fa",
  },
  th: {
    padding: "15px",
    textAlign: "left",
    fontSize: "14px",
    fontWeight: "bold",
    color: "#333",
    borderBottom: "2px solid #e0e0e0",
  },
  tableRow: {
    borderBottom: "1px solid #f0f0f0",
  },
  td: {
    padding: "15px",
    fontSize: "14px",
    color: "#666",
  },
  taskBadge: {
    padding: "4px 12px",
    background: "#e3f2fd",
    color: "#1976d2",
    borderRadius: "12px",
    fontSize: "13px",
    fontWeight: "500",
  },
  scoreBadge: {
    padding: "4px 12px",
    borderRadius: "12px",
    fontSize: "13px",
    fontWeight: "bold",
  },
};
