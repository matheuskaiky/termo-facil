import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-process-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './process-list.component.html',
  styleUrls: ['./process-list.component.css']
})
export class ProcessListComponent implements OnInit {
  processos: any[] = [];
  filteredProcessos: any[] = [];
  
  activeUser: any = null;
  
  // Filtros
  searchTerm: string = '';
  statusFilter: string = '';
  escrivaoFilter: string = '';
  
  isLoading: boolean = true;
  isCreating: boolean = false;

  constructor(private api: ApiService, private router: Router) {}

  async ngOnInit() {
    await this.fetchActiveUser();
    await this.fetchProcessos();
  }

  async fetchActiveUser() {
    try {
      const response = await this.api.get('/auth/me');
      this.activeUser = response.data;
    } catch (error) {
      console.error('Erro ao buscar usuário logado', error);
    }
  }

  async fetchProcessos() {
    this.isLoading = true;
    try {
      const response = await this.api.get('/processos/');
      this.processos = response.data;
      this.applyFilters();
    } catch (error) {
      console.error('Erro ao buscar processos', error);
    } finally {
      this.isLoading = false;
    }
  }

  applyFilters() {
    this.filteredProcessos = this.processos.filter(p => {
      // Filtro de Busca (Nome ou Inquérito)
      const matchSearch = this.searchTerm === '' || 
        (p.nome_depoente && p.nome_depoente.toLowerCase().includes(this.searchTerm.toLowerCase())) ||
        (p.num_procedimento && p.num_procedimento.toLowerCase().includes(this.searchTerm.toLowerCase()));
      
      // Filtro de Status
      const matchStatus = this.statusFilter === '' || p.status_job === this.statusFilter;
      
      // Filtro de Escrivão (apenas se tiver acesso a ver vários)
      const matchEscrivao = this.escrivaoFilter === '' || 
        (p.escrivao && p.escrivao.toLowerCase().includes(this.escrivaoFilter.toLowerCase()));
      
      return matchSearch && matchStatus && matchEscrivao;
    });
  }

  async criarNovoProcesso() {
    if (this.isCreating) return;
    this.isCreating = true;
    try {
      const response = await this.api.post('/processos/novo', {});
      const novoId = response.data.id_depoimento;
      this.router.navigate(['/auditoria', novoId]);
    } catch (error) {
      console.error('Erro ao criar processo mock', error);
      alert('Erro ao criar processo. Verifique se o seed_db.py foi executado.');
    } finally {
      this.isCreating = false;
    }
  }

  goToAuditoria(id: string) {
    this.router.navigate(['/auditoria', id]);
  }

  get canSeeEscrivaoFilter(): boolean {
    return this.activeUser?.cargo?.nome_cargo === 'Delegado' || this.activeUser?.cargo?.nome_cargo === 'Admin';
  }
  
  get canCreateProcess(): boolean {
    // Escrivão ou Delegado/Admin que possua a permissão UPLOAD_AUDIO
    if (!this.activeUser || !this.activeUser.cargo) return false;
    const permissions = this.activeUser.cargo.permissoes || [];
    return permissions.some((p: any) => p.nome_permissao === 'UPLOAD_AUDIO');
  }
}
