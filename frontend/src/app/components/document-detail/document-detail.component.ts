import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ProgressBarModule } from 'primeng/progressbar';
import { DialogModule } from 'primeng/dialog';
import { ApiService } from '../../services/api.service';
import { DocumentResponse, PageItem } from '../../models/document';

@Component({
  selector: 'app-document-detail',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    TagModule,
    ProgressBarModule,
    DialogModule,
  ],
  template: `
    <ng-container *ngIf="doc">
      <p-card [header]="doc.title">
        <div style="display:flex;gap:1rem;align-items:center;margin-bottom:1rem">
          <p-tag
            [value]="doc.doc_type === 'pdf' ? 'PDF' : 'Imagen'"
            severity="info"
          />
          <span>{{ doc.total_pages }} página(s)</span>
          <span style="color:var(--text-color-secondary)">
            {{ doc.created_at | date:'short' }}
          </span>
          <p-button
            label="Mejorar todas"
            icon="pi pi-refresh"
            severity="success"
            [loading]="enhancingAll"
            (onClick)="enhanceAll()"
          ></p-button>
        </div>
      </p-card>

      <div
        style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:1rem;margin-top:1.5rem"
      >
        <div
          *ngFor="let page of doc.pages"
          style="border:1px solid var(--surface-border);border-radius:8px;overflow:hidden;cursor:pointer"
          (click)="openPreview(page)"
        >
          <img
            [src]="pageImg(page)"
            [alt]="'Página ' + page.page_number"
            style="width:100%;height:280px;object-fit:contain;background:#f5f5f5"
          />
          <div
            style="padding:0.5rem;display:flex;justify-content:space-between;align-items:center"
          >
            <strong>Pág {{ page.page_number }}</strong>
            <div style="display:flex;gap:0.25rem;align-items:center">
              <p-tag
                [severity]="page.status === 'completed' ? 'success' : page.status === 'processing' ? 'warn' : page.status === 'failed' ? 'danger' : 'info'"
                [value]="page.status"
              />
              <p-button
                *ngIf="page.status === 'pending' || page.status === 'failed'"
                icon="pi pi-refresh"
                severity="help"
                [rounded]="true"
                [text]="true"
                (click)="$event.stopPropagation(); enhancePage(page)"
              ></p-button>
            </div>
          </div>
        </div>
      </div>

      <p-dialog
        [(visible)]="previewVisible"
        [style]="{ width: '90vw', height: '90vh' }"
        [maximizable]="true"
        [modal]="true"
      >
        <ng-template pTemplate="header">
          Página {{ previewPage?.page_number }}
          <p-tag
            [severity]="previewPage?.status === 'completed' ? 'success' : 'info'"
            [value]="previewPage?.status"
            style="margin-left:0.5rem"
          />
        </ng-template>
        <img
          *ngIf="previewPage"
          [src]="previewImg(previewPage)"
          style="width:100%;height:auto;max-height:80vh;object-fit:contain"
          alt="Vista previa página"
        />
      </p-dialog>
    </ng-container>
  `,
})
export class DocumentDetailComponent implements OnInit {
  doc?: DocumentResponse;
  enhancingAll = false;
  previewVisible = false;
  previewPage?: PageItem;

  constructor(
    private route: ActivatedRoute,
    private api: ApiService
  ) {}

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id')!;
    this.load(id);
  }

  load(id: string) {
    this.api.getDocument(id).subscribe((d) => (this.doc = d));
  }

  pageImg(page: PageItem): string {
    const type = page.status === 'completed' ? 'enhanced' : 'original';
    return this.api.getImageUrl(page.id, type as any);
  }

  previewImg(page: PageItem): string {
    const type = page.status === 'completed' ? 'enhanced' : 'original';
    return this.api.getImageUrl(page.id, type as any);
  }

  enhancePage(page: PageItem) {
    this.api.enhancePage(page.id).subscribe(() => {
      page.status = 'processing';
    });
  }

  enhanceAll() {
    if (!this.doc) return;
    this.enhancingAll = true;
    this.api.enhanceAll(this.doc.id).subscribe({
      next: () => {
        this.doc!.pages.forEach((p) => {
          if (p.status === 'pending') p.status = 'processing';
        });
      },
      complete: () => (this.enhancingAll = false),
    });
  }

  openPreview(page: PageItem) {
    this.previewPage = page;
    this.previewVisible = true;
  }
}
