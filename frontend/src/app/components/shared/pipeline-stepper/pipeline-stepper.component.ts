import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

const STAGES = [
  { id: 'pendente',      label: 'Pendente' },
  { id: 'transcrevendo', label: 'Transcrevendo' },
  { id: 'extraindo',     label: 'Extraindo Dados' },
  { id: 'resumo',        label: 'Gerando Resumo' },
  { id: 'concluido',     label: 'Concluído' },
];

@Component({
  selector: 'app-pipeline-stepper',
  standalone: true,
  imports: [CommonModule],
  template: `
    <ol class="tf-pipeline" [class.compact]="compact" role="list">
      <li *ngFor="let s of stages; let i = index"
          class="step"
          [class.done]="i < activeIndex"
          [class.active]="i === activeIndex && !error"
          [class.errored]="i === activeIndex && error"
          [attr.aria-current]="i === activeIndex ? 'step' : null">
        <div class="step-marker">
          <ng-container *ngIf="i < activeIndex">
            <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
              <polyline points="1.5,5 4,7.5 8.5,2.5" fill="none" stroke="currentColor" stroke-width="1.6"/>
            </svg>
          </ng-container>
          <ng-container *ngIf="i === activeIndex && error">!</ng-container>
          <ng-container *ngIf="i > activeIndex || (i === activeIndex && !error)">{{ i + 1 }}</ng-container>
        </div>
        <div class="step-label">{{ s.label }}</div>
        <div class="step-line" *ngIf="i < stages.length - 1"></div>
      </li>
    </ol>
  `,
  styles: [`
    .tf-pipeline {
      list-style: none; padding: 0; margin: 0;
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 0; align-items: start;
    }
    .step {
      position: relative; text-align: center;
    }
    .step-marker {
      width: 24px; height: 24px; border-radius: 50%;
      background: #fff; border: 2px solid var(--color-border-strong);
      color: var(--color-text-light);
      margin: 0 auto 6px; display: flex; align-items: center; justify-content: center;
      font-size: .72rem; font-weight: 800; position: relative; z-index: 2;
      transition: all .2s;
    }
    .step-label {
      font-size: .72rem; font-weight: 600;
      color: var(--color-text-light);
    }
    .step-line {
      position: absolute; top: 11px; left: 50%; width: 100%; height: 2px;
      background: var(--color-border-strong); z-index: 1;
    }
    .step.done .step-marker {
      background: var(--color-success); border-color: var(--color-success); color: #fff;
    }
    .step.done .step-line {
      background: var(--color-success);
    }
    .step.done .step-label { color: var(--color-success-dark); }
    .step.active .step-marker {
      background: var(--color-primary); border-color: var(--color-primary); color: #fff;
      box-shadow: 0 0 0 4px rgba(43,108,176,.18);
      animation: tfPulse 1.6s ease-in-out infinite;
    }
    .step.active .step-label { color: var(--color-primary); font-weight: 700; }
    .step.errored .step-marker {
      background: var(--color-accent); border-color: var(--color-accent); color: #fff;
    }
    .step.errored .step-label { color: var(--color-danger-dark); font-weight: 700; }
    @keyframes tfPulse {
      0%, 100% { box-shadow: 0 0 0 4px rgba(43,108,176,.18); }
      50%       { box-shadow: 0 0 0 8px rgba(43,108,176,.08); }
    }
    .compact .step-marker { width: 16px; height: 16px; font-size: .6rem; border-width: 1.5px; }
    .compact .step-label  { font-size: .65rem; }
    .compact .step-line   { top: 7px; }
  `]
})
export class PipelineStepperComponent {
  @Input() activeIndex: number = 0;
  @Input() error: boolean = false;
  @Input() compact: boolean = false;

  readonly stages = STAGES;
}
