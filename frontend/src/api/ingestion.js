import { apiClient } from "./client";

export const uploadCsv = ({ file, sourceType }) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("company", 1);

  return apiClient.post(`/upload/${sourceType}/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const getRecords = (options = {}) =>
  apiClient.get("/records/", options);

export const approveRecord = (recordId) =>
  apiClient.post(`/records/${recordId}/approve/`);

export const rejectRecord = (recordId) =>
  apiClient.post(`/records/${recordId}/reject/`);
