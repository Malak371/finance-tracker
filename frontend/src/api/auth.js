import api from "./api";

export async function requestToken(email, password) {
  const form = new URLSearchParams({ username: email, password });
  const response = await api.post("/auth/login", form);
  return response.data.access_token;
}

// Creates a private, pre-filled demo account and returns a token for it.
export async function requestDemoToken() {
  const response = await api.post("/auth/demo");
  return response.data.access_token;
}
