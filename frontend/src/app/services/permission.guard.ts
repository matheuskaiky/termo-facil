import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { ApiService } from './api.service';

export const permissionGuard: CanActivateFn = async (route, state) => {
  const api = inject(ApiService);
  const router = inject(Router);

  try {
    const response = await api.get('/auth/me');
    const user = response.data;
    const permissions = user.cargo?.permissoes?.map((p: any) => p.nome_permissao) || [];
    
    if (permissions.includes('GERENCIAR_USUARIOS')) {
      return true;
    } else {
      alert('Acesso negado: Você não possui a permissão necessária para acessar o Painel de Administrador.');
      router.navigate(['/auditoria']);
      return false;
    }
  } catch (error) {
    console.error('Erro na guarda de permissão:', error);
    router.navigate(['/auditoria']);
    return false;
  }
};
