import api from "./api";

export async function requestToken(email, password) {
  const form = new URLSearchParams({ username: email, password });
  const response = await api.post("/auth/login", form);
  return response.data.access_token;
}
