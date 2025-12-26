import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// Register
export const registerUser = (email, password) =>
  API.post("/auth/register", { email, password });

// Login
export const loginUser = (email, password) =>
  API.post("/auth/login", { email, password });

export default API;
