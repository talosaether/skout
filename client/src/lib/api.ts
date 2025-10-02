export type Asset = {
  id: string;
  created_at: string;
  filename: string;
  mime: string;
  size: number;
};

export type User = {
  id: string;
  email: string;
  created_at: string;
};

export type AuthResponse = {
  token: string;
  user: User;
};

export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AuthError';
  }
}

function getAuthHeaders(token?: string): HeadersInit {
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// Authentication functions
export async function register(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || 'Registration failed');
  }

  return await res.json();
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });

  if (!res.ok) {
    const error = await res.text();
    if (res.status === 401) {
      throw new AuthError(error || 'Invalid email or password');
    }
    throw new Error(error || 'Login failed');
  }

  return await res.json();
}

export async function getCurrentUser(token: string): Promise<User> {
  const res = await fetch('/api/auth/me', {
    headers: getAuthHeaders(token)
  });

  if (!res.ok) {
    if (res.status === 401) {
      throw new AuthError('Invalid or expired token');
    }
    throw new Error('Failed to get user');
  }

  return await res.json();
}

// Asset functions with authentication
export async function listAssets(limit = 20, offset = 0, token?: string) {
  const res = await fetch(`/api/assets?limit=${limit}&offset=${offset}`, {
    headers: getAuthHeaders(token)
  });

  if (!res.ok) {
    if (res.status === 401) {
      throw new AuthError('Authentication required');
    }
    throw new Error("Failed to list assets");
  }

  return (await res.json()) as { items: Asset[]; total: number };
}

export async function uploadBlob(file: Blob, filename: string, token?: string) {
  const fd = new FormData();
  fd.append("file", file, filename);
  const res = await fetch("/api/assets", {
    method: "POST",
    headers: getAuthHeaders(token),
    body: fd
  });

  if (!res.ok) {
    if (res.status === 401) {
      throw new AuthError('Authentication required');
    }
    throw new Error("Upload failed");
  }

  return await res.json();
}

export async function deleteAsset(id: string, token?: string) {
  const res = await fetch(`/api/assets/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(token)
  });

  if (!res.ok) {
    if (res.status === 401) {
      throw new AuthError('Authentication required');
    }
    const errorText = await res.text();
    throw new Error(`Delete failed: ${res.status} ${errorText}`);
  }
}