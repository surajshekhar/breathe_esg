import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL,
  timeout: 15000,
});

export const getErrorMessage = (error) => {
  if (error?.response?.data?.error) {
    const payload = error.response.data.error;
    if (typeof payload === "string") {
      return payload;
    }
    if (payload?.message) {
      return payload.message;
    }
  }
  if (error?.code === "ECONNABORTED") {
    return "Request timed out. Ensure the backend is running and try again.";
  }

  return error?.message || "Something went wrong";
};
