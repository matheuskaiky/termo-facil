import { Component } from '@angular/core';

@Component({
  selector: 'app-header',
  standalone: true,
  templateUrl: './header.component.html'
})
export class HeaderComponent {
  title = 'Termo Fácil';
  user = 'Escrivão Silva';
  station = '1ª DP - Teresina/PI';
}
