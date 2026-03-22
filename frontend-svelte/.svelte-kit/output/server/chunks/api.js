import axios from "axios";
const resolveApiBaseUrl = () => {
  if (typeof window === "undefined") return "http://127.0.0.1:8000";
  const host = window.location.hostname === "localhost" ? "localhost" : "127.0.0.1";
  return `${window.location.protocol}//${host}:8000`;
};
const API_BASE_URL = resolveApiBaseUrl();
axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});
