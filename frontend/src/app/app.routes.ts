import { Routes } from '@angular/router';
import { AuditoriaComponent } from './components/auditoria/auditoria.component';
import { AdminComponent } from './components/admin/admin.component';
import { permissionGuard } from './services/permission.guard';

export const routes: Routes = [
  { path: 'auditoria', component: AuditoriaComponent },
  { path: 'admin', component: AdminComponent, canActivate: [permissionGuard] },
  { path: '', redirectTo: '/auditoria', pathMatch: 'full' },
  { path: '**', redirectTo: '/auditoria' }
];
