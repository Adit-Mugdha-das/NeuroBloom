import axios from "axios";
import "./index3.js";
const resolveApiBaseUrl = () => {
  if (typeof window === "undefined") return "http://127.0.0.1:8000";
  const host = window.location.hostname === "localhost" ? "localhost" : "127.0.0.1";
  return `${window.location.protocol}//${host}:8000`;
};
const API_BASE_URL = resolveApiBaseUrl();
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);
