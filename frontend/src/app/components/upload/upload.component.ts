import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { FileUploadModule } from 'primeng/fileupload';
import { InputTextModule } from 'primeng/inputtext';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { MessageModule } from 'primeng/message';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    FileUploadModule,
    InputTextModule,
    ButtonModule,
    CardModule,
    MessageModule,
  ],
  template: `
    <p-card header="Subir documento">
      <div style="display:flex;flex-direction:column;gap:1rem">
        <div>
          <label for="title">Título del documento</label>
          <input
            id="title"
            pInputText
            type="text"
            [(ngModel)]="title"
            placeholder="Ej: Contrato #123"
            style="width:100%"
          />
        </div>

        <p-fileUpload
          [multiple]="false"
          accept="image/png,image/jpeg,image/tiff,application/pdf"
          [auto]="false"
          (onSelect)="onFileSelect($event)"
          chooseLabel="Seleccionar archivo"
          [disabled]="uploading"
        >
          <ng-template pTemplate="content">
            <div *ngIf="selectedFile" style="margin-top:0.5rem">
              <strong>{{ selectedFile.name }}</strong>
              ({{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB)
            </div>
          </ng-template>
        </p-fileUpload>

        <p-message
          *ngIf="error"
          severity="error"
          [text]="error"
        ></p-message>

        <p-button
          label="Subir"
          icon="pi pi-upload"
          [loading]="uploading"
          [disabled]="!selectedFile || !title"
          (onClick)="upload()"
        ></p-button>
      </div>
    </p-card>
  `,
})
export class UploadComponent {
  title = '';
  selectedFile: File | null = null;
  uploading = false;
  error = '';

  constructor(
    private api: ApiService,
    private router: Router
  ) {}

  onFileSelect(event: any) {
    this.selectedFile = event.files?.[0] ?? null;
    this.error = '';
  }

  async upload() {
    if (!this.selectedFile || !this.title) return;
    this.uploading = true;
    this.error = '';

    try {
      const isPdf = this.selectedFile.type === 'application/pdf';
      const doc = isPdf
        ? await this.api.uploadPdf(this.title, this.selectedFile).toPromise()
        : await this.api.uploadImage(this.title, this.selectedFile).toPromise();

      if (doc) {
        this.router.navigate(['/documents', doc.id]);
      }
    } catch (e: any) {
      this.error = e?.error?.detail || 'Error al subir el archivo';
    } finally {
      this.uploading = false;
    }
  }
}
