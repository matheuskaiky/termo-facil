import { Injectable } from '@angular/core';
import axios from 'axios';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    timeout: 30000,
  });

  constructor() { }

  get(url: string) {
    return this.api.get(url);
  }

  post(url: string, data: any, config?: any) {
    return this.api.post(url, data, config);
  }
}
