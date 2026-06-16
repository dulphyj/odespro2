import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: '/upload', pathMatch: 'full' },
  {
    path: 'upload',
    loadComponent: () =>
      import('./components/upload/upload.component').then((m) => m.UploadComponent),
  },
  {
    path: 'documents',
    loadComponent: () =>
      import('./components/document-list/document-list.component').then(
        (m) => m.DocumentListComponent
      ),
  },
  {
    path: 'documents/:id',
    loadComponent: () =>
      import('./components/document-detail/document-detail.component').then(
        (m) => m.DocumentDetailComponent
      ),
  },
];
