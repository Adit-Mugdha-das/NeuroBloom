import { useNavigate } from "react-router-dom";

export default function Header() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/");
  };

  return (
    <header style={styles.header}>
      <div style={styles.container}>
        <h1 style={styles.logo}>🧠 NeuroBloom</h1>
        <div style={styles.userSection}>
          <span style={styles.email}>{user.email}</span>
          <button style={styles.logoutBtn} onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

const styles = {
  header: {
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    color: "white",
    padding: "15px 0",
    boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
  },
  container: {
    maxWidth: "1200px",
    margin: "0 auto",
    padding: "0 20px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  logo: {
    margin: 0,
    fontSize: "24px",
  },
  userSection: {
    display: "flex",
    alignItems: "center",
    gap: "15px",
  },
  email: {
    fontSize: "14px",
  },
  logoutBtn: {
    background: "rgba(255,255,255,0.2)",
    border: "1px solid white",
    color: "white",
    padding: "8px 20px",
    borderRadius: "5px",
    cursor: "pointer",
    fontSize: "14px",
    transition: "background 0.3s",
  },
};
