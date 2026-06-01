import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('authGuard', () => {
  let authSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authSpy = jasmine.createSpyObj('AuthService', ['isAuthenticated', 'getCurrentUser']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });
  });

  function run(route: Partial<ActivatedRouteSnapshot>): boolean {
    return TestBed.runInInjectionContext(
      () => authGuard(route as ActivatedRouteSnapshot, {} as any) as boolean,
    );
  }

  it('redirects to /login when not authenticated', () => {
    authSpy.isAuthenticated.and.returnValue(false);
    expect(run({ routeConfig: { path: 'processos' } as any })).toBeFalse();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('forces change-password when must_change_password is set', () => {
    authSpy.isAuthenticated.and.returnValue(true);
    authSpy.getCurrentUser.and.returnValue({ must_change_password: true } as any);
    expect(run({ routeConfig: { path: 'processos' } as any })).toBeFalse();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/change-password']);
  });

  it('allows the change-password route itself even when flag is set', () => {
    authSpy.isAuthenticated.and.returnValue(true);
    authSpy.getCurrentUser.and.returnValue({ must_change_password: true } as any);
    expect(run({ routeConfig: { path: 'change-password' } as any })).toBeTrue();
  });

  it('allows access for an authenticated user without forced change', () => {
    authSpy.isAuthenticated.and.returnValue(true);
    authSpy.getCurrentUser.and.returnValue({ must_change_password: false } as any);
    expect(run({ routeConfig: { path: 'processos' } as any })).toBeTrue();
    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });
});
