import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import axios from 'axios';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    timeout: 30000,
  });

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
          this.auth.logout();
          this.router.navigate(['/login']);
        }
        return Promise.reject(error);
      }
    );
  }

  get(url: string) { return this.api.get(url); }
  post(url: string, data: any, config?: any) { return this.api.post(url, data, config); }
  put(url: string, data: any, config?: any) { return this.api.put(url, data, config); }
}
