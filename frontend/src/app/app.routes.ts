import { Routes } from '@angular/router';
import { AuditoriaComponent } from './components/auditoria/auditoria.component';
import { ProcessListComponent } from './components/process-list/process-list.component';
import { AdminComponent } from './components/admin/admin.component';
import { permissionGuard } from './services/permission.guard';

export const routes: Routes = [
  { path: 'processos', component: ProcessListComponent },
  { path: 'auditoria/:id', component: AuditoriaComponent },
  { path: 'admin', component: AdminComponent, canActivate: [permissionGuard] },
  { path: '', redirectTo: '/processos', pathMatch: 'full' },
  { path: '**', redirectTo: '/processos' }
];
