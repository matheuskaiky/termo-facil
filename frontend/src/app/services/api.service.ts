import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import axios from 'axios';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private api = axios.create({
    baseURL: environment.apiUrl,
    timeout: 30000,
  });

  sessionExpired = false;

  constructor(private auth: AuthService, private router: Router) {
    this.api.interceptors.request.use((config) => {
      const token = this.auth.getToken();
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    });

    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.sessionExpired = true;
          this.auth.logout();
          this.router.navigate(['/login'], { queryParams: { expired: '1' } });
        } else if (
          error.response?.status === 403 &&
          error.response?.data?.detail === 'password_change_required'
        ) {
          this.router.navigate(['/change-password']);
        }
        return Promise.reject(error);
      }
    );
  }

  get(url: string) { return this.api.get(url); }
  post(url: string, data: any, config?: any) { return this.api.post(url, data, config); }
  put(url: string, data: any, config?: any) { return this.api.put(url, data, config); }
}
