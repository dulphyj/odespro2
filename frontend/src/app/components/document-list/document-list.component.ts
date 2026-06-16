import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ApiService } from '../../services/api.service';
import { DocumentList } from '../../models/document';

@Component({
  selector: 'app-document-list',
  standalone: true,
  imports: [CommonModule, TableModule, ButtonModule, TagModule],
  template: `
    <h2>Documentos</h2>
    <p-table [value]="docs" [loading]="loading" [paginator]="true" [rows]="10">
      <ng-template pTemplate="header">
        <tr>
          <th>Título</th>
          <th>Tipo</th>
          <th>Archivo</th>
          <th>Páginas</th>
          <th>Fecha</th>
          <th></th>
        </tr>
      </ng-template>
      <ng-template pTemplate="body" let-doc>
        <tr>
          <td>{{ doc.title }}</td>
          <td>
            <p-tag [value]="doc.doc_type === 'pdf' ? 'PDF' : 'Imagen'" />
          </td>
          <td>{{ doc.original_filename }}</td>
          <td>{{ doc.total_pages }}</td>
          <td>{{ doc.created_at | date:'short' }}</td>
          <td>
            <p-button
              icon="pi pi-eye"
              severity="info"
              [rounded]="true"
              [text]="true"
              (onClick)="view(doc.id)"
            ></p-button>
          </td>
        </tr>
      </ng-template>
    </p-table>
  `,
})
export class DocumentListComponent implements OnInit {
  docs: DocumentList[] = [];
  loading = false;

  constructor(
    private api: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.load();
  }

  load() {
    this.loading = true;
    this.api.getDocuments().subscribe({
      next: (d) => (this.docs = d),
      error: () => (this.loading = false),
      complete: () => (this.loading = false),
    });
  }

  view(id: string) {
    this.router.navigate(['/documents', id]);
  }
}
