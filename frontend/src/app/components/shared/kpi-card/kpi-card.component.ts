import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

type Tone = 'info' | 'success' | 'danger' | 'neutral';

@Component({
  selector: 'app-kpi-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="kpi-card" [ngClass]="toneClass">
      <div class="kpi-label">{{ label }}</div>
      <div class="kpi-value">{{ value }}</div>
      <div class="kpi-delta" *ngIf="delta">
        <span [class.up]="deltaUp" [class.down]="!deltaUp">
          {{ deltaUp ? '▲' : '▼' }} {{ delta }}
        </span>
        <span class="kpi-delta-sub">vs. período anterior</span>
      </div>
      <div class="kpi-note" *ngIf="note">{{ note }}</div>
    </div>
  `,
  styles: [`
    .kpi-card {
      background: var(--color-white);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-sm);
      padding: .85rem 1rem;
    }
    .kpi-card.info    { background: var(--color-info-bg);    border-color: transparent; }
    .kpi-card.success { background: var(--color-success-bg); border-color: transparent; }
    .kpi-card.danger  { background: var(--color-danger-bg);  border-color: transparent; }
    .kpi-label {
      font-size: .72rem; font-weight: 700;
      text-transform: uppercase; letter-spacing: .4px;
      color: var(--color-text-light);
      margin-bottom: 4px;
    }
    .kpi-card.info    .kpi-label { color: var(--color-info-dark); }
    .kpi-card.success .kpi-label { color: var(--color-success-dark); }
    .kpi-card.danger  .kpi-label { color: var(--color-danger-dark); }
    .kpi-value {
      font-size: 1.75rem; font-weight: 800;
      color: var(--color-primary); line-height: 1.1;
    }
    .kpi-card.info    .kpi-value { color: var(--color-info-dark); }
    .kpi-card.success .kpi-value { color: var(--color-success-dark); }
    .kpi-card.danger  .kpi-value { color: var(--color-danger-dark); }
    .kpi-delta {
      margin-top: 4px; display: flex; align-items: center; gap: .35rem; flex-wrap: wrap;
    }
    .kpi-delta .up   { font-size: .72rem; font-weight: 700; color: var(--color-success-dark); }
    .kpi-delta .down { font-size: .72rem; font-weight: 700; color: var(--color-danger-dark); }
    .kpi-delta-sub { font-size: .72rem; color: var(--color-text-subtle); }
    .kpi-note { font-size: .72rem; color: var(--color-text-subtle); font-style: italic; margin-top: 4px; }
  `]
})
export class KpiCardComponent {
  @Input() label: string = '';
  @Input() value: string | number = '';
  @Input() tone: Tone = 'neutral';
  @Input() delta: string = '';
  @Input() deltaUp: boolean = true;
  @Input() note: string = '';

  get toneClass(): string {
    return this.tone !== 'neutral' ? this.tone : '';
  }
}
