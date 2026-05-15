import axios from "axios";

const baseURL = process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/+$/, "");

const api = axios.create({
  baseURL,
  timeout: 30000,
});

export default api;
