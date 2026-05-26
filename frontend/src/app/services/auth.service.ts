import { Injectable } from '@angular/core';
import axios from 'axios';

const TOKEN_KEY = 'access_token';
const BASE_URL = 'http://localhost:8000/api/v1';

export interface JwtUser {
  sub: string;
  nome: string;
  matricula: string;
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
    return this.decodeToken(token);
  }

  async login(matricula: string, senha: string): Promise<void> {
    const response = await axios.post(`${BASE_URL}/auth/login`, { matricula, senha });
    sessionStorage.setItem(TOKEN_KEY, response.data.access_token);
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
