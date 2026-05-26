import { inject } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const permissionGuard: CanActivateFn = (route: ActivatedRouteSnapshot, _state) => {
  const required: string = route.data?.['permission'] ?? 'GERENCIAR_USUARIOS';
  const user = inject(AuthService).getCurrentUser();

  if (user?.permissoes?.includes(required)) {
    return true;
  }

  inject(Router).navigate(['/processos']);
  return false;
};
