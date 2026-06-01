import { TestBed } from '@angular/core/testing';
import axios from 'axios';
import { AuthService } from './auth.service';

/** Builds an unsigned JWT with the given payload (signature is irrelevant client-side). */
function makeToken(payload: object): string {
  const b64 = (o: object) =>
    btoa(JSON.stringify(o)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  return `${b64({ alg: 'HS256', typ: 'JWT' })}.${b64(payload)}.sig`;
}

describe('AuthService', () => {
  let service: AuthService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(AuthService);
    sessionStorage.clear();
  });

  afterEach(() => sessionStorage.clear());

  it('isAuthenticated is false without a token', () => {
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('isAuthenticated is true for a non-expired token', () => {
    const exp = Math.floor(Date.now() / 1000) + 3600;
    sessionStorage.setItem('access_token', makeToken({ sub: 'u1', exp }));
    expect(service.isAuthenticated()).toBeTrue();
  });

  it('isAuthenticated is false for an expired token', () => {
    const exp = Math.floor(Date.now() / 1000) - 10;
    sessionStorage.setItem('access_token', makeToken({ sub: 'u1', exp }));
    expect(service.isAuthenticated()).toBeFalse();
  });

  it('getCurrentUser merges stored profile (nome/matricula) with JWT claims', () => {
    const exp = Math.floor(Date.now() / 1000) + 3600;
    sessionStorage.setItem('access_token', makeToken({ sub: 'u1', exp, permissoes: ['X'], cargo: 'Escrivão' }));
    sessionStorage.setItem('user_profile', JSON.stringify({ nome: 'Maria', matricula: '999' }));
    const user = service.getCurrentUser();
    expect(user?.nome).toBe('Maria');
    expect(user?.matricula).toBe('999');
    expect(user?.permissoes).toEqual(['X']);
  });

  it('login stores token and profile from the API responses', async () => {
    const exp = Math.floor(Date.now() / 1000) + 3600;
    const token = makeToken({ sub: 'u1', exp });
    spyOn(axios, 'post').and.resolveTo({ data: { access_token: token } } as any);
    spyOn(axios, 'get').and.resolveTo({ data: { nome: 'João', matricula: '123' } } as any);

    await service.login('123', 'senha');

    expect(sessionStorage.getItem('access_token')).toBe(token);
    expect(JSON.parse(sessionStorage.getItem('user_profile')!).nome).toBe('João');
  });

  it('logout clears token and profile', () => {
    sessionStorage.setItem('access_token', 'x');
    sessionStorage.setItem('user_profile', '{}');
    service.logout();
    expect(sessionStorage.getItem('access_token')).toBeNull();
    expect(sessionStorage.getItem('user_profile')).toBeNull();
  });
});
