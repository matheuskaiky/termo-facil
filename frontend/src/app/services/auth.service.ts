import { Injectable } from '@angular/core';
import axios from 'axios';

const TOKEN_KEY = 'access_token';
const PROFILE_KEY = 'user_profile';
const BASE_URL = 'http://localhost:8000/api/v1';

export interface JwtUser {
  sub: string;
  nome?: string;
  matricula?: string;
  cargo: string | null;
  permissoes: string[];
  must_change_password: boolean;
  exp: number;
}

@Injectable({ providedIn: 'root' })
export class AuthService {

  getToken(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;
    const user = this.decodeToken(token);
    if (!user) return false;
    return user.exp * 1000 > Date.now();
  }

  getCurrentUser(): JwtUser | null {
    const token = this.getToken();
    if (!token) return null;
    const user = this.decodeToken(token);
    if (!user) return null;
    const profile = this._getStoredProfile();
    return { ...user, nome: profile?.nome ?? user.nome ?? '', matricula: profile?.matricula ?? user.matricula ?? '' };
  }

  async login(matricula: string, senha: string): Promise<void> {
    const response = await axios.post(`${BASE_URL}/auth/login`, { matricula, senha });
    const token = response.data.access_token;
    sessionStorage.setItem(TOKEN_KEY, token);
    const profileResp = await axios.get(`${BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    sessionStorage.setItem(PROFILE_KEY, JSON.stringify({
      nome: profileResp.data.nome,
      matricula: profileResp.data.matricula,
    }));
  }

  async changePassword(novaSenha: string): Promise<void> {
    const token = this.getToken();
    const response = await axios.post(
      `${BASE_URL}/auth/change-password`,
      { nova_senha: novaSenha },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    sessionStorage.setItem(TOKEN_KEY, response.data.access_token);
  }

  logout(): void {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(PROFILE_KEY);
  }

  private _getStoredProfile(): { nome: string; matricula: string } | null {
    const raw = sessionStorage.getItem(PROFILE_KEY);
    return raw ? JSON.parse(raw) : null;
  }

  private decodeToken(token: string): JwtUser | null {
    try {
      const payload = token.split('.')[1];
      const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
      return JSON.parse(atob(base64)) as JwtUser;
    } catch {
      return null;
    }
  }
}
