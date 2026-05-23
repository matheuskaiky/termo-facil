import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { AuthService, JwtUser } from '../../services/auth.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './header.component.html',
})
export class HeaderComponent {
  title = 'Termo Fácil';

  constructor(private auth: AuthService, private router: Router) {}

  get activeUser(): JwtUser | null {
    return this.auth.getCurrentUser();
  }

  get canManageUsers(): boolean {
    return this.activeUser?.permissoes?.includes('GERENCIAR_USUARIOS') ?? false;
  }

  get userInitials(): string {
    const nome = this.activeUser?.nome ?? '';
    const parts = nome.replace(/\s*\([^)]*\)/g, '').trim().split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return parts[0]?.[0]?.toUpperCase() ?? 'TF';
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
