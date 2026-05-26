import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet } from '@angular/router';
import { HeaderComponent } from './components/header/header.component';
import { AuthService } from './services/auth.service';

const HEADERLESS_ROUTES = ['/login', '/change-password'];

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, HeaderComponent],
  templateUrl: './app.component.html'
})
export class AppComponent {
  title = 'frontend';

  constructor(private auth: AuthService, private router: Router) {}

  get showHeader(): boolean {
    const url = this.router.url.split('?')[0];
    return this.auth.isAuthenticated() && !HEADERLESS_ROUTES.includes(url);
  }
}
