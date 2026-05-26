import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-filter-chip',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button
      class="filter-chip"
      [class.active]="active"
      (click)="clicked.emit()"
      [attr.aria-pressed]="active">
      {{ label }}<span *ngIf="count != null && count > 0" class="chip-count"> · {{ count }}</span>
    </button>
  `,
  styles: [`
    .filter-chip {
      display: inline-flex; align-items: center;
      padding: .3rem .75rem;
      border-radius: var(--radius-pill);
      border: 1px solid var(--color-border);
      background: transparent;
      color: var(--color-secondary);
      font-size: .78rem; font-weight: 600;
      font-family: inherit; cursor: pointer;
      transition: background .15s, color .15s;
      white-space: nowrap;
    }
    .filter-chip:hover { background: var(--color-surface-hover); }
    .filter-chip.active {
      background: var(--color-primary); color: #fff; border-color: var(--color-primary);
    }
    .chip-count { font-weight: 700; }
  `]
})
export class FilterChipComponent {
  @Input() label: string = '';
  @Input() active: boolean = false;
  @Input() count: number | null = null;
  @Output() clicked = new EventEmitter<void>();
}
