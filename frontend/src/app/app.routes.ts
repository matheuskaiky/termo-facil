import { Routes } from '@angular/router';
import { AuditoriaComponent } from './components/auditoria/auditoria.component';
import { ProcessListComponent } from './components/process-list/process-list.component';
import { AdminComponent } from './components/admin/admin.component';
import { LoginComponent } from './components/login/login.component';
import { ChangePasswordComponent } from './components/change-password/change-password.component';
import { permissionGuard } from './services/permission.guard';
import { authGuard } from './services/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'change-password', component: ChangePasswordComponent, canActivate: [authGuard] },
  { path: 'processos', component: ProcessListComponent, canActivate: [authGuard] },
  { path: 'auditoria/:id', component: AuditoriaComponent, canActivate: [authGuard] },
  { path: 'admin', component: AdminComponent, canActivate: [authGuard, permissionGuard] },
  { path: '', redirectTo: '/processos', pathMatch: 'full' },
  { path: '**', redirectTo: '/processos' },
];
