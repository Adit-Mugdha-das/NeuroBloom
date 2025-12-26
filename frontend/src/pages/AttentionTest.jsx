import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";
import Header from "../components/Header";

export default function AttentionTest() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  
  const [stage, setStage] = useState("intro"); // intro, ready, testing, result
  const [results, setResults] = useState([]);
  const [currentRound, setCurrentRound] = useState(0);
  const [startTime, setStartTime] = useState(0);
  const [showTarget, setShowTarget] = useState(false);
  const [countdown, setCountdown] = useState(3);
  const [difficulty, setDifficulty] = useState("medium");
  const totalRounds = 10;

  const difficultySettings = {
    easy: { minDelay: 2000, maxDelay: 4000, name: "Easy" },
    medium: { minDelay: 1000, maxDelay: 3000, name: "Medium" },
    hard: { minDelay: 500, maxDelay: 2000, name: "Hard" }
  };

  useEffect(() => {
    if (stage === "ready" && countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else if (stage === "ready" && countdown === 0) {
      setStage("testing");
      scheduleNextTarget();
    }
  }, [countdown, stage]);

  useEffect(() => {
    if (stage === "testing" && currentRound >= totalRounds) {
      calculateResults();
    }
  }, [currentRound, stage]);

  const scheduleNextTarget = () => {
    const settings = difficultySettings[difficulty];
    const delay = Math.random() * (settings.maxDelay - settings.minDelay) + settings.minDelay;
    
    setTimeout(() => {
      setShowTarget(true);
      setStartTime(Date.now());
    }, delay);
  };

  const handleClick = () => {
    if (!showTarget) {
      // Clicked too early
      setResults([...results, { round: currentRound + 1, reactionTime: -1, tooEarly: true }]);
    } else {
      // Correct click
      const reactionTime = Date.now() - startTime;
      setResults([...results, { round: currentRound + 1, reactionTime, tooEarly: false }]);
    }
    
    setShowTarget(false);
    setCurrentRound(currentRound + 1);
    
    if (currentRound + 1 < totalRounds) {
      scheduleNextTarget();
    }
  };

  const calculateResults = async () => {
    const validReactions = results.filter(r => !r.tooEarly && r.reactionTime > 0);
    const tooEarlyCount = results.filter(r => r.tooEarly).length;
    const missedCount = totalRounds - results.length;
    
    const avgReactionTime = validReactions.length > 0
      ? validReactions.reduce((sum, r) => sum + r.reactionTime, 0) / validReactions.length
      : 0;

    // Score calculation: base 100, -5 for each too early, -10 for each miss, bonus for fast reactions
    let score = 100;
    score -= tooEarlyCount * 5;
    score -= missedCount * 10;
    
    // Bonus for reaction time (faster = better)
    if (avgReactionTime > 0 && avgReactionTime < 300) score += 20;
    else if (avgReactionTime < 500) score += 10;
    
    score = Math.max(0, Math.min(100, score));

    try {
      await API.post(`/tasks/results?user_id=${user.id}`, {
        task_type: "attention",
        score: score,
        details: JSON.stringify({
          average_reaction_time: avgReactionTime,
          valid_clicks: validReactions.length,
          too_early: tooEarlyCount,
          missed: missedCount,
          difficulty: difficulty,
          all_times: validReactions.map(r => r.reactionTime)
        })
      });

      setStage("result");
    } catch (error) {
      alert("Error submitting results: " + error.message);
    }
  };

  const startTest = () => {
    setStage("ready");
    setCountdown(3);
    setResults([]);
    setCurrentRound(0);
  };

  const validReactions = results.filter(r => !r.tooEarly && r.reactionTime > 0);
  const avgReactionTime = validReactions.length > 0
    ? validReactions.reduce((sum, r) => sum + r.reactionTime, 0) / validReactions.length
    : 0;

  return (
    <div style={styles.page}>
      <Header />
      
      <div style={styles.container}>
        {stage === "intro" && (
          <div style={styles.card}>
            <h2 style={styles.title}>🎯 Attention & Reaction Test</h2>
            <p style={styles.description}>
              A target will appear at random intervals. Click as quickly as possible when you see it.
              Don't click too early! You'll have {totalRounds} rounds to test your reaction speed.
            </p>
            
            <div style={styles.difficultySection}>
              <label style={styles.label}>Select Difficulty:</label>
              <select 
                style={styles.select}
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option value="easy">Easy (2-4s delays)</option>
                <option value="medium">Medium (1-3s delays)</option>
                <option value="hard">Hard (0.5-2s delays)</option>
              </select>
            </div>

            <button style={styles.startBtn} onClick={startTest}>
              Start Test
            </button>
          </div>
        )}

        {stage === "ready" && (
          <div style={styles.card}>
            <h2 style={styles.title}>Get Ready!</h2>
            <div style={styles.bigCountdown}>{countdown}</div>
            <p style={styles.instruction}>Click when you see the green circle</p>
          </div>
        )}

        {stage === "testing" && (
          <div 
            style={{
              ...styles.testArea,
              background: showTarget ? "#43e97b" : "#f5f7fa"
            }}
            onClick={handleClick}
          >
            <div style={styles.roundCounter}>
              Round {currentRound + 1} of {totalRounds}
            </div>
            
            {showTarget ? (
              <div style={styles.target}>
                <div style={styles.targetCircle}>CLICK!</div>
              </div>
            ) : (
              <div style={styles.waiting}>
                <p style={styles.waitText}>Wait for the green screen...</p>
                {currentRound > 0 && results[currentRound - 1]?.tooEarly && (
                  <p style={styles.errorText}>❌ Too early! Wait for green.</p>
                )}
              </div>
            )}
          </div>
        )}

        {stage === "result" && (
          <div style={styles.card}>
            <h2 style={styles.title}>Test Results</h2>
            
            <div style={styles.scoreCircle}>
              <div style={styles.scoreNumber}>
                {Math.round((100 - results.filter(r => r.tooEarly).length * 5) * 
                (validReactions.length / totalRounds))}%
              </div>
              <div style={styles.scoreLabel}>Overall Score</div>
            </div>

            <div style={styles.resultStats}>
              <div style={styles.statItem}>
                <span style={styles.statValue}>{avgReactionTime.toFixed(0)}</span>
                <span style={styles.statLabel}>Avg Time (ms)</span>
              </div>
              <div style={styles.statItem}>
                <span style={styles.statValue}>{validReactions.length}</span>
                <span style={styles.statLabel}>Valid Clicks</span>
              </div>
              <div style={styles.statItem}>
                <span style={styles.statValue}>{results.filter(r => r.tooEarly).length}</span>
                <span style={styles.statLabel}>Too Early</span>
              </div>
            </div>

            <div style={styles.performanceSection}>
              <h4 style={styles.sectionTitle}>Performance Rating:</h4>
              <div style={styles.ratingBar}>
                <div style={{
                  ...styles.ratingFill,
                  width: avgReactionTime < 300 ? "100%" : avgReactionTime < 500 ? "70%" : "40%",
                  background: avgReactionTime < 300 ? "#43e97b" : avgReactionTime < 500 ? "#ffd93d" : "#ff6b6b"
                }}>
                  {avgReactionTime < 300 ? "⚡ Excellent!" : 
                   avgReactionTime < 500 ? "👍 Good" : "😊 Keep Practicing"}
                </div>
              </div>
            </div>

            {validReactions.length > 0 && (
              <div style={styles.timesSection}>
                <h4 style={styles.sectionTitle}>Individual Reaction Times:</h4>
                <div style={styles.timesList}>
                  {validReactions.slice(0, 10).map((r, i) => (
                    <span key={i} style={styles.timeChip}>
                      {r.reactionTime}ms
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div style={styles.buttonGroup}>
              <button style={styles.retryBtn} onClick={() => {
                setStage("intro");
                setResults([]);
                setCurrentRound(0);
              }}>
                Try Again
              </button>
              <button style={styles.dashboardBtn} onClick={() => navigate("/dashboard")}>
                Back to Dashboard
              </button>
            </div>
          </div>
        )}
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
    maxWidth: "900px",
    margin: "0 auto",
    padding: "40px 20px",
  },
  card: {
    background: "white",
    padding: "40px",
    borderRadius: "15px",
    boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
  },
  title: {
    fontSize: "28px",
    color: "#333",
    marginBottom: "20px",
    textAlign: "center",
  },
  description: {
    fontSize: "16px",
    color: "#666",
    lineHeight: "1.6",
    textAlign: "center",
    marginBottom: "30px",
  },
  difficultySection: {
    marginBottom: "30px",
  },
  label: {
    display: "block",
    fontSize: "14px",
    color: "#333",
    marginBottom: "10px",
    fontWeight: "bold",
  },
  select: {
    width: "100%",
    padding: "12px",
    border: "1px solid #ddd",
    borderRadius: "5px",
    fontSize: "14px",
  },
  startBtn: {
    width: "100%",
    padding: "15px",
    background: "#667eea",
    color: "white",
    border: "none",
    borderRadius: "8px",
    fontSize: "18px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  bigCountdown: {
    fontSize: "120px",
    fontWeight: "bold",
    color: "#667eea",
    textAlign: "center",
    margin: "40px 0",
  },
  instruction: {
    fontSize: "18px",
    color: "#666",
    textAlign: "center",
  },
  testArea: {
    height: "500px",
    borderRadius: "15px",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    cursor: "pointer",
    position: "relative",
    transition: "background 0.3s",
  },
  roundCounter: {
    position: "absolute",
    top: "20px",
    right: "20px",
    background: "white",
    padding: "10px 20px",
    borderRadius: "20px",
    fontSize: "14px",
    fontWeight: "bold",
    color: "#333",
  },
  target: {
    textAlign: "center",
  },
  targetCircle: {
    width: "200px",
    height: "200px",
    borderRadius: "50%",
    background: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "32px",
    fontWeight: "bold",
    color: "#43e97b",
    boxShadow: "0 10px 40px rgba(0,0,0,0.2)",
    animation: "pulse 0.5s infinite",
  },
  waiting: {
    textAlign: "center",
  },
  waitText: {
    fontSize: "24px",
    color: "#666",
  },
  errorText: {
    fontSize: "18px",
    color: "#ff6b6b",
    marginTop: "20px",
  },
  scoreCircle: {
    textAlign: "center",
    marginBottom: "30px",
  },
  scoreNumber: {
    fontSize: "64px",
    fontWeight: "bold",
    color: "#667eea",
  },
  scoreLabel: {
    fontSize: "16px",
    color: "#666",
  },
  resultStats: {
    display: "flex",
    justifyContent: "space-around",
    marginBottom: "30px",
    padding: "20px",
    background: "#f5f7fa",
    borderRadius: "10px",
  },
  statItem: {
    textAlign: "center",
  },
  statValue: {
    display: "block",
    fontSize: "32px",
    fontWeight: "bold",
    color: "#333",
  },
  performanceSection: {
    marginBottom: "30px",
  },
  sectionTitle: {
    fontSize: "16px",
    marginBottom: "15px",
    color: "#333",
  },
  ratingBar: {
    height: "50px",
    background: "#e0e0e0",
    borderRadius: "25px",
    overflow: "hidden",
  },
  ratingFill: {
    height: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "white",
    fontSize: "16px",
    fontWeight: "bold",
    transition: "width 0.5s",
  },
  timesSection: {
    marginBottom: "30px",
  },
  timesList: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
  },
  timeChip: {
    padding: "8px 15px",
    background: "#e3f2fd",
    color: "#1976d2",
    borderRadius: "20px",
    fontSize: "14px",
    fontWeight: "500",
  },
  buttonGroup: {
    display: "flex",
    gap: "15px",
    marginTop: "30px",
  },
  retryBtn: {
    flex: 1,
    padding: "12px",
    background: "#667eea",
    color: "white",
    border: "none",
    borderRadius: "8px",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer",
  },
  dashboardBtn: {
    flex: 1,
    padding: "12px",
    background: "#6c757d",
    color: "white",
    border: "none",
    borderRadius: "8px",
    fontSize: "16px",
    fontWeight: "bold",
    cursor: "pointer",
  },
};
