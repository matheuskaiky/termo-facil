import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from './components/header/header.component';
import { AuditoriaComponent } from './components/auditoria/auditoria.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, HeaderComponent, AuditoriaComponent],
  templateUrl: './app.component.html'
})
export class AppComponent {
  title = 'frontend';
}
