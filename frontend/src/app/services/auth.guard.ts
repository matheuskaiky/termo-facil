import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = (route, _state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (!auth.isAuthenticated()) {
    router.navigate(['/login']);
    return false;
  }

  const user = auth.getCurrentUser();
  if (user?.must_change_password && route.routeConfig?.path !== 'change-password') {
    router.navigate(['/change-password']);
    return false;
  }

  return true;
};
