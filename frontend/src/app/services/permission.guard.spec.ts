import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router } from '@angular/router';
import { permissionGuard } from './permission.guard';
import { AuthService } from './auth.service';

describe('permissionGuard', () => {
  let authSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authSpy = jasmine.createSpyObj('AuthService', ['getCurrentUser']);
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
      () => permissionGuard(route as ActivatedRouteSnapshot, {} as any) as boolean,
    );
  }

  it('allows access when the user has the required permission from route.data', () => {
    authSpy.getCurrentUser.and.returnValue({ permissoes: ['VER_METRICAS'] } as any);
    const ok = run({ data: { permission: 'VER_METRICAS' } });
    expect(ok).toBeTrue();
    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });

  it('reads the required permission generically from route.data', () => {
    authSpy.getCurrentUser.and.returnValue({ permissoes: ['GERENCIAR_USUARIOS'] } as any);
    expect(run({ data: { permission: 'VER_METRICAS' } })).toBeFalse();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/processos']);
  });

  it('redirects silently to /processos when permission missing (no alert)', () => {
    authSpy.getCurrentUser.and.returnValue({ permissoes: [] } as any);
    expect(run({ data: { permission: 'GERENCIAR_USUARIOS' } })).toBeFalse();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/processos']);
  });

  it('falls back to GERENCIAR_USUARIOS when no permission specified', () => {
    authSpy.getCurrentUser.and.returnValue({ permissoes: ['GERENCIAR_USUARIOS'] } as any);
    expect(run({ data: {} })).toBeTrue();
  });
});
