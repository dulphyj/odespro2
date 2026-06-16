import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { DocumentList, DocumentResponse, PageStatus } from '../models/document';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = '/api/v1';

  constructor(private http: HttpClient) {}

  getDocuments(): Observable<DocumentList[]> {
    return this.http.get<DocumentList[]>(`${this.base}/documents`);
  }

  getDocument(id: string): Observable<DocumentResponse> {
    return this.http.get<DocumentResponse>(`${this.base}/documents/${id}`);
  }

  uploadImage(title: string, file: File): Observable<DocumentResponse> {
    const form = new FormData();
    form.append('title', title);
    form.append('file', file);
    return this.http.post<DocumentResponse>(`${this.base}/documents/upload-image`, form);
  }

  uploadPdf(title: string, file: File): Observable<DocumentResponse> {
    const form = new FormData();
    form.append('title', title);
    form.append('file', file);
    return this.http.post<DocumentResponse>(`${this.base}/documents/upload-pdf`, form);
  }

  getImageUrl(pageId: string, type: 'original' | 'enhanced' = 'original'): string {
    return `${this.base}/pages/${pageId}/image?type=${type}`;
  }

  getPageStatus(pageId: string): Observable<PageStatus> {
    return this.http.get<PageStatus>(`${this.base}/pages/${pageId}/status`);
  }

  enhancePage(pageId: string): Observable<PageStatus> {
    return this.http.post<PageStatus>(`${this.base}/pages/${pageId}/enhance`, {});
  }

  enhanceAll(docId: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.base}/documents/${docId}/enhance-all`, {});
  }
}
