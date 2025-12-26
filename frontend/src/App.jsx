import { BrowserRouter, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AttentionTest from "./pages/AttentionTest";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import MemoryTest from "./pages/MemoryTest";
import Register from "./pages/Register";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/memory-test" 
          element={
            <ProtectedRoute>
              <MemoryTest />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/attention-test" 
          element={
            <ProtectedRoute>
              <AttentionTest />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
