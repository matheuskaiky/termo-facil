import { CanDeactivateFn } from '@angular/router';

/**
 * Components with a form that can have unsaved changes implement this so the
 * guard (and a window:beforeunload handler in the component) can warn the user
 * before they navigate away and lose their answers.
 */
export interface ComponentCanDeactivate {
  canDeactivate: () => boolean;
}

export const pendingChangesGuard: CanDeactivateFn<ComponentCanDeactivate> = (component) => {
  if (component && typeof component.canDeactivate === 'function' && !component.canDeactivate()) {
    return confirm(
      'Você tem alterações não salvas neste formulário.\n\n' +
      'Se sair agora, as informações preenchidas serão perdidas. Deseja sair mesmo assim?'
    );
  }
  return true;
};
