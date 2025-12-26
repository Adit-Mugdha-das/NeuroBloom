import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";
import Header from "../components/Header";

export default function MemoryTest() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  
  const [stage, setStage] = useState("intro"); // intro, memorize, recall, result
  const [words, setWords] = useState([]);
  const [userInput, setUserInput] = useState("");
  const [results, setResults] = useState(null);
  const [countdown, setCountdown] = useState(10);
  const [difficulty, setDifficulty] = useState("medium");

  useEffect(() => {
    if (stage === "memorize" && countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else if (stage === "memorize" && countdown === 0) {
      setStage("recall");
    }
  }, [countdown, stage]);

  const startTest = async () => {
    try {
      const response = await API.get(`/tasks/memory/start?difficulty=${difficulty}`);
      setWords(response.data.words);
      setCountdown(response.data.time_limit);
      setStage("memorize");
    } catch (error) {
      alert("Error starting test: " + error.message);
    }
  };

  const submitRecall = async () => {
    const userWords = userInput.toLowerCase().split(",").map(w => w.trim()).filter(w => w);
    const correctWords = words.filter(word => userWords.includes(word.toLowerCase()));
    const score = (correctWords.length / words.length) * 100;

    try {
      await API.post(`/tasks/results?user_id=${user.id}`, {
        task_type: "memory",
        score: score,
        details: JSON.stringify({
          words_shown: words,
          words_recalled: userWords,
          correct_words: correctWords,
          difficulty: difficulty
        })
      });

      setResults({
        score: score,
        correct: correctWords.length,
        total: words.length,
        correctWords: correctWords,
        missedWords: words.filter(w => !userWords.includes(w.toLowerCase()))
      });
      setStage("result");
    } catch (error) {
      alert("Error submitting results: " + error.message);
    }
  };

  return (
    <div style={styles.page}>
      <Header />
      
      <div style={styles.container}>
        {stage === "intro" && (
          <div style={styles.card}>
            <h2 style={styles.title}>🧩 Memory Recall Test</h2>
            <p style={styles.description}>
              You will see a list of words for 10 seconds. Try to memorize as many as you can.
              After the time is up, type all the words you remember separated by commas.
            </p>
            
            <div style={styles.difficultySection}>
              <label style={styles.label}>Select Difficulty:</label>
              <select 
                style={styles.select}
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option value="easy">Easy (5 simple words)</option>
                <option value="medium">Medium (7 words)</option>
                <option value="hard">Hard (9 complex words)</option>
              </select>
            </div>

            <button style={styles.startBtn} onClick={startTest}>
              Start Test
            </button>
          </div>
        )}

        {stage === "memorize" && (
          <div style={styles.card}>
            <h2 style={styles.title}>Memorize These Words</h2>
            <div style={styles.countdown}>Time Left: {countdown}s</div>
            
            <div style={styles.wordList}>
              {words.map((word, index) => (
                <div key={index} style={styles.word}>
                  {word}
                </div>
              ))}
            </div>
          </div>
        )}

        {stage === "recall" && (
          <div style={styles.card}>
            <h2 style={styles.title}>Recall the Words</h2>
            <p style={styles.description}>
              Type all the words you remember, separated by commas
            </p>
            
            <textarea
              style={styles.textarea}
              placeholder="e.g., apple, chair, music"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              rows={5}
            />

            <button style={styles.submitBtn} onClick={submitRecall}>
              Submit Answers
            </button>
          </div>
        )}

        {stage === "result" && results && (
          <div style={styles.card}>
            <h2 style={styles.title}>Test Results</h2>
            
            <div style={styles.scoreCircle}>
              <div style={styles.scoreNumber}>{Math.round(results.score)}%</div>
              <div style={styles.scoreLabel}>Accuracy</div>
            </div>

            <div style={styles.resultStats}>
              <div style={styles.statItem}>
                <span style={styles.statValue}>{results.correct}</span>
                <span style={styles.statLabel}>Correct</span>
              </div>
              <div style={styles.statItem}>
                <span style={styles.statValue}>{results.total - results.correct}</span>
                <span style={styles.statLabel}>Missed</span>
              </div>
              <div style={styles.statItem}>
                <span style={styles.statValue}>{results.total}</span>
                <span style={styles.statLabel}>Total</span>
              </div>
            </div>

            {results.correctWords.length > 0 && (
              <div style={styles.wordSection}>
                <h4 style={styles.sectionTitle}>✅ Correctly Recalled:</h4>
                <div style={styles.wordTags}>
                  {results.correctWords.map((word, i) => (
                    <span key={i} style={{...styles.tag, ...styles.correctTag}}>{word}</span>
                  ))}
                </div>
              </div>
            )}

            {results.missedWords.length > 0 && (
              <div style={styles.wordSection}>
                <h4 style={styles.sectionTitle}>❌ Missed Words:</h4>
                <div style={styles.wordTags}>
                  {results.missedWords.map((word, i) => (
                    <span key={i} style={{...styles.tag, ...styles.missedTag}}>{word}</span>
                  ))}
                </div>
              </div>
            )}

            <div style={styles.buttonGroup}>
              <button style={styles.retryBtn} onClick={() => {
                setStage("intro");
                setUserInput("");
                setResults(null);
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
    maxWidth: "800px",
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
  countdown: {
    fontSize: "24px",
    fontWeight: "bold",
    color: "#667eea",
    textAlign: "center",
    marginBottom: "30px",
  },
  wordList: {
    display: "flex",
    flexWrap: "wrap",
    gap: "15px",
    justifyContent: "center",
  },
  word: {
    background: "#667eea",
    color: "white",
    padding: "15px 30px",
    borderRadius: "8px",
    fontSize: "20px",
    fontWeight: "bold",
  },
  textarea: {
    width: "100%",
    padding: "15px",
    border: "2px solid #ddd",
    borderRadius: "8px",
    fontSize: "16px",
    marginBottom: "20px",
    fontFamily: "inherit",
    resize: "vertical",
  },
  submitBtn: {
    width: "100%",
    padding: "15px",
    background: "#43e97b",
    color: "white",
    border: "none",
    borderRadius: "8px",
    fontSize: "18px",
    fontWeight: "bold",
    cursor: "pointer",
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
  wordSection: {
    marginBottom: "20px",
  },
  sectionTitle: {
    fontSize: "16px",
    marginBottom: "10px",
    color: "#333",
  },
  wordTags: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
  },
  tag: {
    padding: "8px 15px",
    borderRadius: "20px",
    fontSize: "14px",
    fontWeight: "500",
  },
  correctTag: {
    background: "#d4edda",
    color: "#155724",
  },
  missedTag: {
    background: "#f8d7da",
    color: "#721c24",
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
