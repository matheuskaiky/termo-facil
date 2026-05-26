import { Component, Input, Output, EventEmitter, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-signature-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './signature-modal.component.html',
  styleUrls: ['./signature-modal.component.css']
})
export class SignatureModalComponent {
  @Input() visible: boolean = false;
  @Input() pdfHash: string | null = null;
  @Input() pdfUrl: string | null = null;
  @Input() pdfGenerationDate: Date | null = null;
  @Input() jobId: string | null = null;
  @Input() inquerito: string = '';
  @Input() asrModel: string = 'whisper-base';
  @Input() llmModel: string = 'llama3';

  @Output() close = new EventEmitter<void>();
  @Output() copyHash = new EventEmitter<void>();
  @Output() downloadPdf = new EventEmitter<void>();

  constructor(private auth: AuthService) {}

  get currentUser() {
    return this.auth.getCurrentUser();
  }

  get formattedDate(): string {
    if (!this.pdfGenerationDate) return '';
    return this.pdfGenerationDate.toLocaleString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      timeZoneName: 'short'
    });
  }

  get modelString(): string {
    return `${this.asrModel} + ${this.llmModel}`;
  }

  onCopyHash() {
    if (this.pdfHash) {
      navigator.clipboard.writeText(this.pdfHash).catch(() => {});
    }
    this.copyHash.emit();
  }

  onDownloadPdf() {
    if (this.pdfUrl) {
      const a = document.createElement('a');
      a.href = this.pdfUrl;
      a.download = `termo-${this.inquerito || 'depoimento'}.pdf`;
      a.click();
    }
    this.downloadPdf.emit();
  }

  onOpenPdf() {
    if (this.pdfUrl) window.open(this.pdfUrl, '_blank');
  }

  @HostListener('document:keydown.escape')
  onEscape() {
    if (this.visible) this.close.emit();
  }
}
