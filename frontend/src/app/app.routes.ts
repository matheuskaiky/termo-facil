import { Routes } from '@angular/router';
import { AuditoriaComponent } from './components/auditoria/auditoria.component';
import { ProcessListComponent } from './components/process-list/process-list.component';
import { ProcessFormComponent } from './components/process-form/process-form.component';
import { AdminComponent } from './components/admin/admin.component';
import { UserFormComponent } from './components/admin/user-form/user-form.component';
import { DelegaciaFormComponent } from './components/admin/delegacia-form/delegacia-form.component';
import { LoginComponent } from './components/login/login.component';
import { ChangePasswordComponent } from './components/change-password/change-password.component';
import { MetricasComponent } from './components/metricas/metricas.component';
import { DashboardDelegaciaDetailComponent } from './components/metricas/dashboard-delegacia-detail/dashboard-delegacia-detail.component';
import { DashboardEscrivaoDetailComponent } from './components/metricas/dashboard-escrivao-detail/dashboard-escrivao-detail.component';
import { DashboardErrosComponent } from './components/metricas/dashboard-erros/dashboard-erros.component';
import { permissionGuard } from './services/permission.guard';
import { authGuard } from './services/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'change-password', component: ChangePasswordComponent, canActivate: [authGuard] },
  { path: 'processos', component: ProcessListComponent, canActivate: [authGuard] },
  { path: 'processos/novo', component: ProcessFormComponent, canActivate: [authGuard] },
  { path: 'processos/:id/editar', component: ProcessFormComponent, canActivate: [authGuard] },
  { path: 'auditoria/:id', component: AuditoriaComponent, canActivate: [authGuard] },
  // Admin sub-routes (specific before generic /admin)
  { path: 'admin/usuarios/novo', component: UserFormComponent, canActivate: [authGuard, permissionGuard], data: { permission: 'GERENCIAR_USUARIOS' } },
  { path: 'admin/usuarios/:id/editar', component: UserFormComponent, canActivate: [authGuard, permissionGuard], data: { permission: 'GERENCIAR_USUARIOS' } },
  { path: 'admin/delegacias/nova', component: DelegaciaFormComponent, canActivate: [authGuard, permissionGuard], data: { permission: 'GERENCIAR_USUARIOS' } },
  { path: 'admin/delegacias/:id/editar', component: DelegaciaFormComponent, canActivate: [authGuard, permissionGuard], data: { permission: 'GERENCIAR_USUARIOS' } },
  { path: 'admin', component: AdminComponent, canActivate: [authGuard, permissionGuard], data: { permission: 'GERENCIAR_USUARIOS' } },
  // Dashboard drill-downs (specific before /metricas)
  { path: 'dashboard/erros', component: DashboardErrosComponent, canActivate: [authGuard, permissionGuard], data: { permission: 'VER_METRICAS' } },
  { path: 'dashboard/delegacias/:id', component: DashboardDelegaciaDetailComponent, canActivate: [authGuard, permissionGuard], data: { permission: 'VER_METRICAS' } },
  { path: 'dashboard/escrivaes/:id', component: DashboardEscrivaoDetailComponent, canActivate: [authGuard, permissionGuard], data: { permission: 'VER_METRICAS' } },
  { path: 'metricas', component: MetricasComponent, canActivate: [authGuard, permissionGuard], data: { permission: 'VER_METRICAS' } },
  { path: '', redirectTo: '/processos', pathMatch: 'full' },
  { path: '**', redirectTo: '/processos' },
];
