import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const permissionGuard: CanActivateFn = (_route, _state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  const user = auth.getCurrentUser();
  if (user?.permissoes?.includes('GERENCIAR_USUARIOS')) {
    return true;
  }
  alert('Acesso negado: você não possui a permissão necessária.');
  router.navigate(['/processos']);
  return false;
};
