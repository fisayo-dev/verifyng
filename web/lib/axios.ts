import axios from "axios";

const fallbackBaseURL = "https://olatunjitobi-verifyng-api.hf.space/api";
const baseURL =
  process.env.NEXT_PUBLIC_BACKEND_URL?.replace(/\/+$/, "") || fallbackBaseURL;

const api = axios.create({
  baseURL,
  timeout: 30000,
});

export default api;
